# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/venda_kg/test_estoque_fracionado_nas_respostas.py
# DESCRIÇÃO: Estoque fracionado (1,5 kg) não pode derrubar nenhuma tela.
#
# O estoque virou Float em f97d3c1 (kg quebrado da serigrafia), mas a busca do
# PDV, a linha da venda, o card de estoque baixo e o relatório de estoque
# seguiram declarando `int` — e o Pydantic recusa 1.5 numa resposta `int`.
# Achado em 07/10/2026: selecionar no PDV um produto com 1,5 kg dava erro 500.
# ---------------------------------------------------------------------------

from datetime import date

import pytest

from app.db.models.contador_venda import ContadorVenda
from app.db.models.estoque import Estoque
from app.db.models.produto import Produto


@pytest.fixture
def sacola(db_session):
    """Produto em KG com 1,5 de estoque, abaixo do mínimo de 2,5."""
    if not db_session.query(ContadorVenda).first():
        db_session.add(ContadorVenda(id=1, proximo_numero=1))
    p = Produto(nome="Sacola Kraft", codigo_produto="SAC-KG", unidade_medida="KG", ativo=True)
    p.estoque = Estoque(quantidade=1.5, quantidade_minima=2.5, quantidade_ideal=10.5,
                        valor_varejo=3000, custo_medio=1000)
    db_session.add(p)
    db_session.commit()
    return p


def test_busca_do_pdv_devolve_o_estoque_quebrado(client, header_com_token, sacola):
    r = client.get("/api/v1/produtos/search", params={"search": "Sacola"}, headers=header_com_token)
    assert r.status_code == 200, r.text
    item = r.json()[0]
    assert item["estoque"] == 1.5
    assert item["quantidade_minima"] == 2.5


def test_linha_da_venda_mostra_o_estoque_quebrado(client, header_com_token, sacola):
    f = client.post("/api/v1/funcionarios/", json={
        "nome": "Vendedor Teste", "cpf": "11122233344", "contato": "11999999999",
        "usuario": {"nome": "vendedor1", "email": "vend1@empresa.com", "senha": "SenhaForte123!"},
        "endereco": [{"logradouro": "Rua X", "numero": "1", "cep": "12345-678",
                      "bairro": "Centro", "cidade": "Lab City", "estado": "SP"}],
    }, headers=header_com_token)
    assert f.status_code in (200, 201), f.text
    v = client.post("/api/v1/vendas/", json={"funcionario_id": f.json()["id"]}, headers=header_com_token)
    assert v.status_code == 201, v.text

    r = client.post(f"/api/v1/vendas/{v.json()['id']}/itens",
                    json={"tipo_produto": "CADASTRADO", "produto_id": sacola.id, "quantidade": 1},
                    headers=header_com_token)
    assert r.status_code in (200, 201), r.text

    venda = client.get(f"/api/v1/vendas/{v.json()['id']}", headers=header_com_token)
    assert venda.status_code == 200, venda.text
    linha = venda.json()["produtos"][0]
    assert linha["estoque_disponivel"] == 1.5


def test_card_de_estoque_baixo(client, header_com_token, sacola):
    r = client.get("/api/v1/dashboard/estoque-baixo", headers=header_com_token)
    assert r.status_code == 200, r.text
    item = next(i for i in r.json()["items"] if i["produto_id"] == sacola.id)
    assert (item["quantidade"], item["quantidade_minima"]) == (1.5, 2.5)


def test_relatorio_de_estoque(client, header_com_token, sacola):
    hoje = date.today().isoformat()
    r = client.get("/api/v1/relatorios/estoque", params={"inicio": hoje, "fim": hoje}, headers=header_com_token)
    assert r.status_code == 200, r.text
    corpo = r.json()
    repor = next(i for i in corpo["abaixo_minimo"] if i["produto_id"] == sacola.id)
    assert (repor["quantidade"], repor["quantidade_minima"], repor["quantidade_ideal"]) == (1.5, 2.5, 10.5)
