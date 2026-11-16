# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/fiscal/conftest.py
# DESCRIÇÃO: Fixtures dos testes de endpoint do módulo fiscal.
#
# POR QUE EXISTE
# --------------
# A fixture `client` de test/conftest.py abre o TestClient com `with`, o que
# dispara o lifespan do app -- e o lifespan roda create_all() + migrações no
# ENGINE REAL (app.db.session.engine), não no SQLite em memória do conftest.
# Nesta máquina isso aponta para o banco da loja, e a migration
# f44a5daad28c (ADD COLUMN sem checar existência) derruba o boot. Todo teste
# que usa `client` erra no setup (552 erros na suíte em 17/09/2026).
#
# Aqui o `client` é redefinido SEM `with`: o Starlette só executa o lifespan
# dentro do context manager, então nada toca o banco real, e as rotas seguem
# usando o SQLite em memória via override de get_db.
# ---------------------------------------------------------------------------

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.models.empresa import Empresa
from app.db.models.empresa_fiscal_settings import EmpresaFiscalSettings

from test.conftest import TEST_HWID, TEST_USER_EMAIL, TEST_USER_PASSWORD


@pytest.fixture(scope="module")
def client():
    """TestClient sem lifespan (ver cabeçalho)."""
    yield TestClient(app)


@pytest.fixture(autouse=True)
def _licenca_com_modulos_fiscais(monkeypatch):
    """Concede NFE e NFCE à licença: sem isso toda rota /fiscal responde 403."""
    from app.core import modulos as modulos_mod

    monkeypatch.setattr(
        modulos_mod.licenca_service, "modulos_da_licenca", lambda _db: ["NFE", "NFCE"]
    )


@pytest.fixture
def header_com_token(client: TestClient, db_session: Session, create_test_empresa) -> dict:
    """Bearer do usuário master criado por `create_test_empresa`."""
    login = {"username": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD, "hwid": TEST_HWID}
    response = client.post("/api/v1/auth/login", data=login)
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def empresa(db_session: Session, header_com_token) -> Empresa:
    empresa = db_session.query(Empresa).first()
    assert empresa is not None, "create_test_empresa não criou empresa"
    return empresa


@pytest.fixture
def fiscal_settings(db_session: Session, empresa: Empresa) -> EmpresaFiscalSettings:
    """Configuração fiscal mínima em homologação, numeração zerada."""
    fs = EmpresaFiscalSettings(
        empresa_id=empresa.id,
        ambiente_emissao=2,
        serie_nfe=1,
        ultimo_numero_nfe=0,
        serie_nfce=1,
        ultimo_numero_nfce=0,
        tipo_certificado="ARQUIVO",
    )
    db_session.add(fs)
    db_session.commit()
    db_session.refresh(fs)
    return fs
