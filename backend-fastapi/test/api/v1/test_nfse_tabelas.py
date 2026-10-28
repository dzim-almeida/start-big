# ---------------------------------------------------------------------------
# ARQUIVO: test_nfse_tabelas.py
# DESCRIÇÃO: Código de tributação nacional, NBS e IBGE da NFS-e (F1 do
#            docs/nfse-plano.md), com os arquivos oficiais embarcados de
#            verdade — o teste também prova que os .csv.gz estão íntegros.
# ---------------------------------------------------------------------------

import pytest
from fastapi.testclient import TestClient

from app.core import seed_nfse
from app.db.models.nfse_tabelas import Nbs, NfseCorrelacaoNbs, NfseServicoNacional
from app.schemas.fiscal.servico import ServicoFiscalUpdate
from app.services.fiscal.nfse.municipio import codigo_ibge

TEST_USER_EMAIL = "teste.funcionario@example.com"
TEST_USER_PASSWORD = "senhaSegura456"
TEST_HWID = "test-terminal-hwid"

ROTA = "/api/v1/fiscal/nfse"


@pytest.fixture(scope="function")
def header_with_token(client: TestClient, db_session, create_test_empresa) -> dict:
    login = client.post("/api/v1/auth/login", data={
        "username": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD, "hwid": TEST_HWID,
    })
    if login.status_code != 200:
        pytest.skip("Falha na autenticação do usuário de teste.")
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.fixture
def licenca(monkeypatch):
    from app.core import modulos as modulos_mod

    def _com(*modulos):
        monkeypatch.setattr(modulos_mod.licenca_service, "modulos_da_licenca", lambda db: list(modulos))
    return _com


@pytest.fixture
def tabelas(db_session):
    """As tabelas oficiais inteiras, pelo mesmo carregador do boot."""
    seed_nfse._carregar(db_session, NfseServicoNacional, "nfse_servicos_nacionais.csv.gz")
    seed_nfse._carregar(db_session, Nbs, "nbs.csv.gz")
    seed_nfse._carregar(db_session, NfseCorrelacaoNbs, "nfse_correlacao_nbs.csv.gz")


# =========================
# Trava do módulo (R1)
# =========================

def test_sem_o_modulo_nfse_nao_libera(client, header_with_token, licenca, tabelas):
    licenca("NFE", "NFCE")
    r = client.get(f"{ROTA}/servicos-nacionais", params={"buscar": "suporte"}, headers=header_with_token)
    assert r.status_code == 403
    assert r.json()["detail"]["codigo"] == "MODULO_NAO_CONTRATADO"


def test_licenca_sem_resposta_nao_libera(client, header_with_token, licenca, tabelas):
    licenca()  # lista vazia = "não sei" → para NFSE, NÃO
    assert client.get(f"{ROTA}/nbs", headers=header_with_token).status_code == 403


# =========================
# Código de tributação nacional
# =========================

def test_acha_o_codigo_nacional_pela_descricao(client, header_with_token, licenca, tabelas):
    licenca("NFSE")
    r = client.get(f"{ROTA}/servicos-nacionais", params={"buscar": "suporte tecnico informatica"}, headers=header_with_token)
    assert r.status_code == 200
    assert "010701" in [x["codigo"] for x in r.json()["resultados"]]


def test_acha_o_codigo_nacional_digitado_com_pontos(client, header_with_token, licenca, tabelas):
    licenca("NFSE")
    r = client.get(f"{ROTA}/servicos-nacionais", params={"buscar": "14.01"}, headers=header_with_token)
    codigos = [x["codigo"] for x in r.json()["resultados"]]
    assert codigos and all(c.startswith("1401") for c in codigos)


# =========================
# NBS
# =========================

def test_sugere_o_nbs_pela_correlacao_oficial(client, header_with_token, licenca, tabelas):
    """O caso do canário: suporte em informática (01.07.01) → NBS de suporte em TI."""
    licenca("NFSE")
    r = client.get(f"{ROTA}/nbs", params={"codigo_tributacao_nacional": "010701"}, headers=header_with_token)
    sugeridos = {x["codigo"]: x["descricao"] for x in r.json()["sugeridos"]}
    assert sugeridos["115013000"] == "Serviços de suporte em tecnologia da informação (TI)"
    assert r.json()["resultados"] == []


def test_codigo_sem_correlacao_nao_sugere_nada(client, header_with_token, licenca, tabelas):
    licenca("NFSE")
    r = client.get(f"{ROTA}/nbs", params={"codigo_tributacao_nacional": "12"}, headers=header_with_token)
    assert r.json()["sugeridos"] == []


def test_busca_livre_no_nbs(client, header_with_token, licenca, tabelas):
    licenca("NFSE")
    r = client.get(f"{ROTA}/nbs", params={"buscar": "1.1501.30.00"}, headers=header_with_token)
    assert [x["codigo"] for x in r.json()["resultados"]] == ["115013000"]


def test_carga_e_idempotente(db_session, tabelas):
    antes = db_session.query(Nbs).count()
    seed_nfse._carregar(db_session, Nbs, "nbs.csv.gz")
    assert db_session.query(Nbs).count() == antes == 917


# =========================
# IBGE a partir de cidade + UF
# =========================

@pytest.mark.parametrize("cidade, uf, esperado", [
    ("Iguatu", "CE", "2305506"),
    ("Iguatu", "PR", "4110052"),           # a UF decide: são duas Iguatu
    ("IGUATU", "ce", "2305506"),
    ("São Paulo", "SP", "3550308"),
    ("sao paulo", "SP", "3550308"),
    ("Alta Floresta D'Oeste", "RO", "1100015"),
    ("Iguatu", None, None),
    ("Cidade Que Não Existe", "CE", None),
])
def test_codigo_ibge(cidade, uf, esperado):
    assert codigo_ibge(cidade, uf) == esperado


# =========================
# Cadastro do serviço
# =========================

def test_servico_grava_os_codigos_sem_pontuacao():
    dados = ServicoFiscalUpdate(codigo_tributacao_nacional="01.07.01", codigo_nbs="1.1501.30.00")
    assert (dados.codigo_tributacao_nacional, dados.codigo_nbs) == ("010701", "115013000")


@pytest.mark.parametrize("campo, valor", [
    ("codigo_tributacao_nacional", "01.07"),
    ("codigo_nbs", "1.1501.30"),
])
def test_servico_recusa_codigo_incompleto(campo, valor):
    with pytest.raises(ValueError):
        ServicoFiscalUpdate(**{campo: valor})
