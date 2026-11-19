# ---------------------------------------------------------------------------
# ARQUIVO: test/services/licenca/test_heartbeat_token.py
# DESCRICAO: LIC-02 (CT-19 a CT-21) -- o heartbeat dos caixas manda o token da
#            licenca, e um 404 SESSAO_INEXISTENTE reconecta o caixa sem
#            bloquear a licenca (ACORDO D-37, lado do app da LIC-09).
#
# Lembrete (docs/licenca/learn): a versao instalada BLOQUEIA a licenca quando
# todos os caixas recebem 400. Por isso a API nova responde 404 a sessao que
# nao existe, e o app novo reconecta em vez de remover o caixa.
# ---------------------------------------------------------------------------

import asyncio
import json
from datetime import datetime, timedelta, timezone

import httpx

from app.db.models.configuracao_licenca import ConfiguracaoLicenca
from app.db.models.terminal_conectado import TerminalConectado
from app.services.licenca import segredos_licenca
from app.services.licenca import sincronizacao
from app.services.licenca.constantes import API_CONECTAR_URL, API_HEARTBEAT_URL
from app.services.licenca.cripto import encriptar_valor

HWID_SERVIDOR = "HWID-DO-SERVIDOR"
CHAVE = "CHAVE-ATIVACAO-DO-CLIENTE"
TOKEN = "eyJ.token-da-licenca.assinatura"
AGORA = datetime.now(timezone.utc)


def _loja(db, caixas: list[str]) -> None:
    """Servidor com a licenca no cofre e os caixas conectados."""
    db.add(ConfiguracaoLicenca(
        cliente_id="cliente-abc",
        hwid=HWID_SERVIDOR,
        licenca_id="lic-abc",
        chave_ativacao=segredos_licenca.guardar_chave_ativacao(CHAVE),
        public_key=encriptar_valor("PEM", HWID_SERVIDOR),
        limite=5,
        data_vencimento=AGORA + timedelta(days=30),
        token=segredos_licenca.guardar_token(TOKEN),
        ultima_sinc=AGORA,
        grace_period=7,
        proxima_validacao=AGORA + timedelta(days=5),
    ))
    for hwid in caixas:
        db.add(TerminalConectado(hwid=hwid))
    db.commit()


class _Resposta:
    def __init__(self, status_code: int, corpo: dict | None = None):
        self.status_code = status_code
        self._corpo = corpo or {}
        self.text = json.dumps(self._corpo)   # a API responde JSON

    def json(self):
        return self._corpo


def _nuvem(monkeypatch, resposta_heartbeat: _Resposta) -> list[dict]:
    """Finge a API: o heartbeat devolve `resposta_heartbeat`; o conectar aceita."""
    chamadas: list[dict] = []

    class _ClienteAsync:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, json=None, headers=None, **kwargs):
            chamadas.append({"url": url, "json": json, "headers": headers or {}})
            if url == API_HEARTBEAT_URL:
                return resposta_heartbeat
            return _Resposta(201, {"msg": "Conexão autorizada."})

    monkeypatch.setattr(httpx, "AsyncClient", _ClienteAsync)
    monkeypatch.setattr(sincronizacao, "obter_hwid", lambda: HWID_SERVIDOR)
    return chamadas


def _licenca(db) -> ConfiguracaoLicenca:
    db.expire_all()
    return db.query(ConfiguracaoLicenca).one()


def _caixas(db) -> list[str]:
    db.expire_all()
    return sorted(t.hwid for t in db.query(TerminalConectado).all())


def test_ct19_heartbeat_manda_o_token_da_licenca(db_session, monkeypatch):
    _loja(db_session, ["CAIXA-01"])
    chamadas = _nuvem(monkeypatch, _Resposta(201))

    asyncio.run(sincronizacao.enviar_heartbeat(db_session))

    heartbeat = [c for c in chamadas if c["url"] == API_HEARTBEAT_URL]
    assert heartbeat[0]["headers"].get("Authorization") == f"Bearer {TOKEN}"
    assert heartbeat[0]["json"] == {"licencaId": "lic-abc", "hwid": "CAIXA-01"}


def test_heartbeat_sem_token_legivel_segue_sem_o_cabecalho(db_session, monkeypatch):
    """Token que nao abre (cofre fora do ar): o heartbeat vai como hoje."""
    from test.apoio import cofre_falso

    _loja(db_session, ["CAIXA-01"])
    chamadas = _nuvem(monkeypatch, _Resposta(201))
    cofre_falso.maquina = "outro-computador"

    asyncio.run(sincronizacao.enviar_heartbeat(db_session))

    heartbeat = [c for c in chamadas if c["url"] == API_HEARTBEAT_URL]
    assert "Authorization" not in heartbeat[0]["headers"]


def test_ct20_sessao_inexistente_reconecta_o_caixa_sem_remover_nem_bloquear(db_session, monkeypatch):
    _loja(db_session, ["CAIXA-01"])
    chamadas = _nuvem(monkeypatch, _Resposta(404, {"codigo": "SESSAO_INEXISTENTE"}))

    asyncio.run(sincronizacao.enviar_heartbeat(db_session))

    reconexoes = [c for c in chamadas if c["url"] == API_CONECTAR_URL]
    assert reconexoes == [{
        "url": API_CONECTAR_URL,
        "json": {"chave": CHAVE, "hwid": "CAIXA-01"},   # com a chave de ativacao
        "headers": {},
    }]
    assert _caixas(db_session) == ["CAIXA-01"]          # o caixa continua na tabela
    assert _licenca(db_session).bloqueada is False


def test_ct21_todos_os_caixas_com_404_nao_bloqueiam_a_licenca(db_session, monkeypatch):
    _loja(db_session, ["CAIXA-01", "CAIXA-02"])
    _nuvem(monkeypatch, _Resposta(404, {"codigo": "SESSAO_INEXISTENTE"}))

    asyncio.run(sincronizacao.enviar_heartbeat(db_session))

    assert _licenca(db_session).bloqueada is False
    assert _caixas(db_session) == ["CAIXA-01", "CAIXA-02"]


def test_400_continua_removendo_e_bloqueando_como_hoje(db_session, monkeypatch):
    """A regra antiga do 400 nao muda (LIC-02 §6.8)."""
    _loja(db_session, ["CAIXA-01"])
    _nuvem(monkeypatch, _Resposta(400, {"message": "Sessão encerrada."}))

    asyncio.run(sincronizacao.enviar_heartbeat(db_session))

    assert _caixas(db_session) == []
    assert _licenca(db_session).bloqueada is True


def test_401_e_403_novos_so_vao_para_o_log(db_session, monkeypatch):
    _loja(db_session, ["CAIXA-01", "CAIXA-02"])
    _nuvem(monkeypatch, _Resposta(401, {"codigo": "LICENCA_HWID_REVOGADO"}))

    asyncio.run(sincronizacao.enviar_heartbeat(db_session))

    assert _caixas(db_session) == ["CAIXA-01", "CAIXA-02"]
    assert _licenca(db_session).bloqueada is False


def test_renovacao_em_segundo_plano_grava_a_carencia(db_session, monkeypatch):
    """F25: a renovacao tambem guarda emCarencia/dataLimiteCarencia (so para a tela)."""
    _loja(db_session, [])
    licenca = _licenca(db_session)
    licenca.proxima_validacao = AGORA + timedelta(hours=1)   # perto: a renovacao roda
    db_session.commit()
    limite = AGORA + timedelta(days=4)

    class _ClienteAsync:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, json=None, **kwargs):
            return _Resposta(201, {
                "valida": True,
                "licencaId": "lic-abc",
                "status": "ATIVA",
                "token": "eyJ.token-renovado.x",
                "proximaValidacaoEm": (AGORA + timedelta(days=5)).isoformat(),
                "ultimaSincronizacao": AGORA.isoformat(),
                "dataVencimento": (AGORA - timedelta(days=1)).isoformat(),
                "gracePeriodDias": 7,
                "emCarencia": True,
                "dataLimiteCarencia": limite.isoformat(),
            })

    monkeypatch.setattr(httpx, "AsyncClient", _ClienteAsync)
    monkeypatch.setattr(sincronizacao, "obter_hwid", lambda: HWID_SERVIDOR)

    asyncio.run(sincronizacao.renovar_licenca_background(db_session))

    licenca = _licenca(db_session)
    assert licenca.em_carencia is True
    assert licenca.data_limite_carencia.replace(tzinfo=timezone.utc) == limite
    assert segredos_licenca.ler_token(licenca.token) == "eyJ.token-renovado.x"
