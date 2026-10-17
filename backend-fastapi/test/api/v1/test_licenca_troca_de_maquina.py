# ---------------------------------------------------------------------------
# ARQUIVO: test_licenca_troca_de_maquina.py
# DESCRICAO: Reconectar a licenca num computador novo com o banco copiado.
#
#            O CASO REAL (serigrafia, 10/2026): o cliente trocou de maquina,
#            copiou o start_big.db para a nova e o sistema subiu bloqueado em
#            CLONAGEM_DETECTADA. A licenca que veio no banco esta cifrada com o
#            HWID da maquina ANTIGA, e o reconectar nao tinha como substitui-la:
#            gravaria uma segunda linha (o get_licenca le a primeira, a antiga)
#            e, antes disso, esbarraria no `licenca_id` unique.
#
#            A invariante: a linha antiga so sai DEPOIS que a nuvem aprova o
#            login. Sem aprovacao -- senha errada, sem internet -- o banco fica
#            exatamente como estava.
# ---------------------------------------------------------------------------

from datetime import datetime, timedelta, timezone

import httpx
import pytest
from fastapi import HTTPException

from app.db.models.configuracao_licenca import ConfiguracaoLicenca
from app.services.licenca import cadastro as licenca_cadastro
from app.services.licenca import decriptar_valor, encriptar_valor


HWID_ANTIGO = "HWID-DO-COMPUTADOR-QUE-SAIU"
HWID_NOVO = "HWID-DO-COMPUTADOR-NOVO"
CHAVE_DO_CLIENTE = "CHAVE-ATIVACAO-DO-CLIENTE"
AGORA = datetime.now(timezone.utc)


class _Resposta:
    def __init__(self, status_code: int, corpo=None):
        self.status_code = status_code
        self._corpo = corpo
        self.text = str(corpo)

    def json(self):
        return self._corpo


def _nuvem(monkeypatch, *, resposta: _Resposta | None = None, offline: bool = False):
    """Finge a nuvem: o POST de login devolve `resposta` (ou cai, se offline)."""

    class _Cliente:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, *args, **kwargs):
            if offline:
                raise httpx.ConnectError("sem internet")
            return resposta

    monkeypatch.setattr(httpx, "Client", _Cliente)
    monkeypatch.setattr(licenca_cadastro, "_buscar_chave_publica_online", lambda: "PEM-FALSO")


def _login_aprovado() -> _Resposta:
    return _Resposta(200, {
        "msg": "ok",
        "clienteId": "cliente-abc",
        "licencaId": "lic-abc",  # a MESMA licenca: e a mesma conta
        "chaveAtivacao": CHAVE_DO_CLIENTE,
        "limite": 3,
        "dataVencimento": (AGORA + timedelta(days=30)).isoformat(),
        "token": "token-novo",
        "ultimaSincronizacao": AGORA.isoformat(),
        "gracePeriodDias": 7,
        "proximaValidacaoEm": (AGORA + timedelta(days=5)).isoformat(),
    })


@pytest.fixture
def banco_copiado(db_session, monkeypatch):
    """O banco que veio do computador antigo, aberto no computador novo."""
    db_session.add(ConfiguracaoLicenca(
        cliente_id="cliente-abc",
        hwid=HWID_ANTIGO,
        licenca_id="lic-abc",
        chave_ativacao=encriptar_valor(CHAVE_DO_CLIENTE, HWID_ANTIGO),
        public_key=encriptar_valor("PEM-FALSO", HWID_ANTIGO),
        limite=3,
        data_vencimento=AGORA + timedelta(days=30),
        token="token-antigo",
        ultima_sinc=AGORA,
        grace_period=7,
        proxima_validacao=AGORA + timedelta(days=5),
    ))
    db_session.commit()
    monkeypatch.setattr(licenca_cadastro, "obter_hwid", lambda: HWID_NOVO)
    return db_session


def _licencas(db):
    db.expire_all()
    return db.query(ConfiguracaoLicenca).all()


def test_reconectar_substitui_a_licenca_do_computador_antigo(banco_copiado, monkeypatch):
    _nuvem(monkeypatch, resposta=_login_aprovado())

    licenca_cadastro.reconnect_licenca(banco_copiado, "dono@loja.com", "senha-certa")
    banco_copiado.commit()

    licencas = _licencas(banco_copiado)
    assert len(licencas) == 1, "a licenca do computador antigo sobreviveu ao lado da nova"
    assert licencas[0].hwid == HWID_NOVO
    assert licencas[0].token == "token-novo"


def test_licenca_reconectada_decifra_no_computador_novo(banco_copiado, monkeypatch):
    """O que de fato tira a loja do bloqueio: o boot consegue decifrar a chave."""
    _nuvem(monkeypatch, resposta=_login_aprovado())

    licenca_cadastro.reconnect_licenca(banco_copiado, "dono@loja.com", "senha-certa")
    banco_copiado.commit()

    licenca = _licencas(banco_copiado)[0]
    assert decriptar_valor(licenca.chave_ativacao, HWID_NOVO) == CHAVE_DO_CLIENTE


def test_senha_recusada_nao_mexe_na_licenca_antiga(banco_copiado, monkeypatch):
    _nuvem(monkeypatch, resposta=_Resposta(401, {"message": "Senha incorreta"}))

    with pytest.raises(HTTPException) as erro:
        licenca_cadastro.reconnect_licenca(banco_copiado, "dono@loja.com", "senha-errada")
    assert erro.value.status_code == 401

    licencas = _licencas(banco_copiado)
    assert [l.hwid for l in licencas] == [HWID_ANTIGO]


def test_sem_internet_nao_mexe_na_licenca_antiga(banco_copiado, monkeypatch):
    _nuvem(monkeypatch, offline=True)

    with pytest.raises(HTTPException) as erro:
        licenca_cadastro.reconnect_licenca(banco_copiado, "dono@loja.com", "senha-certa")
    assert erro.value.status_code == 503

    licencas = _licencas(banco_copiado)
    assert [l.hwid for l in licencas] == [HWID_ANTIGO]


def test_maquina_que_ja_tem_a_propria_licenca_continua_recusando(banco_copiado, monkeypatch):
    """Na mesma maquina nada muda: o reconectar segue devolvendo 409."""
    monkeypatch.setattr(licenca_cadastro, "obter_hwid", lambda: HWID_ANTIGO)
    _nuvem(monkeypatch, resposta=_login_aprovado())

    with pytest.raises(HTTPException) as erro:
        licenca_cadastro.reconnect_licenca(banco_copiado, "dono@loja.com", "senha-certa")
    assert erro.value.status_code == 409

    licencas = _licencas(banco_copiado)
    assert [l.token for l in licencas] == ["token-antigo"]
