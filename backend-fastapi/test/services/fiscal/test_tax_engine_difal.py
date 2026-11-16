# ---------------------------------------------------------------------------
# ARQUIVO: test/services/fiscal/test_tax_engine_difal.py
# DESCRIÇÃO: TASK007 — DIFAL/FCP: a calculadora pura (cenários A–E da spec)
#            e o passo novo do pipeline do engine. Sem banco.
# ---------------------------------------------------------------------------

from dataclasses import is_dataclass
from decimal import Decimal

import pytest

from app.services.fiscal.tax_engine.calculators.difal import ResultadoDIFAL, calcular_difal
from app.services.fiscal.tax_engine.engine import calcular_impostos
from app.services.fiscal.tax_engine.types import ItemEntrada

from .conftest import d, item, nota


# --- Calculadora ---------------------------------------------------------------

def test_cenario_a_base_simples_sem_fcp():
    r = calcular_difal(d("1000"), d("7"), d("18"))
    assert (r.icms_interestadual_valor, r.valor_difal, r.fcp_valor) == (d("70.00"), d("110.00"), d("0.00"))
    assert r.base_calculo == d("1000.00") and r.fcp_base_calculo == d("1000.00")


def test_cenario_b_base_simples_com_fcp():
    r = calcular_difal(d("500"), d("7"), d("20"), percentual_fcp=d("2"))
    assert (r.icms_interestadual_valor, r.valor_difal, r.fcp_valor) == (d("35.00"), d("65.00"), d("10.00"))
    assert r.fcp_aliquota == d("2")


def test_cenario_c_base_dupla_com_fcp():
    r = calcular_difal(d("1000"), d("12"), d("20.5"), percentual_fcp=d("2"), base_dupla=True)
    assert r.base_calculo == d("1257.86")
    assert r.icms_interestadual_valor == d("120.00")
    assert r.valor_difal == d("137.86")
    assert r.fcp_base_calculo == d("1257.86") and r.fcp_valor == d("25.16")


def test_cenario_d_interestadual_igual_a_interna_zera_o_difal():
    r = calcular_difal(d("1000"), d("12"), d("12"))
    assert r.icms_interestadual_valor == d("120.00") and r.valor_difal == d("0.00")


def test_difal_nunca_negativo():
    assert calcular_difal(d("1000"), d("12"), d("7")).valor_difal == d("0.00")


def test_aliquota_interna_de_cem_por_cento_em_base_dupla_e_recusada():
    with pytest.raises(ValueError, match="100%"):
        calcular_difal(d("1000"), d("12"), d("100"), base_dupla=True)


def test_resultado_e_dataclass_puro_com_duas_casas():
    r = calcular_difal(d("333.33"), d("12"), d("18"), percentual_fcp=d("1"))
    assert is_dataclass(r) and isinstance(r, ResultadoDIFAL)
    for valor in (r.valor_difal, r.fcp_valor, r.icms_interestadual_valor):
        assert valor == valor.quantize(Decimal("0.01"))


# --- Engine --------------------------------------------------------------------

def _item_interestadual(**kw) -> ItemEntrada:
    campos = dict(
        valor_bruto="1000.00",
        aliquota_icms=d("7"),  # o resolver já troca para a interestadual
        difal_aliquota_interestadual=d("7"),
        difal_aliquota_interna_destino=d("18"),
    )
    campos.update(kw)
    return item(**campos)


def test_cenario_e_item_interno_nao_tem_difal_e_totais_zerados():
    resultado = calcular_impostos([item()], nota())
    i = resultado.itens[0]
    assert i.difal_valor is None and i.fcp_valor is None and i.difal_base_calculo is None
    assert resultado.totais.valor_difal == d("0") and resultado.totais.valor_fcp == d("0")
    assert resultado.totais.base_calculo_fcp == d("0")


def test_pipeline_calcula_difal_apos_o_icms():
    resultado = calcular_impostos([_item_interestadual(difal_percentual_fcp=d("2"))], nota(uf_emitente="CE"))
    i = resultado.itens[0]
    assert i.icms_aliquota == d("7") and i.icms_valor == d("70.00")
    assert i.difal_base_calculo == d("1000.00")
    assert (i.difal_aliquota_interestadual, i.difal_aliquota_interna_destino) == (d("7"), d("18"))
    assert i.difal_valor == d("110.00") and i.difal_valor_remetente == d("70.00")
    assert (i.fcp_base_calculo, i.fcp_aliquota, i.fcp_valor) == (d("1000.00"), d("2"), d("20.00"))


def test_totais_somam_difal_e_fcp_sem_entrar_no_total_da_nota():
    itens = [
        _item_interestadual(numero_item=1, difal_percentual_fcp=d("2")),
        _item_interestadual(numero_item=2, valor_bruto="500.00", difal_aliquota_interna_destino=d("20"), difal_percentual_fcp=d("2")),
    ]
    t = calcular_impostos(itens, nota(uf_emitente="CE")).totais
    assert t.valor_icms == d("105.00")            # 70 + 35, pela interestadual
    assert t.valor_difal == d("175.00")           # 110 + 65
    assert t.valor_fcp == d("30.00")              # 20 + 10
    assert t.base_calculo_fcp == d("1500.00")
    assert t.valor_total_nota == d("1500.00")     # DIFAL/FCP ficam fora


def test_frete_rateado_entra_na_base_do_difal():
    resultado = calcular_impostos([_item_interestadual()], nota(uf_emitente="CE", frete="100"))
    i = resultado.itens[0]
    assert i.difal_base_calculo == d("1100.00") and i.difal_valor == d("121.00")


def test_cst_20_usa_a_base_cheia_no_difal():
    """A redução é benefício da origem; o destino recebe o diferencial sobre a base inteira."""
    resultado = calcular_impostos(
        [_item_interestadual(cst_icms="20", reducao_base_icms=d("50"))], nota(uf_emitente="CE"),
    )
    i = resultado.itens[0]
    assert i.icms_base_calculo == d("500.00") and i.icms_valor == d("35.00")
    assert i.difal_base_calculo == d("1000.00")
    assert i.difal_valor == d("110.00") and i.difal_valor_remetente == d("70.00")


def test_base_dupla_chega_ao_engine():
    resultado = calcular_impostos(
        [_item_interestadual(aliquota_icms=d("12"), difal_aliquota_interestadual=d("12"),
                             difal_aliquota_interna_destino=d("20.5"), difal_percentual_fcp=d("2"), difal_base_dupla=True)],
        nota(),
    )
    i = resultado.itens[0]
    assert i.difal_base_calculo == d("1257.86") and i.difal_valor == d("137.86") and i.fcp_valor == d("25.16")
