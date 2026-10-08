# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/etiquetas/conftest.py
# DESCRIÇÃO: Fixtures dos testes de endpoint da Central de Etiquetas.
#
# O `client` é redefinido SEM `with`, pelo mesmo motivo de
# test/api/v1/fiscal/conftest.py: com `with` o lifespan roda create_all() e
# as migrações no banco REAL da máquina, não no SQLite em memória.
# ---------------------------------------------------------------------------

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app

from test.conftest import TEST_HWID, TEST_USER_EMAIL, TEST_USER_PASSWORD


@pytest.fixture(scope="module")
def client():
    """TestClient sem lifespan (ver cabeçalho)."""
    yield TestClient(app)


@pytest.fixture
def header_com_token(client: TestClient, db_session: Session, create_test_empresa) -> dict:
    """Bearer do usuário master criado por `create_test_empresa`."""
    login = {"username": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD, "hwid": TEST_HWID}
    response = client.post("/api/v1/auth/login", data=login)
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
