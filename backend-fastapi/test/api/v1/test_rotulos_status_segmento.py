# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/test_rotulos_status_segmento.py
# DESCRICAO: Spec 01A -- rotulos de STATUS da OS por segmento (casos 09 a 13).
#
#            O que estes testes provam:
#              1. a marcenaria recebe os rotulos novos no contrato
#                 /definicao-campos e no widget "OS por status" do dashboard;
#              2. oficina, informatica, serigrafia e PDV continuam EXATAMENTE
#                 como antes (PR1: nada em producao muda);
#              3. o `status` gravado e devolvido continua o codigo do enum --
#                 so o texto (`status_label`) muda.
# ---------------------------------------------------------------------------

import pytest
from fastapi.encoders import jsonable_encoder  # converte o dict do registry como a API converte
from fastapi.testclient import TestClient
from starlette import status

from app.core.segmentos import DEFINICOES  # a declaracao que a API deve devolver
from app.main import app
from app.schemas.ordem_servico import OrdemServicoCreate
from app.services import ordem_servico as os_service

TEST_USER_EMAIL = "teste.funcionario@example.com"
TEST_USER_PASSWORD = "senhaSegura456"

URL_DEFINICAO = "/api/v1/ordens-servico/definicao-campos"  # contrato de campos do segmento
URL_OS_POR_STATUS = "/api/v1/dashboard/os-por-status"      # widget do dashboard


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
    Devolve o header Authorization (mesmo setup de test_ordem_servico_oficina)."""
    # Usuario master: o primeiro usuario criado tem todas as permissoes.
    client.post("/api/v1/usuarios/", json={
        "nome": "Admin Master",
        "email": TEST_USER_EMAIL,
        "senha": TEST_USER_PASSWORD,
    })

    # Login com o hwid de terminal que o conftest usa.
    login = client.post("/api/v1/auth/login", data={
        "username": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
        "hwid": "test-terminal-hwid",
    })
    assert login.status_code == 200, login.text
    header = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # A empresa e quem diz o segmento da instalacao.
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
        "nome": "João Pedro Silva",
        "cpf": "98765432101",
        "tipo": "PF",
        "celular": "11987654321",
        "endereco": [{
            "logradouro": "Rua das Flores", "numero": "100", "bairro": "Centro",
            "cidade": "Campinas", "estado": "SP", "cep": "13010-000",
        }],
    }, headers=header)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _por_no_status(client, header: dict, numero_os: str, status_os: str) -> None:
    """Coloca a OS no status pedido pelo mesmo caminho da tela
    (PUT /ordens-servico/{numero} com o campo `status`)."""
    # Toda OS nasce ABERTA; so muda quando o status pedido e outro.
    if status_os != "ABERTA":
        r = client.put(f"/api/v1/ordens-servico/{numero_os}", json={"status": status_os}, headers=header)
        assert r.status_code == status.HTTP_200_OK, r.text
        assert r.json()["status"] == status_os


def _abrir_os_no_status(client, header: dict, cliente_id: int, objeto: dict, status_os: str) -> str:
    """Abre uma OS pela rota comum e a coloca no status pedido. Devolve o numero."""
    r = client.post("/api/v1/ordens-servico/", json={
        "cliente_id": cliente_id,
        "prioridade": "NORMAL",
        "defeito_relatado": "Teste de rotulo de status",
        "dados_adicionais": {},
        "objeto": objeto,
        "itens": [],
    }, headers=header)
    assert r.status_code == status.HTTP_201_CREATED, r.text
    numero_os = r.json()["numero_os"]
    _por_no_status(client, header, numero_os, status_os)
    return numero_os


def _abrir_planejados_no_status(client, db_session, header: dict, cliente_id: int,
                                nome: str, status_os: str) -> str:
    """Marcenaria: a OS de Planejados so nasce da aprovacao de um orcamento
    (Spec 03A), entao e aberta pelo SERVICO com `origem_orcamento=True`, como a
    Spec 08A vai fazer. Depois o status muda pela rota comum."""
    dados = OrdemServicoCreate(
        cliente_id=cliente_id,
        prioridade="NORMAL",
        defeito_relatado="Teste de rotulo de status",
        dados_adicionais={"tipo_trabalho": "planejados"},
        objeto={"modelo": nome, "dados_adicionais": {}},  # o codigo PRJ e gerado
        itens=[],
    )
    os_ = os_service.create_ordem_servico(db_session, dados, origem_orcamento=True)
    db_session.commit()  # o endpoint faria o commit; aqui o teste faz
    _por_no_status(client, header, os_.numero_os, status_os)
    return os_.numero_os


def _rotulos_do_dashboard(client, header: dict) -> dict:
    """Le o widget "OS por status" e devolve {status: status_label}."""
    r = client.get(URL_OS_POR_STATUS, headers=header)
    assert r.status_code == 200, r.text
    return {item["status"]: item["status_label"] for item in r.json()["items"]}


# =========================
# Contrato /definicao-campos (casos 09 e 10)
# =========================

@pytest.mark.parametrize("segmento", ["oficina_mecanica", "assistencia_tecnica", "serigrafia", "pdv"])
def test_definicao_campos_de_quem_nao_renomeia_fica_igual(client, db_session, segmento):
    """Caso 09: segmento sem rotulo proprio nao ganha a chave, e o resto da
    definicao e a mesma declaracao do registry -- nada mudou para ele."""
    header = _autenticar_e_criar_empresa(client, segmento)

    r = client.get(URL_DEFINICAO, headers=header)

    assert r.status_code == 200, r.text
    definicao = r.json()["definicao"]
    assert "rotulos_status" not in definicao
    # A resposta e o registry inteiro, convertido para JSON do mesmo jeito.
    assert definicao == jsonable_encoder(DEFINICOES[segmento])


def test_definicao_campos_da_marcenaria_traz_os_rotulos_de_status(client, db_session):
    """Caso 10: o frontend (Spec 01B) le os rotulos daqui, sem endpoint novo."""
    header = _autenticar_e_criar_empresa(client, "marcenaria")

    r = client.get(URL_DEFINICAO, headers=header)

    assert r.status_code == 200, r.text
    assert r.json()["definicao"]["rotulos_status"] == {
        "EM_ANDAMENTO": {"rotulo": "Em Produção", "curto": "Em produção"},
        "AGUARDANDO_PECAS": {"rotulo": "Aguardando Material", "curto": "Aguard. material"},
        "AGUARDANDO_RETIRADA": {"rotulo": "Aguardando Entrega", "curto": "Aguard. entrega"},
    }


# =========================
# Dashboard "OS por status" (casos 11 a 13)
# =========================

def test_dashboard_da_informatica_continua_com_o_texto_de_hoje(client, db_session):
    """Caso 11 (GUARDIAO): a informatica esta em producao e nao pediu nada."""
    header = _autenticar_e_criar_empresa(client, "assistencia_tecnica")
    cliente_id = _criar_cliente(client, header)
    # Objeto de informatica: marca, modelo e numero de serie do aparelho.
    aparelho = {"marca": "Samsung", "modelo": "A10", "numero_serie": "SERIAL-01A-001"}
    _abrir_os_no_status(client, header, cliente_id, aparelho, "AGUARDANDO_RETIRADA")

    rotulos = _rotulos_do_dashboard(client, header)

    assert rotulos == {"AGUARDANDO_RETIRADA": "Aguard. retirada"}


def test_dashboard_da_marcenaria_usa_o_rotulo_curto_do_segmento(client, db_session):
    """Caso 12: os tres status renomeados usam o texto curto da marcenaria;
    ABERTA, que ela nao renomeou, continua com o texto padrao."""
    header = _autenticar_e_criar_empresa(client, "marcenaria")
    cliente_id = _criar_cliente(client, header)
    # Uma OS em cada status; o codigo do projeto (PRJ-...) e gerado pelo sistema.
    for status_os in ("AGUARDANDO_RETIRADA", "EM_ANDAMENTO", "AGUARDANDO_PECAS", "ABERTA"):
        _abrir_planejados_no_status(client, db_session, header, cliente_id, f"Cozinha {status_os}", status_os)

    rotulos = _rotulos_do_dashboard(client, header)

    assert rotulos == {
        "AGUARDANDO_RETIRADA": "Aguard. entrega",
        "EM_ANDAMENTO": "Em produção",
        "AGUARDANDO_PECAS": "Aguard. material",
        "ABERTA": "Aberta",  # padrao: a marcenaria nao renomeia este
    }


def test_dashboard_da_marcenaria_devolve_o_codigo_do_enum_no_status(client, db_session):
    """Caso 13: so o TEXTO muda. O campo `status` continua o codigo gravado,
    que e o que filtros e links da tela usam."""
    header = _autenticar_e_criar_empresa(client, "marcenaria")
    cliente_id = _criar_cliente(client, header)
    _abrir_planejados_no_status(client, db_session, header, cliente_id, "Closet casal", "AGUARDANDO_RETIRADA")

    r = client.get(URL_OS_POR_STATUS, headers=header)

    assert r.status_code == 200, r.text
    item = r.json()["items"][0]                    # so ha uma OS, logo um item
    assert item["status"] == "AGUARDANDO_RETIRADA"  # codigo do enum, nunca o texto
    assert item["status_label"] == "Aguard. entrega"
    assert item["count"] == 1
