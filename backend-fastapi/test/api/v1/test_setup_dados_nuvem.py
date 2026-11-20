# ---------------------------------------------------------------------------
# ARQUIVO: test_setup_dados_nuvem.py
# DESCRICAO: Re-login sem backup e cadastro novo com confirmação de e-mail
#            (LIC-03 §6.5 e §6.6; CT-08 a CT-13 e as decisões do usuário na
#            implementação: campos no /auth/reconnect, 409 no setup, códigos
#            do login repassados e o reenviar link).
#
# A nuvem é simulada por funções de mentira (monkeypatch), como nos outros
# testes de licença.
# ---------------------------------------------------------------------------

from datetime import datetime, timedelta, timezone

import httpx
import pytest

import app.core.hwid as modulo_hwid
from app.db.models.configuracao_licenca import ConfiguracaoLicenca
from app.db.models.empresa import Empresa
from app.schemas.licenca.titular import TitularNuvem
from app.services import licenca as licenca_service
from app.services.licenca import cadastro, restauracao_titular, titular_nuvem, transferencia
from app.services.licenca.transferencia import _erro

AGORA = datetime.now(timezone.utc)
HWID = "HWID-DESTE-PC"

TITULAR = {
    "tipoPessoa": "PF",
    "nomeOuRazao": "Maria da Silva",
    "documento": "529.982.247-25",
    "celular": "(85) 99999-0000",
    "endereco": {"cep": "63500-000", "logradouro": "Rua A", "numero": "10",
                 "bairro": "Centro", "cidade": "Iguatu", "estado": "CE"},
}

# Corpo do /auth/setup que a tela manda (PF). O CPF da tela é OUTRO, de propósito.
SETUP = {
    "nome_loja": "Loja da Maria",
    "tipo_pessoa": "PF",
    "nome_responsavel": "Maria da Silva",
    "cpf": "11144477735",
    "celular": "85999990000",
    "endereco": [{"cep": "63500000", "logradouro": "Rua A", "numero": "10",
                  "bairro": "Centro", "cidade": "Iguatu", "estado": "CE"}],
    "nome_usuario": "Maria",
    "email": "maria@exemplo.com.br",
    "senha": "senha-forte-123",
}


class _Resposta:
    """Resposta HTTP de mentira, com o mínimo que o código lê."""

    def __init__(self, status_code: int, corpo=None):
        self.status_code = status_code
        self._corpo = corpo
        self.text = str(corpo)

    def json(self):
        return self._corpo


def _licenca() -> ConfiguracaoLicenca:
    return ConfiguracaoLicenca(
        cliente_id="c", hwid=HWID, licenca_id="lic-1", chave_ativacao="x", public_key="x",
        limite=3, data_vencimento=AGORA + timedelta(days=30), token="t", ultima_sinc=AGORA,
        grace_period=7, proxima_validacao=AGORA + timedelta(days=1),
    )


@pytest.fixture
def depois_do_relogin(db_session, monkeypatch):
    """Banco vazio com a licença que o re-login acabou de gravar neste computador."""
    monkeypatch.setattr(modulo_hwid, "obter_hwid", lambda: HWID)
    db_session.add(_licenca())
    db_session.commit()
    return db_session


@pytest.fixture
def nuvem_do_titular(monkeypatch):
    """Simula GET e PUT do titular. Guarda o que foi enviado no PUT."""
    painel = {"get": _Resposta(200, TITULAR), "put": _Resposta(200, {}), "enviado": None}

    def pedir(db, metodo, url, corpo=None):
        if metodo == "GET":
            resposta = painel["get"]
        else:
            painel["enviado"] = corpo
            resposta = painel["put"]
        if isinstance(resposta, Exception):
            raise resposta
        return resposta

    monkeypatch.setattr(titular_nuvem, "pedir_a_nuvem", pedir)
    return painel


def _empresas(db) -> list[Empresa]:
    db.expire_all()   # relê do banco o que a rota gravou
    return db.query(Empresa).all()


# --- CT-08: dados da nuvem chegam ao front pelo /auth/reconnect ------------------

def test_ct08_reconnect_sem_empresa_traz_titular_e_backup(client, db_session, monkeypatch):
    monkeypatch.setattr(licenca_service, "reconnect_licenca", lambda db, e, s: None)
    monkeypatch.setattr(titular_nuvem, "buscar_titular", lambda db: TitularNuvem(**TITULAR))
    monkeypatch.setattr(restauracao_titular, "consultar_status_backup", lambda db: {
        "historicoEventos": [{"ciclo": "2026-11-10", "tipo": "FULL", "status": "CONFIRMADO",
                              "confirmadoEm": "2026-11-10T22:00:00Z"}],
    })
    resposta = client.post("/api/v1/auth/reconnect", json={"email": "maria@exemplo.com.br", "senha": "senha-forte-123"})
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["inicializado"] is False
    assert corpo["titular"]["documento"] == "529.982.247-25"   # só para mostrar travado
    assert corpo["backup"] == {"ciclo": "2026-11-10", "ultimo_envio": "2026-11-10T22:00:00Z"}


def test_ct08b_falha_da_nuvem_nao_derruba_o_reconnect(client, db_session, monkeypatch):
    monkeypatch.setattr(licenca_service, "reconnect_licenca", lambda db, e, s: None)

    def sem_rede(db):
        raise _erro(503, "SEM_CONEXAO", "sem rede")

    monkeypatch.setattr(titular_nuvem, "buscar_titular", sem_rede)
    monkeypatch.setattr(restauracao_titular, "consultar_status_backup", sem_rede)
    resposta = client.post("/api/v1/auth/reconnect", json={"email": "maria@exemplo.com.br", "senha": "senha-forte-123"})
    assert resposta.status_code == 200
    assert resposta.json()["titular"] is None and resposta.json()["backup"] is None


# --- CT-09 a CT-13: setup sem backup --------------------------------------------

def test_ct09_put_nao_leva_o_documento(client, depois_do_relogin, nuvem_do_titular):
    resposta = client.post("/api/v1/auth/setup", json=SETUP)
    assert resposta.status_code == 201
    enviado = nuvem_do_titular["enviado"]
    assert enviado["nomeOuRazao"] == "Maria da Silva"
    assert "documento" not in enviado and "cpf" not in enviado and "cnpj" not in enviado


def test_ct10_empresa_local_recebe_o_documento_da_nuvem(client, depois_do_relogin, nuvem_do_titular):
    resposta = client.post("/api/v1/auth/setup", json=SETUP)   # tela mandou 11144477735
    assert resposta.status_code == 201
    [empresa] = _empresas(depois_do_relogin)
    assert empresa.documento == "52998224725"   # o da nuvem, só com os números


@pytest.mark.parametrize("falha, codigo", [
    (_Resposta(502, {}), "NUVEM_INDISPONIVEL"),
    (_erro(503, "SEM_CONEXAO", "sem rede"), "SEM_CONEXAO"),
])
def test_ct11_put_falhou_nada_criado(client, depois_do_relogin, nuvem_do_titular, falha, codigo):
    nuvem_do_titular["put"] = falha
    resposta = client.post("/api/v1/auth/setup", json=SETUP)
    assert resposta.status_code == 503
    assert resposta.json()["detail"]["codigo"] == codigo
    assert _empresas(depois_do_relogin) == []


@pytest.mark.parametrize("http, codigo", [
    (401, "LICENCA_HWID_REVOGADO"),
    (403, "DOCUMENTO_TRAVADO"),
])
def test_ct12_put_recusado_com_codigo(client, depois_do_relogin, nuvem_do_titular, http, codigo):
    nuvem_do_titular["put"] = _Resposta(http, {"codigo": codigo, "message": "recusado"})
    resposta = client.post("/api/v1/auth/setup", json=SETUP)
    assert resposta.status_code == http
    assert resposta.json()["detail"]["codigo"] == codigo
    assert _empresas(depois_do_relogin) == []


def test_ct12b_put_400_de_validacao(client, depois_do_relogin, nuvem_do_titular):
    nuvem_do_titular["put"] = _Resposta(400, {"message": "telefone inválido"})
    resposta = client.post("/api/v1/auth/setup", json=SETUP)
    assert resposta.status_code == 400
    assert _empresas(depois_do_relogin) == []


def test_ct13_api_sem_a_rota_setup_como_hoje(client, depois_do_relogin, nuvem_do_titular):
    nuvem_do_titular["get"] = _Resposta(404, {})
    resposta = client.post("/api/v1/auth/setup", json=SETUP)
    assert resposta.status_code == 201
    assert nuvem_do_titular["enviado"] is None             # nem tentou o PUT
    [empresa] = _empresas(depois_do_relogin)
    assert empresa.documento == "11144477735"              # o da tela, como sempre


# --- Cadastro novo: 202 da nuvem vira 409 CONFIRMACAO_NECESSARIA (§6.5) ----------

def test_cadastro_202_nada_gravado_e_409(client, db_session, monkeypatch):
    monkeypatch.setattr(modulo_hwid, "obter_hwid", lambda: HWID)
    monkeypatch.setattr(cadastro, "obter_hwid", lambda: HWID)
    enviados = []

    class _Cliente:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, url, json=None, **k):
            enviados.append(json)
            return _Resposta(202, {"mensagem": "Enviamos as instruções para o seu e-mail."})

    monkeypatch.setattr(httpx, "Client", _Cliente)
    resposta = client.post("/api/v1/auth/setup", json=SETUP)
    assert resposta.status_code == 409
    assert resposta.json()["detail"]["codigo"] == "CONFIRMACAO_NECESSARIA"
    assert enviados[0]["fluxoConfirmacao"] is True
    db_session.expire_all()
    assert db_session.query(ConfiguracaoLicenca).count() == 0
    assert _empresas(db_session) == []


# --- Códigos do login da nuvem repassados (decisão do usuário) ------------------

@pytest.mark.parametrize("http, codigo, local", [
    (403, "AGUARDANDO_CONFIRMACAO_EMAIL", 403),
    (429, "MUITAS_TENTATIVAS", 429),
    (402, "LICENCA_VENCIDA", 403),
    (400, "SEM_LICENCA_ATIVA", 403),
])
def test_login_da_nuvem_repassa_o_codigo(monkeypatch, http, codigo, local):
    class _Cliente:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, url, json=None, **k):
            return _Resposta(http, {"codigo": codigo, "message": "da nuvem"})

    monkeypatch.setattr(httpx, "Client", _Cliente)
    with pytest.raises(Exception) as erro:
        transferencia._entrar_na_conta("a@b.com", "x", HWID)
    assert erro.value.status_code == local
    assert erro.value.detail["codigo"] == codigo


def test_login_outro_4xx_continua_conta_recusada(monkeypatch):
    class _Cliente:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, url, json=None, **k):
            return _Resposta(400, {"message": "Conta bloqueada"})

    monkeypatch.setattr(httpx, "Client", _Cliente)
    with pytest.raises(Exception) as erro:
        transferencia._entrar_na_conta("a@b.com", "x", HWID)
    assert erro.value.detail["codigo"] == "CONTA_RECUSADA"


# --- Reenviar link (rota local pública) -----------------------------------------

@pytest.mark.parametrize("http", [202, 404])
def test_reenviar_link_sempre_202(client, monkeypatch, http):
    class _Cliente:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, url, json=None, **k):
            return _Resposta(http, {})

    monkeypatch.setattr(httpx, "Client", _Cliente)
    resposta = client.post("/api/v1/licenca/reenviar-link", json={"email": "quem@exemplo.com.br"})
    assert resposta.status_code == 202


def test_reenviar_link_sem_rede(client, monkeypatch):
    class _Cliente:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, url, json=None, **k):
            raise httpx.ConnectError("sem internet")

    monkeypatch.setattr(httpx, "Client", _Cliente)
    resposta = client.post("/api/v1/licenca/reenviar-link", json={"email": "quem@exemplo.com.br"})
    assert resposta.status_code == 503
    assert resposta.json()["detail"]["codigo"] == "SEM_CONEXAO"


def test_reconnect_com_status_que_nao_e_json_nao_cai(client, db_session, monkeypatch):
    # A nuvem respondeu 200 com HTML (proxy, manutenção): o re-login já deu certo
    # e não pode virar erro 500 por causa do resumo do backup.
    class _NaoJson(_Resposta):
        def json(self):
            raise ValueError("não é JSON")

    monkeypatch.setattr(licenca_service, "reconnect_licenca", lambda db, e, s: None)
    monkeypatch.setattr(titular_nuvem, "pedir_a_nuvem", lambda db, m, u, c=None: _NaoJson(200, "<html>"))
    resposta = client.post("/api/v1/auth/reconnect", json={"email": "maria@exemplo.com.br", "senha": "senha-forte-123"})
    assert resposta.status_code == 200
    assert resposta.json()["backup"] is None and resposta.json()["titular"] is None
