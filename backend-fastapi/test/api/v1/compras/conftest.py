# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/compras/conftest.py
# DESCRIÇÃO: Fixtures dos testes do módulo de Compras.
#
# O `client` é redefinido SEM `with`, pelo mesmo motivo de
# test/api/v1/fiscal/conftest.py: com `with` o lifespan roda create_all() e
# as migrações no banco REAL da máquina, não no SQLite em memória.
# ---------------------------------------------------------------------------

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.depends import get_current_active_user
from app.db.models.estoque import Estoque
from app.db.models.fornecedor import Fornecedor
from app.db.models.produto import Produto
from app.main import app

from test.conftest import TEST_HWID, TEST_USER_EMAIL, TEST_USER_PASSWORD


@pytest.fixture(scope="module")
def client():
    """TestClient sem lifespan (ver cabeçalho)."""
    yield TestClient(app)


@pytest.fixture
def licenca(monkeypatch):
    """Define os módulos da licença. Padrão dos testes daqui: COMPRAS liberado."""
    from app.core import modulos as modulos_mod

    def _definir(*modulos: str):
        monkeypatch.setattr(modulos_mod.licenca_service, "modulos_da_licenca", lambda _db: list(modulos))

    return _definir


@pytest.fixture(autouse=True)
def _com_compras(licenca):
    licenca("COMPRAS")


@pytest.fixture
def header_com_token(client: TestClient, db_session: Session, create_test_empresa) -> dict:
    """Bearer do usuário master criado por `create_test_empresa`."""
    login = {"username": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD, "hwid": TEST_HWID}
    response = client.post("/api/v1/auth/login", data=login)
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def como():
    """Troca o usuário logado por um funcionário com as permissões dadas."""
    def _como(**permissoes):
        token = {"sub": "99", "empresa_id": 1, "cargo": "Comprador", "is_master": False, "permissoes": permissoes}
        app.dependency_overrides[get_current_active_user] = lambda: token
    yield _como
    app.dependency_overrides.pop(get_current_active_user, None)


@pytest.fixture
def cadastro(db_session: Session) -> dict:
    """Cerveja (com fardo de 12) e três fornecedores: dois que vendem e uma transportadora."""
    ambev = Fornecedor(nome="Ambev SA", nome_fantasia="Ambev", cnpj="11111111000111", tipo="produto", ativo=True)
    atacado = Fornecedor(nome="Atacado Central LTDA", cnpj="22222222000122", tipo=None, ativo=True)
    frete = Fornecedor(nome="Transportes Rapidos", cnpj="33333333000133", tipo="transportadora", ativo=True)
    inativo = Fornecedor(nome="Antigo Distribuidor", cnpj="44444444000144", tipo="produto", ativo=False)
    db_session.add_all([ambev, atacado, frete, inativo])
    db_session.flush()

    produto = Produto(nome="Cerveja Lata 350ml", codigo_produto="CERV-350", unidade_medida="UN", ativo=True)
    produto.estoque = Estoque(quantidade=10, valor_varejo=450, custo_medio=300)
    outro = Produto(nome="Refrigerante 2L", codigo_produto="REFRI-2L", unidade_medida="UN", ativo=True)
    outro.estoque = Estoque(quantidade=5, valor_varejo=900)
    db_session.add_all([produto, outro])
    db_session.commit()
    return {
        "produto_id": produto.id,
        "outro_id": outro.id,
        "ambev": ambev.id,
        "atacado": atacado.id,
        "frete": frete.id,
        "inativo": inativo.id,
    }


@pytest.fixture
def fardo(client: TestClient, header_com_token, cadastro) -> int:
    """Fardo de 12 da cerveja (pela rota de embalagens que já existe)."""
    r = client.put(
        f"/api/v1/produtos/{cadastro['produto_id']}/embalagens",
        json={"embalagens": [{"sigla": "FD", "fator": 12, "preco": 4800}]},
        headers=header_com_token,
    )
    assert r.status_code == 200, r.text
    return r.json()[0]["id"]
