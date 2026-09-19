# ---------------------------------------------------------------------------
# ARQUIVO: test/services/fiscal/test_tax_engine_icms_st.py
# DESCRIÇÃO: TASK008 — ICMS-ST: a calculadora pura (cenários 1–3 da spec) e
#            o ramo do contribuinte no pipeline do engine. Sem banco.
# ---------------------------------------------------------------------------

from decimal import Decimal

import pytest

from app.services.fiscal.tax_engine.calculators.icms_st import calcular_icms_st
from app.services.fiscal.tax_engine.engine import calcular_impostos
from app.services.fiscal.tax_engine.exceptions import CSTNaoSuportadoError
from app.services.fiscal.tax_engine.types import ItemEntrada

from .conftest import d, item, nota


# --- Calculadora ---------------------------------------------------------------

def test_cenario_1_st_sem_reducao():
    r = calcular_icms_st(d("1000"), d("12"), d("18"), mva=d("40"))
    assert r.base_calculo_st == d("1400.00")
    assert r.valor_icms_proprio == d("120.00")
    assert r.valor_icms_st == d("132.00")
    assert (r.mva, r.aliquota_interna_destino, r.aliquota_interestadual) == (d("40"), d("18"), d("12"))
    assert r.reducao_base_st is None


def test_cenario_2_st_com_reducao_de_base():
    r = calcular_icms_st(d("1000"), d("12"), d("18"), mva=d("40"), reducao_base_st=d("20"))
    assert r.base_calculo_st == d("1120.00") and r.valor_icms_st == d("81.60")
    assert r.reducao_base_st == d("20")


def test_icms_proprio_informado_e_o_deduzido():
    r = calcular_icms_st(d("1000"), d("12"), d("18"), mva=d("40"), icms_proprio_informado=d("60.00"))
    assert r.valor_icms_proprio == d("60.00") and r.valor_icms_st == d("192.00")


def test_st_nunca_negativa():
    assert calcular_icms_st(d("1000"), d("18"), d("12"), mva=d("0")).valor_icms_st == d("0.00")


def test_reducao_zero_ou_none_nao_reduz():
    a = calcular_icms_st(d("1000"), d("12"), d("18"), mva=d("40"), reducao_base_st=d("0"))
    b = calcular_icms_st(d("1000"), d("12"), d("18"), mva=d("40"), reducao_base_st=None)
    assert a.base_calculo_st == b.base_calculo_st == d("1400.00")


# --- Engine --------------------------------------------------------------------

def _item_st(**kw) -> ItemEntrada:
    campos = dict(
        valor_bruto="1000.00", cst_icms="10", aliquota_icms=d("12"), cfop="6404",
        st_aliquota_interestadual=d("12"), st_aliquota_interna_destino=d("18"), st_mva=d("40"),
    )
    campos.update(kw)
    return item(**campos)


def test_ramo_st_no_pipeline_cenario_1():
    resultado = calcular_impostos([_item_st()], nota())
    i = resultado.itens[0]
    assert i.icms_situacao_tributaria == "10" and i.icms_valor == d("120.00")
    assert i.icms_st_modalidade_base_calculo == 4
    assert (i.icms_st_base_calculo, i.icms_st_aliquota, i.icms_st_mva) == (d("1400.00"), d("18"), d("40"))
    assert i.icms_st_valor == d("132.00") and i.icms_st_reducao_base is None
    assert i.difal_valor is None
    assert resultado.totais.base_calculo_icms_st == d("1400.00") and resultado.totais.valor_icms_st == d("132.00")
    assert resultado.totais.valor_total_nota == d("1132.00")   # ST entra no vNF


def test_cst_70_com_reducao_da_propria_cenario_2():
    """A redução da ST (20%) vem da regra; a do ICMS próprio (CST 70) vem do produto e é outra."""
    resultado = calcular_impostos(
        [_item_st(cst_icms="70", reducao_base_icms=d("50"), st_reducao_base=d("20"))], nota(),
    )
    i = resultado.itens[0]
    assert i.icms_situacao_tributaria == "70"
    assert i.icms_base_calculo == d("500.00") and i.icms_valor == d("60.00")   # própria reduzida
    assert i.icms_st_base_calculo == d("1120.00") and i.icms_st_reducao_base == d("20")
    assert i.icms_st_valor == d("141.60")                                       # 201,60 − 60,00 (o próprio REAL)


def test_cenario_3_contribuinte_sem_st_nao_soma_nada_no_vnf():
    resultado = calcular_impostos([item(valor_bruto="1000.00", cst_icms="00", aliquota_icms=d("12"), cfop="6102")], nota())
    i = resultado.itens[0]
    assert i.icms_valor == d("120.00") and i.icms_st_valor is None and i.icms_st_base_calculo is None
    assert resultado.totais.valor_icms_st == d("0") and resultado.totais.valor_total_nota == d("1000.00")


def test_difal_continua_fora_do_vnf_e_st_dentro():
    itens = [
        _item_st(numero_item=1),
        item(numero_item=2, valor_bruto="500.00", aliquota_icms=d("12"),
             difal_aliquota_interestadual=d("12"), difal_aliquota_interna_destino=d("18")),
    ]
    t = calcular_impostos(itens, nota()).totais
    assert t.valor_icms_st == d("132.00") and t.valor_difal == d("30.00")
    assert t.valor_total_nota == d("1632.00")


def test_frete_rateado_entra_na_base_da_st():
    i = calcular_impostos([_item_st()], nota(frete="100")).itens[0]
    assert i.icms_st_base_calculo == d("1540.00")


def test_cst_10_sem_regra_de_st_e_recusado():
    with pytest.raises(CSTNaoSuportadoError, match="ST"):
        calcular_impostos([item(cst_icms="10", aliquota_icms=d("12"))], nota())


def test_csosn_202_no_simples_deduz_o_icms_pela_interestadual():
    """Remetente do Simples não destaca ICMS próprio, mas deduz o valor pela interestadual (Conv. 142/2018)."""
    resultado = calcular_impostos(
        [_item_st(cst_icms=None, csosn="202", aliquota_icms=d("0"))], nota(simples_nacional=True),
    )
    i = resultado.itens[0]
    assert i.icms_situacao_tributaria == "202" and i.icms_valor == d("0")
    assert i.icms_st_valor == d("132.00")     # 252 − 120 (1000 × 12%)
    assert resultado.totais.valor_total_nota == d("1132.00")


def test_csosn_201_sem_st_e_recusado():
    with pytest.raises(CSTNaoSuportadoError):
        calcular_impostos([item(cst_icms=None, csosn="201", aliquota_icms=d("12"))], nota(simples_nacional=True))


def test_cfop_do_item_chega_ao_resultado():
    resultado = calcular_impostos([_item_st(), item(numero_item=2, cfop="5102")], nota())
    assert [i.cfop for i in resultado.itens] == ["6404", "5102"]


def test_cst_10_com_mva_zero_e_recusado():
    """MVA 0 não gera ST (engine ignora ≤ 0): CST 10 sairia sem grupo ST."""
    with pytest.raises(CSTNaoSuportadoError, match="ST"):
        calcular_impostos([_item_st(st_mva=d("0"))], nota())
