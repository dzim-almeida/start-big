# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/venda_kg/test_venda_avulso_valor_alto.py
# DESCRICAO: Item avulso de valor alto no PDV (R$ 190.000,00), do lancamento a
#            finalizacao, e a alteracao do item avulso depois de lancado.
# ---------------------------------------------------------------------------

import pytest

from app.db.models.contador_venda import ContadorVenda
from app.db.models.estoque import Estoque
from app.db.models.produto import Produto

CENTO_E_NOVENTA_MIL = 19_000_000


@pytest.fixture
def loja(client, db_session, header_com_token) -> dict:
    if not db_session.query(ContadorVenda).first():
        db_session.add(ContadorVenda(id=1, proximo_numero=1))
        db_session.commit()
    funcionario = client.post("/api/v1/funcionarios/", json={
        "nome": "Vendedor Teste", "cpf": "11122233344", "contato": "11999999999",
        "usuario": {"nome": "vendedor1", "email": "vend1@empresa.com", "senha": "SenhaForte123!"},
        "endereco": [{"logradouro": "Rua X", "numero": "1", "cep": "12345-678",
                      "bairro": "Centro", "cidade": "Lab City", "estado": "SP"}],
    }, headers=header_com_token)
    assert funcionario.status_code in (200, 201), funcionario.text
    fp = client.post("/api/v1/formas-pagamento/", json={"nome": "Dinheiro", "ativo": True}, headers=header_com_token)
    assert fp.status_code == 201, fp.text
    return {"funcionario_id": funcionario.json()["id"], "fp_id": fp.json()["id"]}


def _venda(client, headers, loja) -> int:
    r = client.post("/api/v1/vendas/", json={"funcionario_id": loja["funcionario_id"]}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _lancar(client, headers, venda_id, valor):
    return client.post(f"/api/v1/vendas/{venda_id}/itens", json={
        "tipo_produto": "AVULSO", "descricao_avulsa": "Movel sob medida", "quantidade": 1, "valor_unitario": valor,
    }, headers=headers)


def test_lanca_e_finaliza_avulso_de_190_mil(client, header_com_token, loja):
    v = _venda(client, header_com_token, loja)
    assert _lancar(client, header_com_token, v, CENTO_E_NOVENTA_MIL).status_code == 201

    venda = client.get(f"/api/v1/vendas/{v}", headers=header_com_token).json()
    assert venda["total"] == CENTO_E_NOVENTA_MIL

    r = client.post(f"/api/v1/vendas/{v}/finalizar", json={"pagamentos": [
        {"forma_pagamento_id": loja["fp_id"], "valor": CENTO_E_NOVENTA_MIL, "parcelado": False, "qtd_parcelas": None},
    ]}, headers=header_com_token)
    assert r.status_code == 200, r.text


@pytest.mark.parametrize("alteracao", [
    {"valor_unitario": CENTO_E_NOVENTA_MIL},
    {"quantidade": 2},
    {"desconto": 100},
])
def test_altera_item_avulso_depois_de_lancado(client, header_com_token, loja, alteracao):
    v = _venda(client, header_com_token, loja)
    lancado = _lancar(client, header_com_token, v, 10_000)
    assert lancado.status_code == 201, lancado.text
    item_id = client.get(f"/api/v1/vendas/{v}", headers=header_com_token).json()["produtos"][0]["id"]

    r = client.patch(f"/api/v1/vendas/{v}/itens/{item_id}", json=alteracao, headers=header_com_token)

    assert r.status_code == 200, r.text
    item = client.get(f"/api/v1/vendas/{v}", headers=header_com_token).json()["produtos"][0]
    for campo, valor in alteracao.items():
        assert item[campo] == valor


def test_item_cadastrado_continua_barrado_sem_estoque(client, db_session, header_com_token, loja):
    produto = Produto(nome="Lata", codigo_produto="L1", unidade_medida="UN", ativo=True)
    produto.estoque = Estoque(quantidade=1, valor_varejo=450, custo_medio=300)
    db_session.add(produto)
    db_session.commit()
    v = _venda(client, header_com_token, loja)
    lancado = client.post(f"/api/v1/vendas/{v}/itens", json={
        "tipo_produto": "CADASTRADO", "produto_id": produto.id, "quantidade": 1,
    }, headers=header_com_token)
    assert lancado.status_code == 201, lancado.text
    item_id = client.get(f"/api/v1/vendas/{v}", headers=header_com_token).json()["produtos"][0]["id"]

    r = client.patch(f"/api/v1/vendas/{v}/itens/{item_id}", json={"quantidade": 5}, headers=header_com_token)

    assert r.status_code == 400
    assert "estoque insuficiente" in r.json()["detail"]
