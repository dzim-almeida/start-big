# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/test_configuracao_marcenaria.py
# DESCRICAO: Spec 04A da marcenaria -- GET/PUT /configuracoes/marcenaria
#            (casos 09 a 20).
#
#            O que nao pode errar:
#              - quem nao ve custo recebe so a parte sem custo (as chaves de
#                custo nem aparecem);
#              - so quem tem `manage_custos_marcenaria` altera;
#              - fora da marcenaria a rota nao existe (404).
# ---------------------------------------------------------------------------

import pytest
from fastapi.testclient import TestClient

from app.core.depends import get_current_active_user
from app.db.models.configuracao_marcenaria import ConfiguracaoMarcenaria
from app.main import app

TEST_USER_EMAIL = "teste.funcionario@example.com"
TEST_USER_PASSWORD = "senhaSegura456"

URL = "/api/v1/configuracoes/marcenaria"

# Os campos de custo, que so quem tem view_custos_marcenaria ve (D9).
# `rt_vencimento_dias` entrou na Spec 09A (prazo da conta do RT), no bloco de custos.
CAMPOS_DE_CUSTO = {"markup_padrao_bp", "perda_padrao_bp", "custo_hora_centavos", "rt_padrao_bp", "rt_modo",
                   "rt_vencimento_dias"}

# Os padroes da §4.1 da Spec 04A.
PADROES = {
    "rt_vencimento_dias": 30,          # Spec 09A: padrao aprovado em C5e
    "markup_padrao_bp": 9000,
    "perda_padrao_bp": 1000,
    "custo_hora_centavos": 0,
    "rt_padrao_bp": 0,
    "rt_modo": "MARGEM",
    "validade_dias": 15,
    "prazo_entrega_dias": 30,
    "etapas_producao": ["Corte", "Borda", "Furação", "Montagem", "Embalagem"],
    "checklist_vistoria": [
        "Alinhamento de portas e gavetas",
        "Acabamento de bordas e vedação com silicone",
        "Funcionamento de corrediças, dobradiças e pistões",
        "Fixação e nivelamento dos móveis",
        "Limpeza final do ambiente",
    ],
    "inclui_custos": True,
}


@pytest.fixture
def client():
    """Cliente HTTP SEM `with`: o lifespan (create_all e migracoes no banco real
    da maquina) nao roda. O banco destes testes e o SQLite em memoria do conftest."""
    yield TestClient(app)


@pytest.fixture
def como():
    """Troca o usuario logado por um funcionario (nao master) com as permissoes dadas."""
    def _como(**permissoes):
        token = {"sub": "99", "nome": "Vendedor", "empresa_id": 1, "cargo": "Vendedor",
                 "is_master": False, "permissoes": permissoes}
        app.dependency_overrides[get_current_active_user] = lambda: token
    yield _como
    app.dependency_overrides.pop(get_current_active_user, None)   # volta ao login de verdade


def _empresa(client, segmento: str) -> dict:
    """Cria o master, faz login e cria a empresa com o segmento. Devolve o header."""
    client.post("/api/v1/usuarios/", json={"nome": "Admin Master", "email": TEST_USER_EMAIL, "senha": TEST_USER_PASSWORD})
    login = client.post("/api/v1/auth/login", data={
        "username": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD, "hwid": "test-terminal-hwid",
    })
    assert login.status_code == 200, login.text
    header = {"Authorization": f"Bearer {login.json()['access_token']}"}
    r = client.post("/api/v1/empresas/", json={
        "razao_social": "Marcenaria Teste LTDA", "nome_fantasia": "Teste", "is_cnpj": True,
        "documento": "12345678000199", "regime_tributario": "Simples Nacional",
        "celular": "11999998888", "segmento": segmento,
        "endereco": [{"logradouro": "Av. Paulista", "numero": "1000", "bairro": "Bela Vista",
                      "cidade": "São Paulo", "estado": "SP", "cep": "01310-100"}],
    }, headers=header)
    assert r.status_code == 201, r.text
    return header


@pytest.fixture
def marcenaria(client, db_session) -> dict:
    """Empresa de marcenaria; devolve o header do master."""
    return _empresa(client, "marcenaria")


# =========================
# GET: recorte por permissao (casos 09, 10, 11 e 20)
# =========================

def test_master_recebe_os_padroes_completos(client, marcenaria):
    """Caso 09: primeira leitura cria a configuracao com os padroes da §4.1."""
    r = client.get(URL, headers=marcenaria)
    assert r.status_code == 200, r.text
    assert r.json() == PADROES


def test_cargo_sem_permissao_recebe_so_o_que_nao_e_custo(client, marcenaria, como):
    """Caso 10: as chaves de custo nem aparecem (nao vem null, para a tela nao
    confundir "sem permissao" com "zerado")."""
    como()                                                     # vendedor sem nenhuma caixa
    r = client.get(URL)
    assert r.status_code == 200, r.text
    corpo = r.json()
    assert not (CAMPOS_DE_CUSTO & set(corpo))
    assert corpo == {
        "validade_dias": 15,
        "prazo_entrega_dias": 30,
        "etapas_producao": PADROES["etapas_producao"],
        "checklist_vistoria": PADROES["checklist_vistoria"],
        "inclui_custos": False,
    }


@pytest.mark.parametrize("permissao", ["view_custos_marcenaria", "manage_custos_marcenaria", "all"])
def test_quem_ve_custo_recebe_tudo(client, marcenaria, como, permissao):
    """Caso 11: ver custo (e quem gere tambem ve, D8; 'all' passa em tudo, D11)."""
    como(**{permissao: True})
    r = client.get(URL)
    assert r.status_code == 200, r.text
    assert r.json() == PADROES


def test_duas_leituras_criam_uma_linha_so(client, marcenaria, db_session):
    """Caso 20: get-or-create, nao create-sempre."""
    client.get(URL, headers=marcenaria)
    client.get(URL, headers=marcenaria)
    db_session.expire_all()
    assert db_session.query(ConfiguracaoMarcenaria).count() == 1


# =========================
# PUT: permissao e validacao (casos 12 a 18)
# =========================

def test_quem_so_ve_nao_altera(client, marcenaria, como):
    """Caso 12: mudar o markup padrao muda o preco de todo orcamento novo (D10)."""
    como(view_custos_marcenaria=True)
    r = client.put(URL, json={"markup_padrao_bp": 8000})
    assert r.status_code == 403, r.text
    assert "manage_custos_marcenaria" in r.json()["detail"]


def test_quem_gere_altera_so_o_que_enviou(client, marcenaria, como):
    """Caso 13: PUT parcial."""
    como(manage_custos_marcenaria=True)
    r = client.put(URL, json={"markup_padrao_bp": 8000})
    assert r.status_code == 200, r.text
    assert r.json() == {**PADROES, "markup_padrao_bp": 8000}


def test_markup_fora_do_limite_e_recusado_em_portugues(client, marcenaria):
    """Caso 14."""
    r = client.put(URL, json={"markup_padrao_bp": 100_001}, headers=marcenaria)
    assert r.status_code == 422, r.text
    assert r.json()["detail"][0]["message"] == "O markup deve ficar entre 0% e 1000%."


@pytest.mark.parametrize(
    "etapas, mensagem",
    [
        ([], "Etapas de produção: informe de 1 a 20 itens."),
        ([" "], "Etapas de produção: há um item vazio."),
        (["Corte", "corte"], "Etapas de produção: há itens repetidos."),
        (["x" * 61], "Etapas de produção: cada item pode ter até 60 caracteres."),
    ],
    ids=["vazia", "item_vazio", "repetido", "longo"],
)
def test_lista_de_etapas_invalida(client, marcenaria, etapas, mensagem):
    """Caso 15."""
    r = client.put(URL, json={"etapas_producao": etapas}, headers=marcenaria)
    assert r.status_code == 422, r.text
    assert r.json()["detail"][0]["message"] == mensagem


def test_espacos_das_etapas_sao_removidos(client, marcenaria):
    """Caso 16."""
    r = client.put(URL, json={"etapas_producao": ["  Corte  ", "Borda"]}, headers=marcenaria)
    assert r.status_code == 200, r.text
    assert r.json()["etapas_producao"] == ["Corte", "Borda"]


def test_modo_de_rt_desconhecido_e_recusado(client, marcenaria):
    """Caso 17."""
    r = client.put(URL, json={"rt_modo": "OUTRO"}, headers=marcenaria)
    assert r.status_code == 422, r.text


def test_campo_desconhecido_e_recusado(client, marcenaria):
    """Caso 18: um erro de digitacao no frontend nao some em silencio."""
    r = client.put(URL, json={"campo_inventado": 1}, headers=marcenaria)
    assert r.status_code == 422, r.text


# =========================
# Fora da marcenaria (caso 19)
# =========================

def test_fora_da_marcenaria_a_rota_nao_existe(client, db_session):
    """Caso 19: serigrafia (segmento sem orcamento_tecnico), mesmo como master."""
    header = _empresa(client, "serigrafia")
    assert client.get(URL, headers=header).status_code == 404
    r = client.put(URL, json={"markup_padrao_bp": 8000}, headers=header)
    assert r.status_code == 404
    assert r.json()["detail"] == "Parâmetros de marcenaria não disponíveis para este segmento."
