# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/venda_kg/test_f1_venda_fracionada.py
# DESCRIÇÃO: Vender 3,5 kg no PDV (docs/venda-fracionada-plano.md, F1).
#
# Critérios Q2, Q3, Q4 e Q7 do plano, e as decisões D1 (fracionado pela
# unidade), D2 (3 casas), D3 (UN recusa com mensagem) e D5 (fardo e
# leve-pague não valem para fracionado; a faixa vale).
# ---------------------------------------------------------------------------

import pytest

from app.db.models.contador_venda import ContadorVenda
from app.db.models.estoque import Estoque
from app.db.models.produto import Produto


@pytest.fixture
def loja(client, db_session, header_com_token) -> dict:
    """Sacola em KG a R$ 30,00/kg com 10 kg; lata em UN para comparar."""
    if not db_session.query(ContadorVenda).first():
        db_session.add(ContadorVenda(id=1, proximo_numero=1))
    sacola = Produto(nome="Sacola Kraft", codigo_produto="SAC-KG", unidade_medida="KG", ativo=True)
    sacola.estoque = Estoque(quantidade=10, valor_varejo=3000, custo_medio=1000)
    lata = Produto(nome="Refrigerante Lata", codigo_produto="REFRI-350", unidade_medida="UN", ativo=True)
    lata.estoque = Estoque(quantidade=100, valor_varejo=450, custo_medio=300)
    db_session.add_all([sacola, lata])
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
    return {"sacola": sacola.id, "lata": lata.id, "funcionario_id": funcionario.json()["id"], "fp_id": fp.json()["id"]}


def _venda(client, headers, loja):
    v = client.post("/api/v1/vendas/", json={"funcionario_id": loja["funcionario_id"]}, headers=headers)
    assert v.status_code == 201, v.text
    return v.json()["id"]


def _lancar(client, headers, venda_id, produto_id, quantidade):
    return client.post(f"/api/v1/vendas/{venda_id}/itens",
                       json={"tipo_produto": "CADASTRADO", "produto_id": produto_id, "quantidade": quantidade},
                       headers=headers)


def _linhas(client, headers, venda_id):
    return client.get(f"/api/v1/vendas/{venda_id}", headers=headers).json()["produtos"]


def _estoque(db_session, produto_id):
    db_session.expire_all()
    return db_session.get(Estoque, produto_id).quantidade


def _finalizar(client, headers, venda_id, loja):
    total = client.get(f"/api/v1/vendas/{venda_id}", headers=headers).json()["total"]
    r = client.post(f"/api/v1/vendas/{venda_id}/finalizar", json={
        "pagamentos": [{"forma_pagamento_id": loja["fp_id"], "valor": total, "parcelado": False, "qtd_parcelas": None}],
    }, headers=headers)
    assert r.status_code == 200, r.text


def test_tres_e_meio_kg_de_ponta_a_ponta(client, db_session, header_com_token, loja):
    """Q2 + Q3: cobra 3,5 × R$ 30, baixa 3,5 e o cancelamento devolve 3,5."""
    v = _venda(client, header_com_token, loja)
    assert _lancar(client, header_com_token, v, loja["sacola"], 3.5).status_code == 201, "lançar 3,5 kg"

    [linha] = _linhas(client, header_com_token, v)
    assert (linha["quantidade"], linha["valor_unitario"], linha["subtotal"]) == (3.5, 3000, 10500)
    assert linha["unidade_medida"] == "KG"

    r = client.patch(f"/api/v1/vendas/{v}/itens/{linha['id']}", json={"quantidade": 2.25}, headers=header_com_token)
    assert r.status_code == 200, r.text
    [linha] = _linhas(client, header_com_token, v)
    assert (linha["quantidade"], linha["subtotal"]) == (2.25, 6750)

    _finalizar(client, header_com_token, v, loja)
    assert _estoque(db_session, loja["sacola"]) == 7.75

    movs = client.get("/api/v1/produtos/movimentacoes", params={"produto_id": loja["sacola"]},
                      headers=header_com_token).json()
    assert [m["quantidade"] for m in movs if m["tipo"] == "SAIDA"] == [2.25]

    r = client.post(f"/api/v1/vendas/{v}/cancelar", json={"motivo": "cliente desistiu da compra"}, headers=header_com_token)
    assert r.status_code == 200, r.text
    assert _estoque(db_session, loja["sacola"]) == 10


def test_centavo_arredonda_meio_para_cima(client, header_com_token, loja, db_session):
    """3,5 kg × R$ 10,01 = R$ 35,035 → R$ 35,04."""
    est = db_session.get(Estoque, loja["sacola"])
    est.valor_varejo = 1001
    db_session.commit()
    v = _venda(client, header_com_token, loja)
    _lancar(client, header_com_token, v, loja["sacola"], 3.5)
    assert _linhas(client, header_com_token, v)[0]["subtotal"] == 3504


def test_tres_casas_decimais(client, header_com_token, loja):
    """D2: 0,1234 kg vira 0,123 kg (e o centavo segue a quantidade arredondada)."""
    v = _venda(client, header_com_token, loja)
    assert _lancar(client, header_com_token, v, loja["sacola"], 0.1234).status_code == 201
    [linha] = _linhas(client, header_com_token, v)
    assert (linha["quantidade"], linha["subtotal"]) == (0.123, 369)


def test_quantidade_zero_ou_negativa_e_recusada(client, header_com_token, loja):
    v = _venda(client, header_com_token, loja)
    for q in (0.0001, -1.5):
        assert _lancar(client, header_com_token, v, loja["sacola"], q).status_code == 422, q


@pytest.mark.parametrize("unidade", ["kg", "G", "L", "ml", "M", "M2", "m³"])
def test_unidades_fracionaveis(client, db_session, header_com_token, loja, unidade):
    """D1: a unidade decide (sem diferenciar maiúscula, e com ² ³)."""
    p = db_session.get(Produto, loja["sacola"])
    p.unidade_medida = unidade
    db_session.commit()
    v = _venda(client, header_com_token, loja)
    assert _lancar(client, header_com_token, v, loja["sacola"], 1.5).status_code == 201, unidade


def test_unidade_inteira_recusa_com_mensagem(client, header_com_token, loja):
    """D3 / Q4."""
    v = _venda(client, header_com_token, loja)
    r = _lancar(client, header_com_token, v, loja["lata"], 1.5)
    assert r.status_code == 400
    assert "Refrigerante Lata é vendido em unidade inteira (UN)" in r.json()["detail"]

    assert _lancar(client, header_com_token, v, loja["lata"], 2).status_code == 201
    linha = _linhas(client, header_com_token, v)[0]
    r = client.patch(f"/api/v1/vendas/{v}/itens/{linha['id']}", json={"quantidade": 2.5}, headers=header_com_token)
    assert r.status_code == 400 and "unidade inteira" in r.json()["detail"]


def test_avulso_continua_inteiro(client, header_com_token, loja):
    v = _venda(client, header_com_token, loja)
    r = client.post(f"/api/v1/vendas/{v}/itens", json={
        "tipo_produto": "AVULSO", "descricao_avulsa": "Corte de tecido", "quantidade": 1.5, "valor_unitario": 1000,
    }, headers=header_com_token)
    assert r.status_code == 400 and "avulso" in r.json()["detail"].lower()


def test_estoque_insuficiente_compara_com_fracao(client, header_com_token, loja):
    """10 kg em estoque: 10,5 kg é recusado (a loja de teste não vende sem estoque)."""
    r = client.put("/api/v1/configuracoes/produtos", json={"permitir_venda_estoque_zerado": False}, headers=header_com_token)
    assert r.status_code == 200, r.text
    v = _venda(client, header_com_token, loja)
    assert _lancar(client, header_com_token, v, loja["sacola"], 10.5).status_code == 400
    assert _lancar(client, header_com_token, v, loja["sacola"], 10).status_code == 201


def test_orcamento_de_tres_e_meio_kg_vira_venda_de_tres_e_meio(client, header_com_token, loja):
    """Q7 / D6."""
    orc = client.post("/api/v1/orcamentos/", json={"funcionario_id": loja["funcionario_id"]}, headers=header_com_token)
    assert orc.status_code == 201, orc.text
    orc_id = orc.json()["id"]
    r = client.post(f"/api/v1/orcamentos/{orc_id}/itens",
                    json={"tipo_produto": "CADASTRADO", "produto_id": loja["sacola"], "quantidade": 3.5},
                    headers=header_com_token)
    assert r.status_code == 201, r.text
    r = client.post(f"/api/v1/orcamentos/{orc_id}/itens",
                    json={"tipo_produto": "CADASTRADO", "produto_id": loja["lata"], "quantidade": 1.5},
                    headers=header_com_token)
    assert r.status_code == 400

    cliente = client.post("/api/v1/clientes/cliente_pf", json={
        "nome": "João Pedro Silva", "cpf": "98765432101", "tipo": "PF", "celular": "11987654321",
        "endereco": [{"logradouro": "Rua das Flores", "numero": "100", "bairro": "Centro",
                      "cidade": "Campinas", "estado": "SP", "cep": "13010-000"}],
    }, headers=header_com_token)
    conv = client.post(f"/api/v1/orcamentos/{orc_id}/converter", json={"cliente_id": cliente.json()["id"]},
                       headers=header_com_token)
    assert conv.status_code in (200, 201), conv.text
    [linha] = _linhas(client, header_com_token, conv.json()["id"])
    assert (linha["quantidade"], linha["subtotal"]) == (3.5, 10500)


# ── Regras de preço (D5) ─────────────────────────────────────────────────────

def _configurar(client, headers, **campos):
    r = client.put("/api/v1/configuracoes/vendas", json=campos, headers=headers)
    assert r.status_code == 200, r.text


def _regras(client, headers, produto_id, regras):
    r = client.put(f"/api/v1/produtos/{produto_id}/regras-preco", json={"regras": regras}, headers=headers)
    assert r.status_code == 200, r.text


def test_faixa_vale_com_fracao(client, header_com_token, loja):
    """'A partir de 6 kg, R$ 25/kg': 6,2 kg entra na faixa."""
    _configurar(client, header_com_token, regra_faixas_quantidade=True)
    _regras(client, header_com_token, loja["sacola"], [{"tipo": "FAIXA", "quantidade": 6, "preco": 2500}])
    v = _venda(client, header_com_token, loja)
    _lancar(client, header_com_token, v, loja["sacola"], 6.2)
    [linha] = _linhas(client, header_com_token, v)
    assert (linha["regra_preco"], linha["valor_unitario"], linha["subtotal"]) == ("R2", 2500, 15500)


def test_leve_pague_nao_vale_para_fracionado(client, header_com_token, loja):
    """Leve 3 kg pague 2 não existe: a regra conta unidades inteiras."""
    _configurar(client, header_com_token, regra_leve_pague=True)
    _regras(client, header_com_token, loja["sacola"], [{"tipo": "LEVE_PAGUE", "quantidade": 3, "pague": 2}])
    v = _venda(client, header_com_token, loja)
    _lancar(client, header_com_token, v, loja["sacola"], 3)
    [linha] = _linhas(client, header_com_token, v)
    assert (linha["regra_preco"], linha["desconto_regra"], linha["subtotal"]) == (None, 0, 9000)
