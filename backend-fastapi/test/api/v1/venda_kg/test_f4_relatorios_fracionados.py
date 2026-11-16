# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/venda_kg/test_f4_relatorios_fracionados.py
# DESCRIÇÃO: Venda de 3,5 kg não derruba relatório nem financeiro (F4, Q8).
#
# 3,5 kg × custo R$ 10,01 = 3503,5 centavos. As somas de custo passaram a
# ROUND no banco; antes, `int` na resposta recusava o centavo quebrado e a tela
# caía com erro 500 — o mesmo defeito que derrubou a busca do PDV em 07/10.
# ---------------------------------------------------------------------------

from datetime import date

import pytest

from app.db.models.contador_venda import ContadorVenda
from app.db.models.estoque import Estoque
from app.db.models.produto import Produto

HOJE = date.today().isoformat()


@pytest.fixture
def venda_finalizada(client, db_session, header_com_token) -> dict:
    if not db_session.query(ContadorVenda).first():
        db_session.add(ContadorVenda(id=1, proximo_numero=1))
    sacola = Produto(nome="Sacola Kraft", codigo_produto="SAC-KG", unidade_medida="KG", ativo=True)
    sacola.estoque = Estoque(quantidade=10, valor_varejo=3001, custo_medio=1001)
    db_session.add(sacola)
    db_session.commit()

    f = client.post("/api/v1/funcionarios/", json={
        "nome": "Vendedor Teste", "cpf": "11122233344", "contato": "11999999999",
        "usuario": {"nome": "vendedor1", "email": "vend1@empresa.com", "senha": "SenhaForte123!"},
        "endereco": [{"logradouro": "Rua X", "numero": "1", "cep": "12345-678",
                      "bairro": "Centro", "cidade": "Lab City", "estado": "SP"}],
    }, headers=header_com_token)
    fp = client.post("/api/v1/formas-pagamento/", json={"nome": "Dinheiro", "ativo": True}, headers=header_com_token)
    v = client.post("/api/v1/vendas/", json={"funcionario_id": f.json()["id"]}, headers=header_com_token).json()["id"]
    r = client.post(f"/api/v1/vendas/{v}/itens",
                    json={"tipo_produto": "CADASTRADO", "produto_id": sacola.id, "quantidade": 3.5},
                    headers=header_com_token)
    assert r.status_code == 201, r.text
    total = client.get(f"/api/v1/vendas/{v}", headers=header_com_token).json()["total"]
    assert total == 10504
    r = client.post(f"/api/v1/vendas/{v}/finalizar", json={
        "pagamentos": [{"forma_pagamento_id": fp.json()["id"], "valor": total, "parcelado": False, "qtd_parcelas": None}],
    }, headers=header_com_token)
    assert r.status_code == 200, r.text
    return {"venda_id": v, "funcionario_id": f.json()["id"], "produto_id": sacola.id}


@pytest.mark.parametrize("rota", [
    "/api/v1/relatorios/faturamento",
    "/api/v1/relatorios/ranking-funcionarios",
    "/api/v1/relatorios/comissoes",
    "/api/v1/relatorios/estoque",
    "/api/v1/relatorios/regras-preco",
    "/api/v1/relatorios/contador",
    "/api/v1/financeiro/resumo",
    "/api/v1/financeiro/custo-detalhe",
])
def test_relatorio_responde_com_venda_fracionada(client, header_com_token, venda_finalizada, rota):
    r = client.get(rota, params={"inicio": HOJE, "fim": HOJE}, headers=header_com_token)
    assert r.status_code == 200, f"{rota}: {r.status_code} {r.text[:300]}"


def test_extrato_do_funcionario(client, header_com_token, venda_finalizada):
    r = client.get("/api/v1/relatorios/extrato-funcionario",
                   params={"funcionario_id": venda_finalizada["funcionario_id"], "inicio": HOJE, "fim": HOJE},
                   headers=header_com_token)
    assert r.status_code == 200, r.text


def test_curva_abc_soma_tres_e_meio(client, header_com_token, venda_finalizada):
    r = client.get("/api/v1/relatorios/estoque", params={"inicio": HOJE, "fim": HOJE}, headers=header_com_token)
    assert r.status_code == 200, r.text
    linha = next(i for i in r.json()["curva_abc"] if i["produto_id"] == venda_finalizada["produto_id"])
    assert linha["quantidade"] == 3.5


def test_cancelar_devolve_tres_e_meio(client, db_session, header_com_token, venda_finalizada):
    r = client.post(f"/api/v1/vendas/{venda_finalizada['venda_id']}/cancelar",
                    json={"motivo": "cliente desistiu da compra"}, headers=header_com_token)
    assert r.status_code == 200, r.text
    db_session.expire_all()
    assert db_session.get(Estoque, venda_finalizada["produto_id"]).quantidade == 10
