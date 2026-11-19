# ---------------------------------------------------------------------------
# ARQUIVO: test/services/licenca/test_segredos_licenca.py
# DESCRICAO: LIC-01 (CT-01 a CT-11) -- token e chave de ativacao guardados no
#            cofre (DPAPI no Windows; aqui, o cofre falso de test/apoio/).
#
# O cofre falso imita o que importa da DPAPI: o que foi trancado "nesta
# maquina" abre; o que foi trancado em outra nao abre; e o Windows pode
# recusar. A troca da DPAPI pelo falso e feita pela fixture `usar_cofre_falso`
# do test/conftest.py, que vale para todos os testes.
# ---------------------------------------------------------------------------

import logging
import pathlib
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from app.db.models.configuracao_licenca import ConfiguracaoLicenca
from app.services.licenca import cofre
from app.services.licenca import segredos_licenca
from app.services.licenca import validacao as licenca_validacao
from app.services.licenca.cripto import encriptar_valor
from test.apoio import cofre_falso

HWID = "HWID-DESTE-COMPUTADOR"
CHAVE = "CHAVE-ATIVACAO-DO-CLIENTE"
TOKEN_ANTIGO = "eyJ.token-antigo.assinatura"   # JWT sempre comeca com "eyJ"
TOKEN_NOVO = "eyJ.token-novo.assinatura"
AGORA = datetime.now(timezone.utc)


# ===========================================================================
# Apoio
# ===========================================================================

def _licenca_formato_antigo(db) -> ConfiguracaoLicenca:
    """Licenca como esta hoje nas lojas: token em texto puro e chave pelo HWID."""
    licenca = ConfiguracaoLicenca(
        cliente_id="cliente-abc",
        hwid=HWID,
        licenca_id="lic-abc",
        chave_ativacao=encriptar_valor(CHAVE, HWID),
        public_key=encriptar_valor("PEM-FALSO", HWID),
        limite=3,
        data_vencimento=AGORA + timedelta(days=30),
        token=TOKEN_ANTIGO,
        ultima_sinc=AGORA,
        grace_period=7,
        proxima_validacao=AGORA + timedelta(days=1),
    )
    db.add(licenca)
    db.commit()
    return licenca


def _colunas(db) -> tuple[str, str]:
    """Le direto do banco o que esta gravado nas duas colunas de segredo."""
    db.expire_all()   # descarta o que a sessao lembra e le de novo do banco
    licenca = db.query(ConfiguracaoLicenca).one()
    return licenca.token, licenca.chave_ativacao


class _Resposta:
    """Resposta HTTP de mentira, so com o que o codigo le."""

    def __init__(self, status_code: int, corpo: dict):
        self.status_code = status_code
        self._corpo = corpo
        self.text = str(corpo)

    def json(self):
        return self._corpo


def _nuvem_aprova_conectar(monkeypatch) -> list[dict]:
    """Finge a nuvem: o POST /licenca/conectar aprova e manda o TOKEN_NOVO."""
    chamadas: list[dict] = []

    class _Cliente:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, url, json=None, **kwargs):
            chamadas.append({"url": url, "json": json})
            return _Resposta(201, {
                "msg": "Conexão autorizada.",
                "licencaId": "lic-abc",
                "chaveAtivacao": CHAVE,
                "limite": 3,
                "dataVencimento": (AGORA + timedelta(days=30)).isoformat(),
                "token": TOKEN_NOVO,
                "ultimaSincronizacao": AGORA.isoformat(),
                "gracePeriodDias": 7,
                "proximaValidacaoEm": (AGORA + timedelta(days=1)).isoformat(),
            })

    monkeypatch.setattr(httpx, "Client", _Cliente)
    monkeypatch.setattr(licenca_validacao, "obter_hwid", lambda: HWID)
    return chamadas


# ===========================================================================
# CT-01 a CT-05: guardar e ler
# ===========================================================================

def test_ct01_guardar_e_ler_token_devolve_o_mesmo_token():
    guardado = segredos_licenca.guardar_token(TOKEN_NOVO)

    assert guardado.startswith("dpapi:v1:")       # marca de "ja esta no cofre"
    assert TOKEN_NOVO not in guardado             # o token nao fica a vista
    assert segredos_licenca.ler_token(guardado) == TOKEN_NOVO


def test_ct02_ler_token_antigo_sem_prefixo_devolve_como_esta():
    assert segredos_licenca.ler_token(TOKEN_ANTIGO) == TOKEN_ANTIGO
    assert segredos_licenca.ler_token(None) is None


def test_ct03_ler_token_que_nao_abre_levanta_segredo_ilegivel():
    guardado = segredos_licenca.guardar_token(TOKEN_NOVO)
    cofre_falso.maquina = "outro-computador"      # o banco foi parar em outra maquina

    with pytest.raises(cofre.SegredoIlegivel):
        segredos_licenca.ler_token(guardado)


def test_ct04_guardar_e_ler_chave_devolve_a_mesma_chave():
    guardado = segredos_licenca.guardar_chave_ativacao(CHAVE)

    assert guardado.startswith("dpapi:v1:")
    assert CHAVE not in guardado
    assert segredos_licenca.ler_chave_ativacao(guardado, HWID) == CHAVE


def test_ct05_ler_chave_no_formato_antigo_abre_pelo_hwid():
    antiga = encriptar_valor(CHAVE, HWID)

    assert segredos_licenca.ler_chave_ativacao(antiga, HWID) == CHAVE


# ===========================================================================
# CT-06 a CT-08: migracao no startup
# ===========================================================================

def test_ct06_migracao_tranca_token_e_chave_antigos(db_session):
    _licenca_formato_antigo(db_session)

    segredos_licenca.migrar_segredos(db_session, HWID)

    token, chave = _colunas(db_session)
    assert token.startswith("dpapi:v1:")
    assert chave.startswith("dpapi:v1:")
    assert segredos_licenca.ler_token(token) == TOKEN_ANTIGO
    assert segredos_licenca.ler_chave_ativacao(chave, HWID) == CHAVE


def test_ct07_migracao_rodada_duas_vezes_nao_muda_nada_na_segunda(db_session):
    _licenca_formato_antigo(db_session)
    segredos_licenca.migrar_segredos(db_session, HWID)
    depois_da_primeira = _colunas(db_session)

    segredos_licenca.migrar_segredos(db_session, HWID)

    assert _colunas(db_session) == depois_da_primeira


def test_ct08_migracao_com_cofre_falhando_nao_altera_nada_nem_derruba(db_session, caplog):
    _licenca_formato_antigo(db_session)
    antes = _colunas(db_session)
    cofre_falso.sempre_falhar = True

    with caplog.at_level(logging.WARNING):
        segredos_licenca.migrar_segredos(db_session, HWID)   # nao pode lancar

    assert _colunas(db_session) == antes
    assert "COFRE" in caplog.text.upper()


def test_migracao_sem_licenca_nao_faz_nada(db_session):
    segredos_licenca.migrar_segredos(db_session, HWID)   # banco sem licenca: nada a fazer

    assert db_session.query(ConfiguracaoLicenca).count() == 0


# ===========================================================================
# CT-09 e CT-10: o cofre na validacao da licenca
# ===========================================================================

def test_ct09_validacao_online_ok_mas_cofre_falha_ao_gravar_mantem_token_anterior(
    db_session, monkeypatch, caplog
):
    licenca = _licenca_formato_antigo(db_session)
    segredos_licenca.migrar_segredos(db_session, HWID)
    token_guardado_antes, _ = _colunas(db_session)
    _nuvem_aprova_conectar(monkeypatch)
    # A partir daqui a gravacao falha; a leitura da chave (antes) ja aconteceu
    # pelo caminho do cofre. Para a leitura funcionar e so a gravacao falhar,
    # o teste troca so o `proteger`.
    monkeypatch.setattr(cofre, "proteger", _proteger_que_falha)

    with caplog.at_level(logging.WARNING):
        resultado = licenca_validacao.verificar_licenca_ativa(db_session)

    assert resultado["status"] == "online_valid"           # a licenca continua valida
    token_depois, _ = _colunas(db_session)
    assert token_depois == token_guardado_antes             # o token anterior ficou
    assert "COFRE" in caplog.text.upper()                   # e o log registrou
    assert licenca.licenca_id == "lic-abc"


def _proteger_que_falha(dados: bytes) -> bytes:
    raise cofre.CofreIndisponivel("Windows recusou (simulado).")


def test_ct10_token_que_nao_abre_com_internet_pede_outro_e_regrava(db_session, monkeypatch):
    _licenca_formato_antigo(db_session)
    segredos_licenca.migrar_segredos(db_session, HWID)
    # Token gravado "em outra maquina": nao abre aqui. A chave continua boa.
    licenca = db_session.query(ConfiguracaoLicenca).one()
    cofre_falso.maquina = "outro-computador"
    licenca.token = segredos_licenca.guardar_token(TOKEN_ANTIGO)
    cofre_falso.maquina = "maquina-de-teste"
    db_session.commit()
    chamadas = _nuvem_aprova_conectar(monkeypatch)

    resultado = licenca_validacao.verificar_licenca_ativa(db_session)

    assert resultado["status"] == "online_valid"
    assert chamadas and chamadas[0]["json"]["chave"] == CHAVE   # pediu com a chave
    token, _ = _colunas(db_session)
    assert segredos_licenca.ler_token(token) == TOKEN_NOVO       # e regravou no cofre


# ===========================================================================
# CT-11: o cofre falso nunca entra no app
# ===========================================================================

def test_ct11_nenhum_arquivo_do_app_menciona_o_cofre_falso():
    pasta_app = pathlib.Path(__file__).resolve().parents[3] / "app"

    citam = [
        str(arquivo)
        for arquivo in pasta_app.rglob("*.py")
        if "cofre_falso" in arquivo.read_text(encoding="utf-8")
    ]

    assert citam == []


# ===========================================================================
# Erros de tela (LIC-01 §6.4) e as portas que leem os segredos
# ===========================================================================

def _cair_a_internet(monkeypatch) -> None:
    """Finge a nuvem fora do ar: o POST /licenca/conectar nao conecta."""

    class _Cliente:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, url, json=None, **kwargs):
            raise httpx.ConnectError("sem internet")

    monkeypatch.setattr(httpx, "Client", _Cliente)
    monkeypatch.setattr(licenca_validacao, "obter_hwid", lambda: HWID)


def test_banco_copiado_no_formato_novo_pede_transferencia(db_session, monkeypatch):
    """Revisao 2 da SPEC-01: a chave que nao abre responde o codigo que o app
    ja leva para a tela de transferencia (decisao do usuario, 2026-11-19)."""
    from fastapi import HTTPException

    _licenca_formato_antigo(db_session)
    segredos_licenca.migrar_segredos(db_session, HWID)
    cofre_falso.maquina = "notebook-novo"       # o banco foi aberto em outro computador
    _nuvem_aprova_conectar(monkeypatch)

    with pytest.raises(HTTPException) as erro:
        licenca_validacao.verificar_licenca_ativa(db_session)

    assert erro.value.status_code == 403
    assert erro.value.detail["codigo"] == "LICENCA_DE_OUTRA_MAQUINA"


def test_cofre_fora_do_ar_responde_503_cofre_indisponivel(db_session, monkeypatch):
    from fastapi import HTTPException

    _licenca_formato_antigo(db_session)
    segredos_licenca.migrar_segredos(db_session, HWID)
    cofre_falso.sempre_falhar = True
    _nuvem_aprova_conectar(monkeypatch)

    with pytest.raises(HTTPException) as erro:
        licenca_validacao.verificar_licenca_ativa(db_session)

    assert erro.value.status_code == 503
    assert erro.value.detail["codigo"] == "COFRE_INDISPONIVEL"


def test_token_que_nao_abre_sem_internet_responde_token_ilegivel(db_session, monkeypatch):
    from fastapi import HTTPException

    _licenca_formato_antigo(db_session)
    segredos_licenca.migrar_segredos(db_session, HWID)
    licenca = db_session.query(ConfiguracaoLicenca).one()
    cofre_falso.maquina = "outro-computador"
    licenca.token = segredos_licenca.guardar_token(TOKEN_ANTIGO)   # token de outra maquina
    cofre_falso.maquina = "maquina-de-teste"
    db_session.commit()
    _cair_a_internet(monkeypatch)
    # A chave publica nao e lida da rede nesse caminho: ela esta no banco.
    monkeypatch.setattr(licenca_validacao, "decriptar_valor", lambda valor, hwid: "PEM-FALSO")

    with pytest.raises(HTTPException) as erro:
        licenca_validacao.verificar_licenca_ativa(db_session)

    assert erro.value.status_code == 403
    assert erro.value.detail["codigo"] == "TOKEN_ILEGIVEL"


def test_fiscal_recebe_o_token_aberto_do_cofre(db_session):
    """O fiscal (get_licenca_token) manda o token no Bearer da API fiscal:
    precisa do token aberto, nunca do 'dpapi:v1:...' (decisao do usuario)."""
    from app.db.crud import fiscal as fiscal_crud

    _licenca_formato_antigo(db_session)
    segredos_licenca.migrar_segredos(db_session, HWID)

    assert fiscal_crud.get_licenca_token(db_session) == TOKEN_ANTIGO

    cofre_falso.maquina = "outro-computador"
    assert fiscal_crud.get_licenca_token(db_session) == ""   # nao abre: vazio, como sem token


def test_nuvem_recebe_o_token_aberto_do_cofre(db_session):
    from app.services.cloud import _http as cloud_http

    _licenca_formato_antigo(db_session)
    segredos_licenca.migrar_segredos(db_session, HWID)

    assert cloud_http._get_license_token(db_session) == TOKEN_ANTIGO


def test_migracao_no_startup_nunca_derruba_o_boot(monkeypatch):
    """Sem HWID (ou com qualquer erro), a tarefa do startup so registra no log."""
    from app.core import tarefas

    def _sem_hwid():
        raise RuntimeError("HWID indisponivel")

    monkeypatch.setattr(tarefas, "obter_hwid", _sem_hwid)

    tarefas._migrar_segredos_da_licenca()   # nao pode lancar
    tarefas._verificar_pasta_de_dados()     # idem
