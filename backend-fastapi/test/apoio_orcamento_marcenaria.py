# ---------------------------------------------------------------------------
# ARQUIVO: test/apoio_orcamento_marcenaria.py
# DESCRICAO: Fixtures e ajudantes dos testes do orcamento de marcenaria
#            (Spec 06A). Usados pelos conftest de test/services/marcenaria e
#            test/api/v1/marcenaria (`from test.apoio_orcamento_marcenaria import *`).
#
# `client` SEM `with`: com `with`, o lifespan roda create_all() e as migracoes
# no banco REAL da maquina. O banco destes testes e o SQLite em memoria do
# conftest raiz (fixture `db_session`).
# ---------------------------------------------------------------------------

from typing import Any, Optional

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.depends import get_current_active_user
from app.db.models.empresa import Empresa
from app.db.models.estoque import Estoque
from app.db.models.fornecedor import Fornecedor
from app.db.models.funcionario import Funcionario
from app.db.models.produto import Produto
from app.db.models.usuario import Usuario
from app.main import app

URL = "/api/v1/marcenaria/orcamentos"

EMAIL_MASTER = "teste.funcionario@example.com"
SENHA_MASTER = "senhaSegura456"


@pytest.fixture(scope="module")
def client():
    yield TestClient(app)


def _criar_loja(client: TestClient, segmento: str) -> dict:
    """Master + login + empresa do segmento. Devolve o header com o token."""
    client.post("/api/v1/usuarios/", json={"nome": "Admin Master", "email": EMAIL_MASTER, "senha": SENHA_MASTER})
    login = client.post("/api/v1/auth/login", data={
        "username": EMAIL_MASTER, "password": SENHA_MASTER, "hwid": "test-terminal-hwid",
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
def loja(client, db_session) -> dict:
    """Loja de MARCENARIA; devolve o header do master."""
    return _criar_loja(client, "marcenaria")


@pytest.fixture
def mudar_segmento(db_session: Session):
    """Troca o segmento da empresa (para provar o 404 fora da marcenaria)."""
    def _mudar(segmento: str):
        empresa = db_session.query(Empresa).first()
        empresa.segmento = segmento
        db_session.commit()
    return _mudar


@pytest.fixture
def token_master(db_session: Session, loja) -> dict:
    """O token do master como o servico recebe (para chamar o servico direto)."""
    usuario = db_session.query(Usuario).filter_by(email=EMAIL_MASTER).first()
    funcionario = db_session.query(Funcionario).filter_by(usuario_id=usuario.id).first()
    return {
        "sub": str(usuario.id), "nome": "Admin Master", "empresa_id": 1, "is_master": True,
        "permissoes": {}, "funcionario_id": funcionario.id if funcionario else None,
    }


@pytest.fixture
def como():
    """Troca o usuario logado por um funcionario (nao master) com as permissoes dadas.

    Ex.: como(manage_orcamentos_marcenaria=True). Devolve o token usado.
    """
    def _como(funcionario_id: Optional[int] = None, **permissoes):
        token = {"sub": "99", "nome": "Vendedor Teste", "empresa_id": 1, "cargo": "Vendedor",
                 "is_master": False, "permissoes": permissoes, "funcionario_id": funcionario_id}
        app.dependency_overrides[get_current_active_user] = lambda: token
        return token
    yield _como
    app.dependency_overrides.pop(get_current_active_user, None)    # volta ao login de verdade


@pytest.fixture
def produto(db_session: Session):
    """Cria um produto com estoque. Devolve o id.

    valor_entrada = ultimo preco de compra; custo_medio = reserva (O3a).
    """
    def _produto(nome: str, valor_entrada: Optional[int] = None, custo_medio: Optional[int] = None,
                 sofre_perda: bool = True, codigo: Optional[str] = None, unidade: str = "UN") -> int:
        # Produto ativo exige codigo (constraint do banco): sem um, gera "P-<n>".
        codigo = codigo or f"P-{db_session.query(Produto).count() + 1}"
        p = Produto(nome=nome, codigo_produto=codigo, unidade_medida=unidade, ativo=True, sofre_perda=sofre_perda)
        p.estoque = Estoque(quantidade=10, valor_varejo=0, valor_entrada=valor_entrada, custo_medio=custo_medio)
        db_session.add(p)
        db_session.commit()
        return p.id
    return _produto


@pytest.fixture
def fornecedor(db_session: Session):
    """Cria um fornecedor (arquiteto ou central parceira). Devolve o id."""
    def _fornecedor(nome: str, ativo: bool = True) -> int:
        f = Fornecedor(nome=nome, ativo=ativo)
        db_session.add(f)
        db_session.commit()
        return f.id
    return _fornecedor


@pytest.fixture
def cliente_id(client, loja) -> int:
    """Cliente PF com endereco e celular."""
    r = client.post("/api/v1/clientes/cliente_pf", json={
        "nome": "Dona Marta", "cpf": "52998224725", "tipo": "PF", "celular": "11987654321",
        "email": "marta@example.com",
        "endereco": [{"logradouro": "Rua das Flores", "numero": "100", "bairro": "Centro",
                      "cidade": "Campinas", "estado": "SP", "cep": "13010000"}],
    }, headers=loja)
    assert r.status_code == 201, r.text
    return r.json()["id"]


class Api:
    """Atalho para chamar a API do orcamento com o header do master.

    `rev` vira `?revisao=` (toda escrita manda a revisao, D20).
    """

    def __init__(self, client: TestClient, header: dict):
        self.client = client
        self.header = header

    def req(self, metodo: str, caminho: str = "", rev: Optional[int] = None, **kwargs) -> Any:
        params = dict(kwargs.pop("params", {}) or {})
        if rev is not None:
            params["revisao"] = rev
        # `params or None`: sem parametros, a query escrita no caminho ("?x=1") fica como esta.
        return self.client.request(metodo, f"{URL}{caminho}", headers=self.header, params=params or None, **kwargs)

    def criar(self, **corpo) -> dict:
        r = self.req("POST", "/", json=corpo)
        assert r.status_code == 201, r.text
        return r.json()

    def detalhe(self, orcamento_id: int) -> dict:
        r = self.req("GET", f"/{orcamento_id}")
        assert r.status_code == 200, r.text
        return r.json()

    def ok(self, metodo: str, caminho: str, rev: Optional[int] = None, esperado: int = 200, **kwargs) -> dict:
        """Chama e confere o status; devolve o JSON."""
        r = self.req(metodo, caminho, rev=rev, **kwargs)
        assert r.status_code == esperado, r.text
        return r.json() if r.content else {}


@pytest.fixture
def api(client, loja) -> Api:
    return Api(client, loja)


# ---------------------------------------------------------------------------
# Cenario B da Spec 05 (§11.1/§11.2): RT 8% sai da margem, desconto 5%.
# Markup 90%, perda 10%, custo/hora R$ 45,00, instalacao R$ 750,00, sinal 40%.
# ---------------------------------------------------------------------------

def montar_cenario_b(api: Api, produto, fornecedor, cliente: Optional[int] = None,
                     arquitetos: Optional[list[dict]] = None) -> dict:
    """Monta pela API o orcamento do cenario B e devolve o detalhe."""
    orc = api.criar(cliente_id=cliente, projeto_nome="Residencial Alpha Ville - Apto 802")
    oid = orc["id"]
    d = api.ok("PATCH", f"/{oid}", rev=orc["revisao"], json={
        "markup_bp": 9000, "perda_bp": 1000, "custo_hora_centavos": 4500,
        "instalacao_custo_centavos": 75000,
        "desconto": {"modo": "PERCENTUAL", "valor": 500},
        "sinal": {"modo": "PERCENTUAL", "valor": 4000},
    })
    if arquitetos is None:
        arquitetos = [{"fornecedor_id": fornecedor("Studio Renascer"), "rt_bp": 800}]
    d = api.ok("PUT", f"/{oid}/rt", rev=d["revisao"], json={"arquitetos": arquitetos})
    d = api.ok("POST", f"/{oid}/ambientes", rev=d["revisao"], esperado=201, json={"nome": "Cozinha Gourmet"})
    amb = d["ambientes"][0]["id"]

    mdf_branco = produto("MDF Branco TX 18mm", valor_entrada=28000, sofre_perda=True)
    mdf_freijo = produto("MDF Freijó 18mm", valor_entrada=38000, sofre_perda=True)
    fita = produto("Fita PVC", valor_entrada=350, sofre_perda=True, unidade="M")
    corredica = produto("Corrediça Tandem", valor_entrada=19500, sofre_perda=False, unidade="PAR")
    gola = produto("Perfil gola", valor_entrada=8750, sofre_perda=False)
    central = fornecedor("Madeiranit")

    d = api.ok("POST", f"/{oid}/ambientes/{amb}/moveis", rev=d["revisao"], esperado=201, json={
        "nome": "Torre Quente", "quantidade": 1,
        "tipo_producao": "TERCEIRIZADA", "central_fornecedor_id": central, "terceirizado_centavos": 38000,
        "mao_obra": {"modo": "FIXA", "centavos": 30000, "horas_centesimos": 0},
        "insumos": [
            {"produto_id": mdf_branco, "quantidade_milesimos": 1400},
            {"produto_id": mdf_freijo, "quantidade_milesimos": 900},
            {"produto_id": fita, "quantidade_milesimos": 26000},
            {"produto_id": corredica, "quantidade_milesimos": 2000},
            {"produto_id": gola, "quantidade_milesimos": 2800},
        ],
    })
    d = api.ok("POST", f"/{oid}/ambientes/{amb}/moveis", rev=d["revisao"], esperado=201, json={
        "nome": "Balcão", "quantidade": 2,
        "mao_obra": {"modo": "HORAS", "centavos": 0, "horas_centesimos": 400},
        "insumos": [
            {"produto_id": mdf_branco, "quantidade_milesimos": 1000},
            {"produto_id": corredica, "quantidade_milesimos": 3000},
        ],
    })
    return d


# ---------------------------------------------------------------------------
# Aprovacao (Spec 08A)
# ---------------------------------------------------------------------------

@pytest.fixture
def forma_pagamento(client, loja):
    """Cria uma forma de pagamento (a seed do startup nao roda nos testes)."""
    def _forma(nome: str = "PIX") -> int:
        r = client.post("/api/v1/formas-pagamento/", json={"nome": nome, "ativo": True}, headers=loja)
        assert r.status_code == 201, r.text
        return r.json()["id"]
    return _forma


def ids_dos_moveis(d: dict) -> list[int]:
    """Todos os moveis do detalhe, na ordem da tela."""
    return [m["id"] for amb in d["ambientes"] for m in amb["moveis"]]


def aprovar(api: Api, d: dict, movel_ids: Optional[list[int]] = None, esperado: int = 200, **extra) -> Any:
    """POST /aprovar com todos os moveis (ou os dados). Devolve o JSON (ou a resposta, se esperado != 200)."""
    corpo = {"movel_ids": movel_ids if movel_ids is not None else ids_dos_moveis(d), **extra}
    r = api.req("POST", f"/{d['id']}/aprovar", rev=d["revisao"], json=corpo)
    if esperado != 200:
        assert r.status_code == esperado, r.text
        return r
    assert r.status_code == 200, r.text
    return r.json()


def os_da_api(api: Api, numero_os: str) -> dict:
    """A OS como a tela de OS le (GET /ordens-servico/{numero})."""
    r = api.client.get(f"/api/v1/ordens-servico/{numero_os}", headers=api.header)
    assert r.status_code == 200, r.text
    return r.json()


# ---------------------------------------------------------------------------
# Separacao de material (Spec 10A)
# ---------------------------------------------------------------------------

URL_MARCENARIA = "/api/v1/marcenaria"


class Separacao:
    """Atalho para a API da separacao de uma OS (Spec 10A), com o header do master."""

    def __init__(self, client: TestClient, header: dict):
        self.client = client
        self.header = header

    def req(self, metodo: str, numero_os: str, caminho: str = "", **kwargs) -> Any:
        return self.client.request(metodo, f"{URL_MARCENARIA}/os/{numero_os}/separacao{caminho}",
                                   headers=self.header, **kwargs)

    def ler(self, numero_os: str) -> dict:
        r = self.req("GET", numero_os)
        assert r.status_code == 200, r.text
        return r.json()

    def linha(self, numero_os: str, descricao: str) -> dict:
        """A linha cuja descricao comeca com o texto dado (ex.: "MDF")."""
        return next(linha for linha in self.ler(numero_os)["linhas"] if linha["descricao"].startswith(descricao))

    def acao(self, numero_os: str, linha: dict, acao: str, quantidade: Optional[int] = None,
             esperado: int = 200, separada: Optional[int] = None) -> Any:
        """POST retirar/devolver/concluir/reabrir com a trava da linha (D16).

        `separada` troca a `separada_esperada_milesimos` (para provar o 409).
        Devolve o JSON (ou a resposta, se esperado != 200).
        """
        corpo: dict[str, Any] = {
            "separada_esperada_milesimos": linha["separada_milesimos"] if separada is None else separada,
        }
        if quantidade is not None:
            corpo["quantidade_milesimos"] = quantidade
        r = self.req("POST", numero_os, f"/{linha['item_id']}/{acao}", json=corpo)
        assert r.status_code == esperado, r.text
        return r.json() if esperado == 200 else r


@pytest.fixture
def separacao(client, loja) -> Separacao:
    return Separacao(client, loja)


def aprovar_simples(api: Api, cliente_id: int, moveis: list[list[dict]]) -> tuple[dict, str]:
    """Orcamento de UM ambiente com os moveis dados (cada um, a lista de insumos),
    todos internos e de quantidade 1, aprovado inteiro. Devolve (detalhe, numero da OS).
    """
    orc = api.criar(cliente_id=cliente_id, projeto_nome="Projeto da separação")
    d = api.ok("POST", f"/{orc['id']}/ambientes", rev=orc["revisao"], esperado=201, json={"nome": "Cozinha"})
    amb = d["ambientes"][0]["id"]
    for numero, insumos in enumerate(moveis, start=1):
        d = api.ok("POST", f"/{orc['id']}/ambientes/{amb}/moveis", rev=d["revisao"], esperado=201, json={
            "nome": f"Móvel {numero}", "quantidade": 1,
            "mao_obra": {"modo": "FIXA", "centavos": 10000, "horas_centesimos": 0},
            "insumos": insumos,
        })
    d = aprovar(api, d)
    return d, d["os"]["numero_os"]
