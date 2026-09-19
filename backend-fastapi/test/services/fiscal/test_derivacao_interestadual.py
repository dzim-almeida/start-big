# ---------------------------------------------------------------------------
# ARQUIVO: test/services/fiscal/test_derivacao_interestadual.py
# DESCRIÇÃO: TASK008 CA-3 — CFOP e CST/CSOSN derivados da OPERAÇÃO quando o
#            perfil já disse se há ST. Funções puras.
# ---------------------------------------------------------------------------

import pytest

from app.services.fiscal.derivacao.cfop import (
    NATUREZA_POR_CFOP,
    DerivacaoAmbiguaError,
    derivar_cfop,
    derivar_cfop_operacao,
)
from app.services.fiscal.derivacao.situacao import derivar_situacao_operacao
from app.services.fiscal.derivacao.types import ContextoDerivacao

CONTRIBUINTE, ISENTO, NAO_CONTRIBUINTE = 1, 2, 9
BALCAO, INTERNET = 1, 2


# --- CFOP por operação ------------------------------------------------------

@pytest.mark.parametrize("uf_dest, indpres", [("SP", INTERNET), ("MG", BALCAO), (None, INTERNET)])
def test_operacao_interna_ou_balcao_fica_no_grupo_5(uf_dest, indpres):
    assert derivar_cfop_operacao("SP", uf_dest, indpres, NAO_CONTRIBUINTE, existe_st_na_regra=False) == "5102"
    assert derivar_cfop_operacao("SP", uf_dest, indpres, CONTRIBUINTE, existe_st_na_regra=False, eh_producao_propria=True) == "5101"
    assert derivar_cfop_operacao("SP", uf_dest, indpres, CONTRIBUINTE, existe_st_na_regra=True) == "5405"


def test_b2c_interestadual_e_6108_ou_6107():
    assert derivar_cfop_operacao("SP", "MG", INTERNET, NAO_CONTRIBUINTE, existe_st_na_regra=False) == "6108"
    assert derivar_cfop_operacao("SP", "MG", INTERNET, NAO_CONTRIBUINTE, existe_st_na_regra=False, eh_producao_propria=True) == "6107"
    # ST na regra não muda o B2C: consumidor final não tem cadeia seguinte
    assert derivar_cfop_operacao("SP", "MG", INTERNET, NAO_CONTRIBUINTE, existe_st_na_regra=True) == "6108"


@pytest.mark.parametrize("ie", [CONTRIBUINTE, ISENTO])
def test_b2b_interestadual_sem_st_e_6102_ou_6101(ie):
    assert derivar_cfop_operacao("SP", "mg", INTERNET, ie, existe_st_na_regra=False) == "6102"
    assert derivar_cfop_operacao("SP", "MG", INTERNET, ie, existe_st_na_regra=False, eh_producao_propria=True) == "6101"


def test_b2b_interestadual_com_st_e_6404_ou_6403():
    assert derivar_cfop_operacao("SP", "MG", INTERNET, CONTRIBUINTE, existe_st_na_regra=True) == "6404"
    assert derivar_cfop_operacao("SP", "MG", INTERNET, CONTRIBUINTE, existe_st_na_regra=True, eh_producao_propria=True) == "6403"


def test_todos_os_cfops_derivaveis_tem_natureza():
    for cfop in ("5101", "5102", "5405", "6101", "6102", "6107", "6108", "6403", "6404"):
        assert cfop in NATUREZA_POR_CFOP, cfop


# --- derivar_cfop(ctx) do cadastro ------------------------------------------

def _ctx(**kw) -> ContextoDerivacao:
    base = dict(uf_emitente="SP", crt=3, uf_destinatario="MG", indicador_presenca=INTERNET)
    base.update(kw)
    return ContextoDerivacao(**base)


def test_cadastro_sem_saber_do_perfil_continua_recusando_o_substituido_interestadual():
    with pytest.raises(DerivacaoAmbiguaError):
        derivar_cfop(_ctx(), situacao_tributaria="60")


def test_cadastro_com_a_regra_do_perfil_resolve_o_substituido():
    assert derivar_cfop(_ctx(destinatario_pj_com_ie=True), situacao_tributaria="60", existe_st_na_regra=True).valor == "6404"
    assert derivar_cfop(_ctx(destinatario_pj_com_ie=True), situacao_tributaria="60", existe_st_na_regra=False).valor == "6102"


# --- CST/CSOSN por operação --------------------------------------------------

def test_sem_st_a_situacao_do_produto_nao_muda():
    assert derivar_situacao_operacao("20", None, simples=False, existe_st=False, tem_reducao=True) == "20"
    assert derivar_situacao_operacao(None, "102", simples=True, existe_st=False, tem_reducao=False) == "102"


def test_com_st_no_regime_normal_e_10_ou_70():
    assert derivar_situacao_operacao("00", None, simples=False, existe_st=True, tem_reducao=False) == "10"
    assert derivar_situacao_operacao("20", None, simples=False, existe_st=True, tem_reducao=True) == "70"


def test_com_st_no_simples_e_201_ou_202():
    assert derivar_situacao_operacao(None, "101", simples=True, existe_st=True, tem_reducao=False) == "201"
    assert derivar_situacao_operacao(None, "102", simples=True, existe_st=True, tem_reducao=False) == "202"
    assert derivar_situacao_operacao(None, None, simples=True, existe_st=True, tem_reducao=False) == "202"
