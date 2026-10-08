# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/embalagens/test_relatorio_regras_preco.py
# DESCRIÇÃO: Relatório "vendas por regra de preço" (plano de embalagens, fase 6).
#
# O que não pode errar: o abatimento junta as duas formas da regra (R1/R3 em
# `desconto_regra`, R2 no preço trocado), venda com duas regras conta UMA vez
# no topo, e só entra venda FINALIZADA.
# ---------------------------------------------------------------------------

from datetime import date, timedelta

from app.db.models.estoque import Estoque
from app.db.models.produto import Produto
from test.api.v1.embalagens.test_regras_preco import (  # noqa: F401 — `adega` e `loja` são fixtures
    FAIXA_6,
    adega,
    cadastrar_regras,
    configurar,
)
from test.api.v1.embalagens.test_venda_por_embalagem import (  # noqa: F401
    finalizar,
    lancar,
    ligar_embalagens,
    loja,
    nova_venda,
)

URL = "/api/v1/relatorios/regras-preco"


def periodo() -> dict:
    # Um dia de folga para cada lado: o relatório filtra em UTC e o teste não
    # pode depender do fuso da máquina.
    return {"inicio": (date.today() - timedelta(days=1)).isoformat(),
            "fim": (date.today() + timedelta(days=1)).isoformat()}


def test_sem_regra_o_relatorio_vem_vazio(client, header_com_token, adega):
    v = nova_venda(client, header_com_token, adega)
    lancar(client, header_com_token, v, adega["produto_id"], 17)
    finalizar(client, header_com_token, v, adega)

    r = client.get(URL, params=periodo(), headers=header_com_token)
    assert r.status_code == 200, r.text
    corpo = r.json()
    assert (corpo["qtd_vendas"], corpo["faturamento"], corpo["abatimento"]) == (0, 0, 0)
    assert corpo["por_regra"] == [] and corpo["por_produto"] == []


def test_r1_e_r2_somam_o_abatimento_e_a_venda_conta_uma_vez(client, db_session, header_com_token, adega):
    ligar_embalagens(client, header_com_token)
    configurar(client, header_com_token, regra_embalagem_avulsas=True, regra_faixas_quantidade=True)

    # Água a R$ 2,00; a partir de 6 un, R$ 1,50 (R2).
    agua = Produto(nome="Água 500ml", codigo_produto="AGUA-500", unidade_medida="UN", ativo=True)
    agua.estoque = Estoque(quantidade=100, valor_varejo=200, custo_medio=80)
    db_session.add(agua)
    db_session.commit()
    cadastrar_regras(client, header_com_token, agua.id, [{**FAIXA_6, "preco": 150}])

    # Venda 1: 17 cervejas (R1: −17,50) + 6 águas (R2: 6 × 0,50 = −3,00).
    v1 = nova_venda(client, header_com_token, adega)
    lancar(client, header_com_token, v1, adega["produto_id"], 17)
    lancar(client, header_com_token, v1, agua.id, 6)
    finalizar(client, header_com_token, v1, adega)

    # Venda 2: 15 cervejas = 1 fardo (R1: 67,50 − 50,00 = −17,50).
    v2 = nova_venda(client, header_com_token, adega)
    lancar(client, header_com_token, v2, adega["produto_id"], 15)
    finalizar(client, header_com_token, v2, adega)

    # Venda 3: 2 águas, abaixo da faixa — sem regra, não entra.
    v3 = nova_venda(client, header_com_token, adega)
    lancar(client, header_com_token, v3, agua.id, 2)
    finalizar(client, header_com_token, v3, adega)

    # Venda 4: aberta, com regra — não finalizada, não entra.
    v4 = nova_venda(client, header_com_token, adega)
    lancar(client, header_com_token, v4, adega["produto_id"], 15)

    corpo = client.get(URL, params=periodo(), headers=header_com_token).json()

    assert corpo["qtd_vendas"] == 2  # a venda 1 tem duas regras e conta uma vez
    assert corpo["abatimento"] == 1750 + 300 + 1750
    assert corpo["faturamento"] == 5900 + 900 + 5000

    por_regra = {r["regra"]: r for r in corpo["por_regra"]}
    assert set(por_regra) == {"R1", "R2"}
    r1, r2 = por_regra["R1"], por_regra["R2"]
    assert (r1["qtd_vendas"], r1["unidades"], r1["faturamento"], r1["abatimento"]) == (2, 32, 10900, 3500)
    assert (r2["qtd_vendas"], r2["unidades"], r2["faturamento"], r2["abatimento"]) == (1, 6, 900, 300)

    # Por produto: maior abatimento primeiro.
    assert [(p["regra"], p["nome"]) for p in corpo["por_produto"]] == [
        ("R1", "Cerveja Lata 350ml"), ("R2", "Água 500ml"),
    ]

    # Fora do período, nada.
    antes = {"inicio": "2020-01-01", "fim": "2020-01-31"}
    assert client.get(URL, params=antes, headers=header_com_token).json()["qtd_vendas"] == 0
