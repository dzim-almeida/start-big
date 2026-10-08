# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/test_relatorio_contador.py
# DESCRIÇÃO: Receita para o contador — segregação do PGDAS-D.
#
# O que não pode errar: o total bate com o faturamento bruto; o grupo vem do
# CSOSN/CST do cadastro; produto sem classificação NÃO vira "normal"; o
# desconto da OS é rateado pelos itens.
# ---------------------------------------------------------------------------

from datetime import date, timedelta

from app.core.segregacao_receita import Grupo, classificar, ratear
from app.db.models.empresa import Empresa
from app.db.models.estoque import Estoque
from app.db.models.produto import Produto
from app.db.models.produto_fiscal import ProdutoFiscal
from test.api.v1.embalagens.conftest import header_com_token  # noqa: F401 — fixture
from test.api.v1.embalagens.test_venda_por_embalagem import (  # noqa: F401 — `loja` é fixture
    finalizar,
    lancar,
    loja,
    nova_venda,
)
from test.api.v1.test_ordem_servico_oficina import (
    _autenticar_e_criar_empresa,
    _criar_cliente,
    _criar_forma_pagamento,
    _criar_produto,
    _item,
    _item_produto,
    _os_payload,
)

URL = "/api/v1/relatorios/contador"


def periodo() -> dict:
    return {"inicio": (date.today() - timedelta(days=1)).isoformat(),
            "fim": (date.today() + timedelta(days=1)).isoformat()}


def simples(db_session):
    for empresa in db_session.query(Empresa).all():
        empresa.crt = 1
    db_session.commit()


def fiscal(db_session, produto_id, csosn=None, cst_icms=None, cst_pis=None):
    db_session.add(ProdutoFiscal(produto_id=produto_id, ncm="22030000", csosn=csosn, cst_icms=cst_icms,
                                 cst_pis=cst_pis, cst_cofins=cst_pis))
    db_session.commit()


def grupo(corpo, icms_st, monofasico) -> int:
    [g] = [g for g in corpo["mercadoria"] if (g["icms_st"], g["monofasico"]) == (icms_st, monofasico)]
    return g["valor"]


# ── Conta pura ───────────────────────────────────────────────────────────────

def test_classificar_le_o_campo_do_regime():
    assert classificar(1, "500", None, "04", "04") == Grupo(icms_st=True, monofasico=True)
    assert classificar(1, "102", "60", "49", "49") == Grupo(icms_st=False, monofasico=False)  # CST sobrou
    assert classificar(3, "500", "00", "01", "01") == Grupo(icms_st=False, monofasico=False)
    assert classificar(3, None, "60", None, "04") == Grupo(icms_st=True, monofasico=True)
    assert classificar(1, None, "60", None, None) is None  # Simples sem CSOSN: não chuta
    assert classificar(None, " ", None, None, None) is None


def test_ratear_soma_exato():
    assert ratear(10800, [10000, 2000]) == [9000, 1800]
    assert sum(ratear(1000, [1, 1, 1])) == 1000
    assert ratear(500, [0, 0]) == [0, 0]


# ── Vendas ───────────────────────────────────────────────────────────────────

def test_vendas_separadas_por_grupo_e_sem_classificacao(client, db_session, header_com_token, loja):
    simples(db_session)
    fiscal(db_session, loja["produto_id"], csosn="500", cst_pis="04")  # cerveja: ST + monofásico
    biscoito = Produto(nome="Biscoito", codigo_produto="BISC", unidade_medida="UN", ativo=True)
    biscoito.estoque = Estoque(quantidade=10, valor_varejo=500)
    sem_fiscal = Produto(nome="Sem Ficha", codigo_produto="SEMF", unidade_medida="UN", ativo=True)
    sem_fiscal.estoque = Estoque(quantidade=10, valor_varejo=300)
    db_session.add_all([biscoito, sem_fiscal])
    db_session.commit()
    fiscal(db_session, biscoito.id, csosn="102", cst_pis="49")

    v = nova_venda(client, header_com_token, loja)
    lancar(client, header_com_token, v, loja["produto_id"], 2)  # 900
    lancar(client, header_com_token, v, biscoito.id, 1)  # 500
    lancar(client, header_com_token, v, sem_fiscal.id, 1)  # 300
    r = client.post(f"/api/v1/vendas/{v}/itens", json={
        "tipo_produto": "AVULSO", "descricao_avulsa": "Gelo", "valor_unitario": 700, "quantidade": 1,
    }, headers=header_com_token)
    assert r.status_code == 201, r.text
    finalizar(client, header_com_token, v, loja)

    r = client.get(URL, params=periodo(), headers=header_com_token)
    assert r.status_code == 200, r.text
    corpo = r.json()
    assert corpo["crt"] == 1
    assert grupo(corpo, True, True) == 900
    assert grupo(corpo, False, False) == 500
    assert grupo(corpo, True, False) == grupo(corpo, False, True) == 0
    assert corpo["mercadoria_sem_classificacao"] == 1000
    assert {(p["nome"], p["valor"], p["motivo"]) for p in corpo["produtos_sem_classificacao"]} == {
        ("Gelo", 700, "Item avulso (sem cadastro)"),
        ("Sem Ficha", 300, "Sem CSOSN no cadastro fiscal"),
    }
    assert corpo["receita_total"] == corpo["faturamento_vendas"] == 2400


# ── OS ───────────────────────────────────────────────────────────────────────

def test_os_rateia_o_desconto_e_separa_servico_e_juros(client, db_session):
    header = _autenticar_e_criar_empresa(client, "assistencia_tecnica")
    simples(db_session)
    cliente_id = _criar_cliente(client, header)
    fp_id = _criar_forma_pagamento(client, header)
    peca = _criar_produto(client, header, "PECA-ST", 10, valor=2000)
    fiscal(db_session, peca, csosn="500", cst_pis="49")

    itens = [_item("Mão de obra", 10000), _item_produto(peca, "Peça", 2000)]
    r = client.post("/api/v1/ordens-servico/", json=_os_payload(cliente_id, "SERIAL-CONT", itens=itens), headers=header)
    assert r.status_code == 201, r.text
    numero = r.json()["numero_os"]
    # 12.000 − 1.200 de desconto + 300 de juros = 11.100
    fin = {
        "situacao_equipamento": "REPARADO", "garantia": "90 dias", "desconto": 1200, "acrescimo": 300,
        "pagamentos": [{"forma_pagamento_id": fp_id, "valor": 11100}],
    }
    rf = client.put(f"/api/v1/ordens-servico/{numero}/finalizar", json=fin, headers=header)
    assert rf.status_code == 200, rf.text

    corpo = client.get(URL, params=periodo(), headers=header).json()
    assert corpo["servicos"] == 9000  # 10.000 × 10.800 / 12.000
    assert grupo(corpo, True, False) == 1800
    assert corpo["frete_e_juros"] == 300
    assert corpo["receita_total"] == corpo["faturamento_os"] == 11100
    assert corpo["produtos_sem_classificacao"] == []
