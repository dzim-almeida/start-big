# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/test_os_tipo_criacao_manual.py
# DESCRICAO: Spec 03A da marcenaria -- tipo de trabalho que so nasce de outro
#            documento (casos 11 a 18).
#
#            A OS de Moveis planejados nasce da APROVACAO de um orcamento
#            (Spec 08A). O caminho comum (POST /ordens-servico/) recusa a
#            criacao, e a OS nao troca de tipo depois. A regra le a marcacao
#            `criacao_manual` do tipo no registry, nunca o nome do segmento.
#
#            Os GUARDIOES da serigrafia (caso 17) provam que quem esta em
#            producao continua abrindo e editando OS como sempre.
# ---------------------------------------------------------------------------

import pytest
from fastapi.testclient import TestClient
from starlette import status

from app.db.models.objeto_servico import ObjetoServico
from app.db.models.ordem_servico import OrdemServico
from app.main import app
from app.schemas.ordem_servico import OrdemServicoCreate
from app.services import ordem_servico as os_service

TEST_USER_EMAIL = "teste.funcionario@example.com"
TEST_USER_PASSWORD = "senhaSegura456"

URL_OS = "/api/v1/ordens-servico"  # rota comum de OS


@pytest.fixture
def client():
    """Cliente HTTP SEM `with`: assim o lifespan do app (create_all e
    migracoes no banco real da maquina) nao roda. O banco destes testes e o
    SQLite em memoria do conftest (fixture db_session)."""
    yield TestClient(app)


# =========================
# Helpers de setup
# =========================

def _autenticar_e_criar_empresa(client, segmento: str) -> dict:
    """Cria o usuario master, faz login e cria a empresa com o segmento dado.
    Devolve o header Authorization (mesmo setup de test_os_identificador_gerado)."""
    client.post("/api/v1/usuarios/", json={
        "nome": "Admin Master",
        "email": TEST_USER_EMAIL,
        "senha": TEST_USER_PASSWORD,
    })
    login = client.post("/api/v1/auth/login", data={
        "username": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
        "hwid": "test-terminal-hwid",
    })
    assert login.status_code == 200, login.text
    header = {"Authorization": f"Bearer {login.json()['access_token']}"}

    r = client.post("/api/v1/empresas/", json={
        "razao_social": "Empresa Teste 000199 LTDA",
        "nome_fantasia": "Teste",
        "is_cnpj": True,
        "documento": "12345678000199",
        "regime_tributario": "Simples Nacional",
        "celular": "11999998888",
        "segmento": segmento,
        "endereco": [{
            "logradouro": "Av. Paulista", "numero": "1000", "bairro": "Bela Vista",
            "cidade": "São Paulo", "estado": "SP", "cep": "01310-100",
        }],
    }, headers=header)
    assert r.status_code == 201, r.text
    return header


def _criar_cliente(client, header: dict) -> int:
    """Cliente PF minimo, so para poder abrir OS."""
    r = client.post("/api/v1/clientes/cliente_pf", json={
        "nome": "Dona Marta",
        "cpf": "52998224725",
        "tipo": "PF",
        "celular": "11987654321",
        "endereco": [{
            "logradouro": "Rua das Flores", "numero": "100", "bairro": "Centro",
            "cidade": "Campinas", "estado": "SP", "cep": "13010-000",
        }],
    }, headers=header)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _corpo_os(cliente_id: int, nome: str, dados_os: dict) -> dict:
    """Corpo de abertura de OS. O tipo de trabalho vai em `dados_adicionais`
    DA OS, que e onde o frontend grava (Spec 03A, D9)."""
    return {
        "cliente_id": cliente_id,
        "prioridade": "NORMAL",
        "defeito_relatado": "Pedido de teste",
        "dados_adicionais": dados_os,
        "objeto": {"modelo": nome, "dados_adicionais": {}},
        "itens": [],
    }


def _criar_planejados_pelo_servico(db_session, cliente_id: int) -> OrdemServico:
    """Cria a OS de Planejados como a Spec 08A vai criar: pelo SERVICO, com
    `origem_orcamento=True`. O endpoint nunca expoe esse parametro (D7)."""
    dados = OrdemServicoCreate(**_corpo_os(cliente_id, "Cozinha apto 302", {"tipo_trabalho": "planejados"}))
    os_ = os_service.create_ordem_servico(db_session, dados, origem_orcamento=True)
    db_session.commit()  # o endpoint faria o commit; aqui o teste faz
    return os_


def _quantas_os_e_objetos(db_session) -> tuple[int, int]:
    """Conta o que esta gravado, para provar que a recusa nao deixou rastro."""
    db_session.expire_all()  # le do banco, nao do cache da sessao
    return db_session.query(OrdemServico).count(), db_session.query(ObjetoServico).count()


# =========================
# Marcenaria: o POST comum e recusado (casos 11, 12, 13 e 18)
# =========================

@pytest.mark.parametrize(
    "dados_os",
    [
        {"tipo_trabalho": "planejados"},        # caso 11: o tipo que nasce do orcamento
        {},                                     # caso 12: sem tipo (D5-b)
        {"tipo_trabalho": "reforma_moveis"},    # caso 13: tipo que saiu do registry
    ],
    ids=["planejados", "sem_tipo", "tipo_desconhecido"],
)
def test_marcenaria_nao_abre_os_pelo_caminho_comum(client, db_session, dados_os):
    """Casos 11 a 13: 422 explicando o caminho certo, e nada gravado."""
    header = _autenticar_e_criar_empresa(client, "marcenaria")
    cliente_id = _criar_cliente(client, header)

    r = client.post(f"{URL_OS}/", json=_corpo_os(cliente_id, "Cozinha apto 302", dados_os), headers=header)

    assert r.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, r.text
    detalhe = r.json()["detail"]
    assert "Móveis planejados" in detalhe   # o nome vem do registry, nao do codigo
    assert "Orçamentos" in detalhe          # e diz onde a OS nasce
    assert _quantas_os_e_objetos(db_session) == (0, 0)


def test_origem_orcamento_no_corpo_e_ignorado(client, db_session):
    """Caso 18: o schema nao tem o campo, entao mandar no corpo nao fura a trava."""
    header = _autenticar_e_criar_empresa(client, "marcenaria")
    cliente_id = _criar_cliente(client, header)
    corpo = _corpo_os(cliente_id, "Cozinha apto 302", {"tipo_trabalho": "planejados"})
    corpo["origem_orcamento"] = True  # tentativa de "pular a trava" pela API

    r = client.post(f"{URL_OS}/", json=corpo, headers=header)

    assert r.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, r.text
    assert _quantas_os_e_objetos(db_session) == (0, 0)


# =========================
# Marcenaria: o caminho do orcamento e a edicao (casos 14, 15 e 16)
# =========================

def test_servico_com_origem_orcamento_cria_a_os_de_planejados(client, db_session):
    """Caso 14: o caminho legitimo cria a OS e gera o codigo do projeto."""
    header = _autenticar_e_criar_empresa(client, "marcenaria")
    cliente_id = _criar_cliente(client, header)

    os_ = _criar_planejados_pelo_servico(db_session, cliente_id)

    assert os_.dados_adicionais["tipo_trabalho"] == "planejados"
    # Codigo gerado do numero da OS: "OS-2026-000001" -> "PRJ-2026-000001".
    assert os_.objeto.numero_serie == f"PRJ-{os_.numero_os.removeprefix('OS-')}"


def test_os_de_planejados_nao_troca_de_tipo(client, db_session):
    """Caso 15: virar outro tipo perderia o vinculo com o orcamento (D8)."""
    header = _autenticar_e_criar_empresa(client, "marcenaria")
    cliente_id = _criar_cliente(client, header)
    os_ = _criar_planejados_pelo_servico(db_session, cliente_id)

    r = client.put(f"{URL_OS}/{os_.numero_os}",
                   json={"dados_adicionais": {"tipo_trabalho": "outro"}}, headers=header)

    assert r.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, r.text
    assert "não pode ser alterado" in r.json()["detail"]


def test_reenviar_o_mesmo_tipo_nao_e_troca(client, db_session):
    """Caso 16: o formulario reenvia tudo; o mesmo tipo de volta e edicao normal."""
    header = _autenticar_e_criar_empresa(client, "marcenaria")
    cliente_id = _criar_cliente(client, header)
    os_ = _criar_planejados_pelo_servico(db_session, cliente_id)

    r = client.put(f"{URL_OS}/{os_.numero_os}", json={
        "dados_adicionais": {"tipo_trabalho": "planejados"},
        "observacoes": "Cliente pediu puxador preto",
    }, headers=header)

    assert r.status_code == status.HTTP_200_OK, r.text
    assert r.json()["observacoes"] == "Cliente pediu puxador preto"


# =========================
# GUARDIAO: serigrafia como sempre (caso 17)
# =========================

def test_serigrafia_abre_e_troca_de_tipo_como_sempre(client, db_session):
    """Caso 17: sem tipo, com camisa, e trocando camisa -> sacola. Tudo como hoje."""
    header = _autenticar_e_criar_empresa(client, "serigrafia")
    cliente_id = _criar_cliente(client, header)

    # Sem tipo: a serigrafia tem tipos criaveis a mao, entao segue (D5).
    r = client.post(f"{URL_OS}/", json=_corpo_os(cliente_id, "Logo frente", {}), headers=header)
    assert r.status_code == status.HTTP_201_CREATED, r.text

    # Com tipo camisa.
    r = client.post(f"{URL_OS}/", json=_corpo_os(cliente_id, "Logo costas", {"tipo_trabalho": "camisa"}),
                    headers=header)
    assert r.status_code == status.HTTP_201_CREATED, r.text
    numero_os = r.json()["numero_os"]

    # Troca camisa -> sacola: os dois tipos sao criaveis a mao, entao pode.
    r = client.put(f"{URL_OS}/{numero_os}",
                   json={"dados_adicionais": {"tipo_trabalho": "sacola_plastica"}}, headers=header)
    assert r.status_code == status.HTTP_200_OK, r.text
    assert r.json()["dados_adicionais"]["tipo_trabalho"] == "sacola_plastica"
