# ---------------------------------------------------------------------------
# ARQUIVO: test/services/test_os_item_origem.py
# DESCRICAO: ⚠️ Prova de nao regressao da OS (Spec 08A da marcenaria, §8 e
#            casos 14, 15, 28 e 29), num segmento que JA ESTA EM PRODUCAO
#            (informatica).
#
#            A coluna `ordem_servico_itens.origem` e generica: nula em todo
#            item comum, que continua se editando e removendo como sempre. So
#            o item COM origem e travado -- e ninguem consegue criar um pela API.
# ---------------------------------------------------------------------------

import pytest
from fastapi.testclient import TestClient

from app.db.models.ordem_servico_item import OrdemServicoItem
from app.main import app

from test.apoio_orcamento_marcenaria import _criar_loja

OS_URL = "/api/v1/ordens-servico"


@pytest.fixture
def client():
    """SEM `with`: o lifespan nao roda (nada no banco real da maquina)."""
    yield TestClient(app)


@pytest.fixture
def informatica(client, db_session) -> dict:
    return _criar_loja(client, "assistencia_tecnica")


@pytest.fixture
def os_informatica(client, informatica) -> str:
    """Uma OS de informatica com um item, criada pelo POST de sempre."""
    cliente = client.post("/api/v1/clientes/cliente_pf", json={
        "nome": "Seu Jorge", "cpf": "11144477735", "tipo": "PF",
    }, headers=informatica).json()["id"]
    r = client.post(f"{OS_URL}/", json={
        "cliente_id": cliente, "prioridade": "NORMAL", "defeito_relatado": "Tela quebrada", "dados_adicionais": {},
        "objeto": {"marca": "Apple", "modelo": "iPhone 11", "numero_serie": "ABC12345"},
        "itens": [{"tipo": "SERVICO", "nome": "Troca de tela", "unidade_medida": "UN", "quantidade": 1,
                   "valor_unitario": 35000}],
    }, headers=informatica)
    assert r.status_code == 201, r.text
    return r.json()["numero_os"]


def test_28_get_da_os_traz_origem_nula(client, informatica, os_informatica):
    os_ = client.get(f"{OS_URL}/{os_informatica}", headers=informatica).json()

    assert [i["origem"] for i in os_["itens"]] == [None]
    assert (os_["valor_bruto"], os_["valor_total"]) == (35000, 35000)


def test_29_origem_no_corpo_e_ignorada_e_o_item_continua_livre(client, informatica, os_informatica):
    r = client.post(f"{OS_URL}/{os_informatica}/itens", json={
        "tipo": "SERVICO", "nome": "Película", "unidade_medida": "UN", "quantidade": 1, "valor_unitario": 3000,
        "origem": "ORCAMENTO_MARCENARIA",
    }, headers=informatica)
    assert r.status_code in (200, 201), r.text
    pelicula = next(i for i in r.json()["itens"] if i["nome"] == "Película")
    assert pelicula["origem"] is None

    r = client.put(f"{OS_URL}/{os_informatica}/itens/{pelicula['id']}", json={"valor_unitario": 4000}, headers=informatica)
    assert r.status_code == 200, r.text
    assert client.delete(f"{OS_URL}/{os_informatica}/itens/{pelicula['id']}", headers=informatica).status_code == 204


def test_14_trava_e_generica_vale_em_qualquer_segmento(client, informatica, os_informatica, db_session):
    """O servico da OS nao sabe o que e marcenaria: item com origem trava em qualquer OS."""
    item = db_session.query(OrdemServicoItem).first()
    item.origem = "QUALQUER_DOCUMENTO"
    db_session.commit()

    r = client.put(f"{OS_URL}/{os_informatica}/itens/{item.id}", json={"quantidade": 2}, headers=informatica)
    assert r.status_code == 409
    assert r.json()["detail"].startswith("Este item veio do orçamento.")
    assert client.delete(f"{OS_URL}/{os_informatica}/itens/{item.id}", headers=informatica).status_code == 409
