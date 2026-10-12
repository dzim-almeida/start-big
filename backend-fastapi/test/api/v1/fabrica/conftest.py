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


# --- OS na marcenaria depois da aposentadoria da fábrica (Spec 03A) ----------------
#
# Os testes que montavam o trilho (orçamento, trilho e separação) saíram junto
# com a fábrica (SPEC-00 FB1, Spec 03A D17). O que fica aqui serve ao teste que
# prova que ela ficou INERTE (test_fabrica_aposentada.py).


@pytest.fixture
def modo_fabrica(db_session: Session, marcenaria):
    """Grava a chave da loja (ligada por padrão). Depois da aposentadoria ela
    continua no banco, mas não liga mais nada -- é isso que os testes provam."""
    from app.db.models.configuracao_os import ConfiguracaoOS

    def _definir(ligado: bool = True):
        empresa = db_session.query(Empresa).first()
        config = db_session.query(ConfiguracaoOS).filter_by(empresa_id=empresa.id).first()
        if config is None:
            config = ConfiguracaoOS(empresa_id=empresa.id)
            db_session.add(config)
        config.modo_fabrica = ligado
        db_session.commit()

    _definir(True)
    return _definir


@pytest.fixture
def cliente_id(client: TestClient, header_com_token) -> int:
    r = client.post("/api/v1/clientes/cliente_pf", json={
        "nome": "Dona Marta", "cpf": "52998224725", "tipo": "PF", "celular": "11987654321",
        "endereco": [{"logradouro": "Rua das Flores", "numero": "100", "bairro": "Centro",
                      "cidade": "Campinas", "estado": "SP", "cep": "13010-000"}],
    }, headers=header_com_token)
    assert r.status_code == 201, r.text
    return r.json()["id"]


@pytest.fixture
def abrir_os(db_session: Session, cliente_id):
    """Abre uma OS de Móveis planejados como a aprovação do orçamento vai abrir
    (Spec 08A): pelo SERVIÇO, com `origem_orcamento=True`. O POST comum é
    recusado desde a Spec 03A. Devolve o modelo da OS (não o JSON)."""
    from app.schemas.ordem_servico import OrdemServicoCreate
    from app.services import ordem_servico as os_service

    def _abrir(nome="Cozinha apto 302", itens=None):
        dados = OrdemServicoCreate(
            cliente_id=cliente_id, prioridade="NORMAL", defeito_relatado="Cozinha planejada",
            dados_adicionais={"tipo_trabalho": "planejados"},   # o tipo fica na OS
            objeto={"modelo": nome, "dados_adicionais": {}},     # o código PRJ é gerado
            itens=itens or [],
        )
        os_ = os_service.create_ordem_servico(db_session, dados, origem_orcamento=True)
        db_session.commit()  # o endpoint faria o commit; aqui a fixture faz
        return os_
    return _abrir
