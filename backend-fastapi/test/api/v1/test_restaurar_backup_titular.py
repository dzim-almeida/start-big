# ---------------------------------------------------------------------------
# ARQUIVO: test_restaurar_backup_titular.py
# DESCRICAO: Restauração do banco pelo titular depois do re-login (LIC-03 §4.1,
#            §6.1; CT-01 a CT-07 e CT-21 a CT-23).
#
# A nuvem é simulada: trocamos (monkeypatch) as funções que falam com ela por
# versões de mentira, que devolvem o que cada caso precisa. Assim o teste não
# depende de internet e mostra exatamente o que o backend faz com cada resposta.
# ---------------------------------------------------------------------------

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.db.models.configuracao_licenca import ConfiguracaoLicenca
from app.schemas.backup.operacoes import DownloadChainResponse
from app.schemas.licenca import AutoCadastroResponse
from app.services.backup import restore
from app.services.cloud.flow import CloudSyncError
from app.services.licenca import restauracao_titular
from app.services.licenca.transferencia import _erro

AGORA = datetime.now(timezone.utc)
URL = "/api/v1/licenca/restaurar-backup"
CORPO = {"email": "dono@exemplo.com.br", "senha": "senha-da-conta"}


def _licenca_local(licenca_id: str = "lic-da-loja") -> ConfiguracaoLicenca:
    """A licença que o re-login acabou de gravar neste computador."""
    return ConfiguracaoLicenca(
        cliente_id="cliente-1", hwid="HWID-TESTE", licenca_id=licenca_id,
        chave_ativacao="x", public_key="x", limite=3,
        data_vencimento=AGORA + timedelta(days=30), token="x", ultima_sinc=AGORA,
        grace_period=7, proxima_validacao=AGORA + timedelta(days=1),
    )


def _login(licenca_id: str = "lic-da-loja") -> AutoCadastroResponse:
    """Resposta de login aprovado da nuvem para a conta `licenca_id`."""
    return AutoCadastroResponse(
        msg="ok", licencaId=licenca_id, chaveAtivacao="CHAVE", limite=3,
        dataVencimento=AGORA + timedelta(days=30), token="t", ultimaSincronizacao=AGORA,
        gracePeriodDias=7, proximaValidacaoEm=AGORA + timedelta(days=1),
    )


def _status(*eventos: dict) -> dict:
    """Corpo do GET /erp/backup/status com o histórico pedido."""
    return {"planoPermiteBackup": True, "historicoEventos": list(eventos)}


def _full(ciclo: str, quando: str = "2026-11-10T22:00:00Z", status: str = "CONFIRMADO") -> dict:
    return {"ciclo": ciclo, "tipo": "FULL", "status": status, "confirmadoEm": quando}


@pytest.fixture
def nuvem(monkeypatch, db_session, tmp_path):
    """Liga a nuvem de mentira e devolve um "painel" para cada teste configurar."""
    db_session.add(_licenca_local())
    db_session.commit()

    painel = {
        "login": _login(),
        "status": _status(_full("2026-11-10")),
        "download": DownloadChainResponse(status="success", ciclo="2026-11-10"),
        "ciclo_baixado": None,
        "preparado": None,
    }

    def entrar(email, senha, hwid):
        if isinstance(painel["login"], Exception):
            raise painel["login"]
        return painel["login"]

    def consultar_status(db):
        if isinstance(painel["status"], Exception):
            raise painel["status"]
        return painel["status"]

    async def baixar(db, ciclo):
        painel["ciclo_baixado"] = ciclo
        if isinstance(painel["download"], Exception):
            raise painel["download"]
        return painel["download"]

    def preparar(ciclo):
        painel["preparado"] = ciclo

    monkeypatch.setattr(restauracao_titular, "_entrar_na_conta", entrar)
    monkeypatch.setattr(restauracao_titular, "consultar_status_backup", consultar_status)
    monkeypatch.setattr(restauracao_titular, "download_chain", baixar)
    monkeypatch.setattr(restauracao_titular.restore, "preparar_restauracao_do_titular", preparar)
    # Nenhuma restauração pendente, a não ser que o teste crie o marcador
    monkeypatch.setattr(restore, "MARKER_RESTORE_PATH", str(tmp_path / "restore.json"))
    return painel


def test_ct01_senha_certa_e_licenca_desta_maquina(client, nuvem):
    resposta = client.post(URL, json=CORPO)
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "pendente_reinicio"
    assert corpo["ciclo"] == "2026-11-10"
    assert nuvem["preparado"] == "2026-11-10"


def test_ct02_senha_errada_nada_preparado(client, nuvem):
    nuvem["login"] = _erro(401, "CREDENCIAIS_INVALIDAS", "E-mail ou senha da conta StartBig incorretos.")
    resposta = client.post(URL, json=CORPO)
    assert resposta.status_code == 401
    assert resposta.json()["detail"]["codigo"] == "CREDENCIAIS_INVALIDAS"
    assert nuvem["preparado"] is None and nuvem["ciclo_baixado"] is None


def test_ct03_conta_de_outra_licenca(client, nuvem):
    nuvem["login"] = _login("lic-de-outra-loja")
    resposta = client.post(URL, json=CORPO)
    assert resposta.status_code == 403
    assert resposta.json()["detail"]["codigo"] == "LICENCA_DE_OUTRA_CONTA"
    assert nuvem["preparado"] is None and nuvem["ciclo_baixado"] is None


def test_ct04_sem_backup_na_nuvem(client, nuvem):
    # A nuvem diz que o ciclo pedido não tem arquivos
    nuvem["download"] = DownloadChainResponse(status="no_files", ciclo="2026-11-10")
    resposta = client.post(URL, json=CORPO)
    assert resposta.status_code == 404
    assert resposta.json()["detail"]["codigo"] == "BACKUP_INEXISTENTE"
    assert nuvem["preparado"] is None


def test_ct04b_url_download_404(client, nuvem):
    nuvem["download"] = CloudSyncError("404", code="BACKUP_INEXISTENTE", http_status=404)
    resposta = client.post(URL, json=CORPO)
    assert resposta.status_code == 404
    assert resposta.json()["detail"]["codigo"] == "BACKUP_INEXISTENTE"


def test_ct05_restauracao_ja_pendente(client, nuvem):
    with open(restore.MARKER_RESTORE_PATH, "w", encoding="utf-8") as marcador:
        marcador.write("{}")
    resposta = client.post(URL, json=CORPO)
    assert resposta.status_code == 409
    assert resposta.json()["detail"]["codigo"] == "RESTAURACAO_JA_PENDENTE"
    assert nuvem["ciclo_baixado"] is None  # nem chegou a baixar


@pytest.mark.parametrize("falha, codigo", [
    (CloudSyncError("Falha de rede"), "SEM_CONEXAO"),                       # sem http_status = rede
    (CloudSyncError("5xx", http_status=502), "NUVEM_INDISPONIVEL"),
])
def test_ct06_sem_rede_ou_nuvem_fora(client, nuvem, falha, codigo):
    nuvem["download"] = falha
    resposta = client.post(URL, json=CORPO)
    assert resposta.status_code == 503
    assert resposta.json()["detail"]["codigo"] == codigo


def test_ct06b_login_sem_rede(client, nuvem):
    nuvem["login"] = _erro(503, "SEM_CONEXAO", "Sem conexão com a StartBig.")
    resposta = client.post(URL, json=CORPO)
    assert resposta.status_code == 503
    assert resposta.json()["detail"]["codigo"] == "SEM_CONEXAO"


def test_ct07_ciclo_informado_e_usado(client, nuvem):
    nuvem["download"] = DownloadChainResponse(status="success", ciclo="2026-10-27")
    resposta = client.post(URL, json={**CORPO, "ciclo": "2026-10-27"})
    assert resposta.status_code == 200
    assert nuvem["ciclo_baixado"] == "2026-10-27"
    assert nuvem["preparado"] == "2026-10-27"


def test_ct21_semana_atual_sem_full_usa_a_anterior(client, nuvem):
    # Segunda de manhã: a semana atual só tem um envio que falhou
    nuvem["status"] = _status(
        _full("2026-11-17", status="FALHOU"),
        _full("2026-11-10"),
        _full("2026-11-03"),
    )
    resposta = client.post(URL, json=CORPO)
    assert resposta.status_code == 200
    assert nuvem["ciclo_baixado"] == "2026-11-10"


def test_ct22_trial_com_um_full_antigo(client, nuvem):
    nuvem["status"] = _status({"ciclo": "2026-09-01", "tipo": "full", "status": "confirmado"})
    resposta = client.post(URL, json=CORPO)
    assert resposta.status_code == 200
    assert nuvem["ciclo_baixado"] == "2026-09-01"


def test_ct23_nenhum_full_confirmado(client, nuvem):
    nuvem["status"] = _status(
        {"ciclo": "2026-11-10", "tipo": "FRAGMENTO", "status": "CONFIRMADO"},
        _full("2026-11-03", status="PENDENTE"),
    )
    resposta = client.post(URL, json=CORPO)
    assert resposta.status_code == 404
    assert resposta.json()["detail"]["codigo"] == "BACKUP_INEXISTENTE"
    assert nuvem["ciclo_baixado"] is None


def test_chave_invalida_passa_o_codigo_da_lic01(client, nuvem):
    nuvem["download"] = HTTPException(
        status_code=422,
        detail={"codigo": "BACKUP_CHAVE_INVALIDA", "mensagem": "O backup da nuvem não abre com a chave desta licença."},
    )
    resposta = client.post(URL, json=CORPO)
    assert resposta.status_code == 422
    assert resposta.json()["detail"]["codigo"] == "BACKUP_CHAVE_INVALIDA"


# --- Funções puras -----------------------------------------------------------

def test_resumo_do_backup_traz_o_ultimo_envio_do_ciclo():
    status = _status(
        _full("2026-11-10", quando="2026-11-10T22:00:00Z"),
        {"ciclo": "2026-11-10", "tipo": "FRAGMENTO", "status": "CONFIRMADO", "confirmadoEm": "2026-11-14T22:00:00Z"},
        _full("2026-11-03"),
    )
    resumo = restauracao_titular.resumo_do_backup(status)
    assert resumo.ciclo == "2026-11-10"
    assert resumo.ultimo_envio == "2026-11-14T22:00:00Z"


def test_resumo_do_backup_sem_full_e_none():
    assert restauracao_titular.resumo_do_backup(_status()) is None
    assert restauracao_titular.resumo_do_backup({}) is None


def test_preparar_do_titular_recusa_com_marcador(monkeypatch, tmp_path):
    marcador = tmp_path / "restore.json"
    marcador.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(restore, "MARKER_RESTORE_PATH", str(marcador))
    assert restore.restauracao_pendente() is True
