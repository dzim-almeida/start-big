# ---------------------------------------------------------------------------
# ARQUIVO: test_ultimo_ciclo.py
# DESCRICAO: Lembrar o resultado do último ciclo de envio para a nuvem e
#            mostrá-lo em GET /backup/avisos (LIC-08, CT-01 a CT-05).
# ---------------------------------------------------------------------------

import pytest

from app.core import permissoes
from app.core.depends import get_current_master_user
from app.main import app
from app.schemas.backup.operacoes import SyncResponse
from app.services.cloud import ultimo_ciclo
from app.services.cloud.flow import CloudSyncError


@pytest.fixture(autouse=True)
def limpo():
    """Cada teste começa sem aviso guardado (o valor fica em memória)."""
    ultimo_ciclo.registrar(None)
    permissoes._pasta_aberta_desde = None
    yield
    ultimo_ciclo.registrar(None)
    permissoes._pasta_aberta_desde = None


def test_ct01_ciclo_parado_pelo_trial_e_registrado():
    ultimo_ciclo.registrar_resposta(SyncResponse(status="blocked", code="TRIAL_BACKUP_USADO",
                                                 feito_em="2026-11-18T10:00:00Z"))
    aviso = ultimo_ciclo.ler()
    assert aviso["codigo"] == "TRIAL_BACKUP_USADO"
    assert aviso["desde"] is not None
    assert aviso["feito_em"] == "2026-11-18T10:00:00Z"


def test_ct02_erro_da_nuvem_com_codigo_e_registrado():
    ultimo_ciclo.registrar_erro(CloudSyncError("403", code="BACKUP_MAQUINA_REVOGADA", http_status=403))
    assert ultimo_ciclo.ler()["codigo"] == "BACKUP_MAQUINA_REVOGADA"


def test_ct03_mesmo_codigo_mantem_o_desde():
    ultimo_ciclo.registrar("LICENCA_VENCIDA")
    primeiro = ultimo_ciclo.ler()["desde"]
    ultimo_ciclo.registrar("LICENCA_VENCIDA")
    assert ultimo_ciclo.ler()["desde"] == primeiro


@pytest.mark.parametrize("status", ["success", "skipped", "up_to_date"])
def test_ct04_ciclo_que_envia_ou_nao_tem_novidade_limpa(status):
    ultimo_ciclo.registrar("TRIAL_BACKUP_USADO")
    ultimo_ciclo.registrar_resposta(SyncResponse(status=status))
    assert ultimo_ciclo.ler() is None


@pytest.mark.parametrize("status", ["in_progress", "waiting", "no_local_backup"])
def test_ciclo_sem_conclusao_nao_mexe_no_aviso(status):
    # Outro terminal enviando, ou nada local ainda: não diz nada sobre o motivo
    ultimo_ciclo.registrar("LICENCA_VENCIDA")
    ultimo_ciclo.registrar_resposta(SyncResponse(status=status))
    assert ultimo_ciclo.ler()["codigo"] == "LICENCA_VENCIDA"


def test_erro_de_rede_sem_codigo_nao_vira_aviso():
    # Sem internet o envio só fica para depois: não é "backup parado"
    ultimo_ciclo.registrar_erro(CloudSyncError("Falha de rede"))
    assert ultimo_ciclo.ler() is None


def test_data_do_ultimo_full_do_historico():
    status = {"historicoEventos": [
        {"ciclo": "2026-11-03", "tipo": "FULL", "status": "CONFIRMADO", "confirmadoEm": "2026-11-03T10:00:00Z"},
        {"ciclo": "2026-11-17", "tipo": "full", "status": "confirmado", "confirmadoEm": "2026-11-18T10:00:00Z"},
        {"ciclo": "2026-11-17", "tipo": "FRAGMENTO", "status": "CONFIRMADO", "confirmadoEm": "2026-11-19T10:00:00Z"},
    ]}
    assert ultimo_ciclo.data_do_ultimo_full(status) == "2026-11-18T10:00:00Z"
    assert ultimo_ciclo.data_do_ultimo_full({}) is None


@pytest.fixture
def como_master():
    """Finge um Master logado só nestes testes (a rota é do Master, como as de backup)."""
    app.dependency_overrides[get_current_master_user] = lambda: {"sub": "1", "is_master": True}
    yield
    app.dependency_overrides.pop(get_current_master_user, None)


def test_rota_de_avisos_exige_master():
    # Amarração: trocar a dependência liberaria a rota para qualquer funcionário
    from app.api.v1.endpoints import backup as endpoint_backup
    rota = next(r for r in endpoint_backup.router.routes if getattr(r, "path", "") == "/avisos")
    assert get_current_master_user in [d.call for d in rota.dependant.dependencies]


def test_ct05_rota_de_avisos_traz_ciclo_e_pasta(client, como_master):
    ultimo_ciclo.registrar("TRIAL_BACKUP_USADO", feito_em="2026-11-18T10:00:00Z")
    permissoes._marcar_pasta_aberta()
    resposta = client.get("/api/v1/backup/avisos")
    assert resposta.status_code == 200
    avisos = {a["codigo"]: a for a in resposta.json()["avisos"]}
    assert set(avisos) == {"TRIAL_BACKUP_USADO", "PASTA_DADOS_ABERTA"}
    assert avisos["TRIAL_BACKUP_USADO"]["desde"] and avisos["PASTA_DADOS_ABERTA"]["desde"]
    assert avisos["TRIAL_BACKUP_USADO"]["feito_em"] == "2026-11-18T10:00:00Z"


def test_rota_sem_avisos_devolve_lista_vazia(client, como_master):
    resposta = client.get("/api/v1/backup/avisos")
    assert resposta.json() == {"avisos": []}


def test_sync_bloqueado_devolve_o_codigo_e_a_data(monkeypatch):
    # O ciclo de envio para pelo /status (como antes), mas agora conta o motivo
    import asyncio
    import importlib
    # `app.services.cloud.sync` é ao mesmo tempo o módulo e a função reexportada
    # pelo pacote; importlib pega o MÓDULO.
    modulo_sync = importlib.import_module("app.services.cloud.sync")
    from app.services import backup as backup_service

    class _Resposta:
        status_code = 200

        def json(self):
            return {"planoPermiteBackup": False, "codigoBloqueio": "TRIAL_BACKUP_USADO",
                    "historicoEventos": [{"ciclo": "2026-11-17", "tipo": "FULL", "status": "CONFIRMADO",
                                          "confirmadoEm": "2026-11-18T10:00:00Z"}]}

    async def pedir(db, metodo, url, payload=None):
        return _Resposta()

    monkeypatch.setattr(modulo_sync, "_request", pedir)
    monkeypatch.setattr(backup_service, "get_last_backup", lambda: None)
    resposta = asyncio.run(modulo_sync.sync(db=None))
    assert resposta.status == "blocked"
    assert resposta.code == "TRIAL_BACKUP_USADO"
    assert resposta.feito_em == "2026-11-18T10:00:00Z"
