# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/test_servico_fiscal_nfse.py
# DESCRICAO: O cadastro fiscal do servico com a NFS-e (F1 do docs/nfse-plano.md):
#            prestador so com o modulo NFSE consegue preencher o servico, e
#            quem tem NFE continua exatamente como antes.
# ---------------------------------------------------------------------------

import pytest
from fastapi.testclient import TestClient

from app.db.models.empresa import Empresa
from app.db.models.empresa_fiscal_settings import EmpresaFiscalSettings

TEST_USER_EMAIL = "teste.funcionario@example.com"
TEST_USER_PASSWORD = "senhaSegura456"
TEST_HWID = "test-terminal-hwid"


@pytest.fixture(scope="function")
def loja(client: TestClient, db_session, create_test_empresa) -> dict:
    login = client.post("/api/v1/auth/login", data={
        "username": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD, "hwid": TEST_HWID,
    })
    if login.status_code != 200:
        pytest.skip("Falha na autenticação do usuário de teste.")
    empresa = db_session.query(Empresa).first()
    if not db_session.query(EmpresaFiscalSettings).filter_by(empresa_id=empresa.id).first():
        db_session.add(EmpresaFiscalSettings(
            empresa_id=empresa.id, serie_nfe=1, ultimo_numero_nfe=0, ambiente_emissao=2,
        ))
        db_session.commit()
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.fixture
def licenca(monkeypatch):
    from app.core import modulos as modulos_mod

    def _com(*modulos):
        monkeypatch.setattr(modulos_mod.licenca_service, "modulos_da_licenca", lambda db: list(modulos))
    return _com


def _servico(client, loja) -> int:
    r = client.post("/api/v1/servicos/", json={"descricao": "Suporte em informatica", "valor": 15000}, headers=loja)
    assert r.status_code == 201, r.text
    return r.json()["id"]


@pytest.mark.parametrize("modulos", [("NFSE",), ("NFE",), ("NFE", "NFSE")])
def test_nfe_ou_nfse_preenche_o_servico(client, loja, licenca, modulos):
    licenca("FINANCEIRO")                    # o cadastro do serviço não depende de módulo
    servico_id = _servico(client, loja)
    licenca(*modulos)

    r = client.put(f"/api/v1/servicos/{servico_id}/fiscal", json={
        "codigo_servico_lc116": "01.07",
        "codigo_tributacao_nacional": "01.07.01",
        "codigo_nbs": "1.1501.30.00",
    }, headers=loja)

    assert r.status_code == 200, r.text
    assert (r.json()["codigo_tributacao_nacional"], r.json()["codigo_nbs"]) == ("010701", "115013000")
    lido = client.get(f"/api/v1/servicos/{servico_id}/fiscal", headers=loja).json()
    assert lido["codigo_servico_lc116"] == "0107"


def test_sem_nfe_e_sem_nfse_continua_recusando_igual(client, loja, licenca):
    licenca("FINANCEIRO")
    servico_id = _servico(client, loja)

    r = client.get(f"/api/v1/servicos/{servico_id}/fiscal", headers=loja)

    assert r.status_code == 403
    assert r.json()["detail"]["modulo"] == "NFE"      # a mesma recusa de antes da NFS-e


def test_salvar_sem_os_campos_novos_nao_apaga_os_codigos(client, loja, licenca):
    """Tela de quem só tem NFE não manda os campos da NFS-e: eles ficam."""
    licenca("NFE", "NFSE")
    servico_id = _servico(client, loja)
    client.put(f"/api/v1/servicos/{servico_id}/fiscal", json={
        "codigo_tributacao_nacional": "010701", "codigo_nbs": "115013000",
    }, headers=loja)

    licenca("NFE")
    client.put(f"/api/v1/servicos/{servico_id}/fiscal", json={"cfop_padrao": "5933"}, headers=loja)

    licenca("NFE", "NFSE")
    lido = client.get(f"/api/v1/servicos/{servico_id}/fiscal", headers=loja).json()
    assert (lido["codigo_tributacao_nacional"], lido["codigo_nbs"], lido["cfop_padrao"]) == ("010701", "115013000", "5933")
