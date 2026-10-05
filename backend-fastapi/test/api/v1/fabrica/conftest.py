# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/fabrica/conftest.py
# DESCRIÇÃO: Fixtures da marcenaria-fábrica.
#
# `client` SEM `with`, como em test/api/v1/compras/conftest.py: com `with` o
# lifespan roda create_all() e as migrações no banco REAL da máquina.
# ---------------------------------------------------------------------------

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.depends import get_current_active_user
from app.db.models.empresa import Empresa
from app.db.models.estoque import Estoque
from app.db.models.produto import Produto
from app.main import app

from test.conftest import TEST_HWID, TEST_USER_EMAIL, TEST_USER_PASSWORD


@pytest.fixture(scope="module")
def client():
    yield TestClient(app)


@pytest.fixture
def header_com_token(client: TestClient, db_session: Session, create_test_empresa) -> dict:
    login = {"username": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD, "hwid": TEST_HWID}
    response = client.post("/api/v1/auth/login", data=login)
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def segmento(db_session: Session, header_com_token):
    """Troca o segmento da empresa de teste."""
    def _definir(valor):
        empresa = db_session.query(Empresa).first()
        empresa.segmento = valor
        db_session.commit()
    return _definir


@pytest.fixture
def marcenaria(segmento):
    segmento("marcenaria")


@pytest.fixture
def como():
    """Troca o usuário logado por um funcionário com as permissões dadas."""
    def _como(**permissoes):
        token = {"sub": "99", "empresa_id": 1, "cargo": "Marceneiro", "is_master": False, "permissoes": permissoes}
        app.dependency_overrides[get_current_active_user] = lambda: token
    yield _como
    app.dependency_overrides.pop(get_current_active_user, None)


@pytest.fixture
def chapa(db_session: Session) -> int:
    produto = Produto(nome="MDF Branco 15mm 2750x1850", codigo_produto="MDF-15-BR", unidade_medida="CH", ativo=True)
    produto.estoque = Estoque(quantidade=4, valor_varejo=0, custo_medio=30000)
    db_session.add(produto)
    db_session.commit()
    return produto.id
