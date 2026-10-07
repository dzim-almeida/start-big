# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/venda_kg/test_f0_venda_inteira.py
# DESCRIÇÃO: Fotografia da venda INTEIRA (produto em UN) antes da venda
#            fracionada (docs/venda-fracionada-plano.md, F0 e critério Q9).
#
# Escrita em 07/10/2026 com o código ainda inteiro. Depois da F1 tudo aqui tem
# de continuar igual — inclusive o JSON: `3`, não `3.0`. A tela e o cupom
# formatam o que recebem, e "3.0 UN" no cupom é regressão.
# ---------------------------------------------------------------------------

import pytest

from app.db.models.contador_venda import ContadorVenda
from app.db.models.estoque import Estoque
from app.db.models.produto import Produto


@pytest.fixture
def loja(client, db_session, header_com_token) -> dict:
    """Refrigerante em UN, R$ 4,50, 100 em estoque, custo 3,00."""
    if not db_session.query(ContadorVenda).first():
        db_session.add(ContadorVenda(id=1, proximo_numero=1))
    produto = Produto(nome="Refrigerante Lata", codigo_produto="REFRI-350", unidade_medida="UN", ativo=True)
    produto.estoque = Estoque(quantidade=100, valor_varejo=450, custo_medio=300)
    db_session.add(produto)
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
    return {"produto_id": produto.id, "funcionario_id": funcionario.json()["id"], "fp_id": fp.json()["id"]}


def _estoque(db_session, produto_id):
    db_session.expire_all()
    return db_session.get(Estoque, produto_id).quantidade


def _linhas(client, headers, venda_id):
    r = client.get(f"/api/v1/vendas/{venda_id}", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()["produtos"]


def _finalizar(client, headers, venda_id, loja):
    total = client.get(f"/api/v1/vendas/{venda_id}", headers=headers).json()["total"]
    r = client.post(f"/api/v1/vendas/{venda_id}/finalizar", json={
        "pagamentos": [{"forma_pagamento_id": loja["fp_id"], "valor": total, "parcelado": False, "qtd_parcelas": None}],
    }, headers=headers)
    assert r.status_code == 200, r.text


def test_venda_inteira_de_ponta_a_ponta(client, db_session, header_com_token, loja):
    v = client.post("/api/v1/vendas/", json={"funcionario_id": loja["funcionario_id"]}, headers=header_com_token)
    assert v.status_code == 201, v.text
    venda_id = v.json()["id"]

    r = client.post(f"/api/v1/vendas/{venda_id}/itens",
                    json={"tipo_produto": "CADASTRADO", "produto_id": loja["produto_id"], "quantidade": 3},
                    headers=header_com_token)
    assert r.status_code == 201, r.text

    [linha] = _linhas(client, header_com_token, venda_id)
    assert (linha["quantidade"], linha["valor_unitario"], linha["subtotal"]) == (3, 450, 1350)
    assert type(linha["quantidade"]) is int, "o JSON tem de seguir `3`, não `3.0`"

    r = client.patch(f"/api/v1/vendas/{venda_id}/itens/{linha['id']}", json={"quantidade": 5}, headers=header_com_token)
    assert r.status_code == 200, r.text
    [linha] = _linhas(client, header_com_token, venda_id)
    assert (linha["quantidade"], linha["subtotal"]) == (5, 2250)
    assert type(linha["quantidade"]) is int

    venda = client.get(f"/api/v1/vendas/{venda_id}", headers=header_com_token).json()
    assert venda["total"] == 2250

    _finalizar(client, header_com_token, venda_id, loja)
    assert _estoque(db_session, loja["produto_id"]) == 95

    movs = client.get("/api/v1/produtos/movimentacoes", params={"produto_id": loja["produto_id"]},
                      headers=header_com_token).json()
    saidas = [m for m in movs if m["tipo"] == "SAIDA"]
    assert [(m["quantidade"], m["custo_unitario"]) for m in saidas] == [(5, 300)]

    r = client.post(f"/api/v1/vendas/{venda_id}/cancelar", json={"motivo": "cliente desistiu da compra"},
                    headers=header_com_token)
    assert r.status_code == 200, r.text
    assert _estoque(db_session, loja["produto_id"]) == 100


def test_unidade_quebrada_hoje_e_recusada_sem_erro_500(client, header_com_token, loja):
    """Hoje 1,5 em qualquer produto é 422. Depois da F1, UN segue recusando (D3)."""
    v = client.post("/api/v1/vendas/", json={"funcionario_id": loja["funcionario_id"]}, headers=header_com_token)
    r = client.post(f"/api/v1/vendas/{v.json()['id']}/itens",
                    json={"tipo_produto": "CADASTRADO", "produto_id": loja["produto_id"], "quantidade": 1.5},
                    headers=header_com_token)
    assert r.status_code == 422, r.text


def test_orcamento_inteiro_vira_venda_inteira(client, db_session, header_com_token, loja):
    orc = client.post("/api/v1/orcamentos/", json={"funcionario_id": loja["funcionario_id"]}, headers=header_com_token)
    assert orc.status_code == 201, orc.text
    orc_id = orc.json()["id"]
    r = client.post(f"/api/v1/orcamentos/{orc_id}/itens",
                    json={"tipo_produto": "CADASTRADO", "produto_id": loja["produto_id"], "quantidade": 2},
                    headers=header_com_token)
    assert r.status_code == 201, r.text

    cliente = client.post("/api/v1/clientes/cliente_pf", json={
        "nome": "João Pedro Silva", "cpf": "98765432101", "tipo": "PF", "celular": "11987654321",
        "endereco": [{"logradouro": "Rua das Flores", "numero": "100", "bairro": "Centro",
                      "cidade": "Campinas", "estado": "SP", "cep": "13010-000"}],
    }, headers=header_com_token)
    assert cliente.status_code == 201, cliente.text
    conv = client.post(f"/api/v1/orcamentos/{orc_id}/converter", json={"cliente_id": cliente.json()["id"]},
                       headers=header_com_token)
    assert conv.status_code in (200, 201), conv.text

    [linha] = _linhas(client, header_com_token, conv.json()["id"])
    assert (linha["quantidade"], linha["subtotal"]) == (2, 900)
    assert type(linha["quantidade"]) is int
