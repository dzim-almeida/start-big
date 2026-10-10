# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/embalagens/test_venda_atacado.py
# DESCRIÇÃO: Venda no preço de atacado (chave do PDV + pedido mínimo).
#
# O que não pode regredir: com a chave DESLIGADA (o padrão) a venda sai
# exatamente como antes, mesmo com preço de atacado cadastrado.
# ---------------------------------------------------------------------------

from fastapi.testclient import TestClient

from app.db.models.estoque import Estoque
from test.api.v1.embalagens.test_regras_preco import FAIXA_6, cadastrar_regras, configurar, ler_venda
from test.api.v1.embalagens.test_venda_por_embalagem import (  # noqa: F401 — `loja` é fixture
    lancar,
    linhas,
    loja,
    nova_venda,
)

# Cerveja da `loja`: varejo R$ 4,50. Atacado aqui: R$ 4,00.
ATACADO = 400


def com_atacado(db_session, produto_id, preco=ATACADO):
    db_session.get(Estoque, produto_id).valor_atacado = preco
    db_session.commit()


def modo(client: TestClient, headers, venda_id, ligado: bool):
    return client.patch(f"/api/v1/vendas/{venda_id}", json={"modo_atacado": ligado}, headers=headers)


def pagar(client, headers, venda_id, loja):
    total = ler_venda(client, headers, venda_id)["total"]
    return client.post(f"/api/v1/vendas/{venda_id}/finalizar", json={
        "pagamentos": [{"forma_pagamento_id": loja["fp_id"], "valor": total, "parcelado": False, "qtd_parcelas": None}],
    }, headers=headers)


def test_chave_da_loja_desligada_recusa_o_atacado(client, db_session, header_com_token, loja):
    com_atacado(db_session, loja["produto_id"])
    v = nova_venda(client, header_com_token, loja)
    lancar(client, header_com_token, v, loja["produto_id"], 10)

    r = modo(client, header_com_token, v, True)
    assert r.status_code == 400 and "desligada" in r.text
    [linha] = linhas(client, header_com_token, v)
    assert (linha["valor_unitario"], linha["regra_preco"]) == (450, None)


def test_liga_desliga_troca_o_preco_e_volta_ao_varejo(client, db_session, header_com_token, loja):
    com_atacado(db_session, loja["produto_id"])
    configurar(client, header_com_token, atacado_habilitado=True)
    v = nova_venda(client, header_com_token, loja)
    lancar(client, header_com_token, v, loja["produto_id"], 10)

    r = modo(client, header_com_token, v, True)
    assert r.status_code == 200, r.text
    assert r.json()["modo_atacado"] is True
    [linha] = linhas(client, header_com_token, v)
    assert (linha["valor_unitario"], linha["valor_unitario_tabela"], linha["subtotal"]) == (400, 450, 4000)
    assert (linha["regra_preco"], linha["regra_descricao"]) == ("ATACADO", "Preço de atacado")
    assert ler_venda(client, header_com_token, v)["total"] == 4000

    # Item lançado depois de ligar já entra no atacado.
    lancar(client, header_com_token, v, loja["produto_id"], 2)
    assert all(l["valor_unitario"] == 400 for l in linhas(client, header_com_token, v))

    assert modo(client, header_com_token, v, False).status_code == 200
    assert all(
        (l["valor_unitario"], l["regra_preco"], l["valor_unitario_tabela"]) == (450, None, None)
        for l in linhas(client, header_com_token, v)
    )
    assert ler_venda(client, header_com_token, v)["total"] == 12 * 450


def test_produto_sem_preco_de_atacado_fica_no_varejo(client, db_session, header_com_token, loja):
    com_atacado(db_session, loja["produto_id"], None)
    configurar(client, header_com_token, atacado_habilitado=True)
    v = nova_venda(client, header_com_token, loja)
    lancar(client, header_com_token, v, loja["produto_id"], 3)

    assert modo(client, header_com_token, v, True).status_code == 200
    [linha] = linhas(client, header_com_token, v)
    assert (linha["valor_unitario"], linha["regra_preco"]) == (450, None)


def test_pedido_minimo_bloqueia_finalizar_ate_completar(client, db_session, header_com_token, loja):
    com_atacado(db_session, loja["produto_id"])
    configurar(client, header_com_token, atacado_habilitado=True, atacado_pedido_minimo=5000)
    v = nova_venda(client, header_com_token, loja)
    lancar(client, header_com_token, v, loja["produto_id"], 10)  # 10 × 4,00 = 40,00
    modo(client, header_com_token, v, True)

    r = pagar(client, header_com_token, v, loja)
    assert r.status_code == 400
    assert "R$ 50,00" in r.text and "faltam R$ 10,00" in r.text

    lancar(client, header_com_token, v, loja["produto_id"], 3)  # 13 × 4,00 = 52,00
    assert pagar(client, header_com_token, v, loja).status_code == 200


def test_pedido_minimo_nao_vale_no_varejo(client, db_session, header_com_token, loja):
    com_atacado(db_session, loja["produto_id"])
    configurar(client, header_com_token, atacado_habilitado=True, atacado_pedido_minimo=99999)
    v = nova_venda(client, header_com_token, loja)
    lancar(client, header_com_token, v, loja["produto_id"], 1)
    assert pagar(client, header_com_token, v, loja).status_code == 200


def test_atacado_tira_a_faixa_e_desligar_devolve_a_faixa(client, db_session, header_com_token, loja):
    com_atacado(db_session, loja["produto_id"])
    cadastrar_regras(client, header_com_token, loja["produto_id"], [FAIXA_6])  # 6+ un: R$ 3,80
    configurar(client, header_com_token, atacado_habilitado=True, regra_faixas_quantidade=True)
    v = nova_venda(client, header_com_token, loja)
    lancar(client, header_com_token, v, loja["produto_id"], 10)
    assert linhas(client, header_com_token, v)[0]["regra_preco"] == "R2"

    modo(client, header_com_token, v, True)
    [linha] = linhas(client, header_com_token, v)
    assert (linha["valor_unitario"], linha["valor_unitario_tabela"], linha["regra_preco"]) == (400, 450, "ATACADO")

    modo(client, header_com_token, v, False)
    [linha] = linhas(client, header_com_token, v)
    assert (linha["valor_unitario"], linha["valor_unitario_tabela"], linha["regra_preco"]) == (380, 450, "R2")
