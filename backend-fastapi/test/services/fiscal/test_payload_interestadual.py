# ---------------------------------------------------------------------------
# ARQUIVO: test/services/fiscal/test_payload_interestadual.py
# DESCRIÇÃO: TASK009 — o payload da NF-e interestadual na nomenclatura da
#            Focus NFe: ICMSUFDest (DIFAL/FCP), grupo ST, totais e idDest.
# ---------------------------------------------------------------------------

from decimal import Decimal

import pytest

from app.db.models.cliente import ClientePF
from app.services.fiscal.payload_builder import montar_payload_nfe
from app.services.fiscal.tax_engine.engine import calcular_impostos
from app.services.fiscal.tax_engine.types import DadosNota, ItemEntrada

from .conftest import d
from .test_payload_builder import (
    _empresa, _endereco_empresa, _fiscal_settings, _item_venda, _pagamento, _produto, _venda,
)

CHAVES_DIFAL = {
    "base_calculo_uf_destino", "aliquota_interna_uf_destino", "aliquota_interestadual",
    "valor_icms_interestadual_uf_destino", "valor_icms_interestadual_uf_remetente",
}
CHAVES_FCP = {"base_calculo_fcp_uf_destino", "percentual_fcp_uf_destino", "valor_fcp_uf_destino"}
CHAVES_ST = {
    "icms_modalidade_base_calculo_st", "icms_base_calculo_st", "icms_aliquota_st",
    "icms_valor_st", "icms_margem_valor_adicionado_st",
}
CHAVES_TOTAIS_NOVAS = {
    "icms_base_calculo_st", "icms_valor_total_st", "valor_icms_uf_destino", "valor_fcp_uf_destino",
}


def _item_entrada(iv, cfop, **extras) -> ItemEntrada:
    campos = dict(
        numero_item=1, produto_id=iv.produto_id, descricao=iv.produto.nome,
        quantidade=d(iv.quantidade), valor_unitario=d(iv.valor_unitario) / 100,
        valor_bruto=d(iv.subtotal) / 100, desconto_item=d(iv.desconto) / 100,
        ncm="84716052", cfop=cfop, origem_mercadoria=0, cst_icms="00", csosn="102",
        aliquota_icms=d("12"), aliquota_pis=d("0.65"), aliquota_cofins=d("3"),
    )
    campos.update(extras)
    return ItemEntrada(**campos)


def _montar(venda, itens_entrada, simples=False, total_pagamento=None):
    resultado = calcular_impostos(itens_entrada, DadosNota(uf_emitente="SP", simples_nacional=simples))
    if total_pagamento is not None:
        # Com ST o que se cobra do cliente é produtos + ST: a venda do PDV
        # precisa fechar com o vNF (Rejeição 767), senão o builder recusa.
        venda.total = total_pagamento
        venda.pagamentos = [_pagamento(total_pagamento)]
    return montar_payload_nfe(
        empresa=_empresa("Simples Nacional" if simples else "Lucro Presumido"),
        endereco_empresa=_endereco_empresa(),
        fiscal_settings=_fiscal_settings(),
        venda=venda,
        nota_fiscal=None,
        resultado_calculo=resultado,
    ), resultado


@pytest.fixture
def venda():
    iv = _item_venda(1, _produto(1), quantidade=1, valor_unitario=100000)
    return _venda([iv], [_pagamento(100000)], cliente=ClientePF(id=1, nome="Maria", cpf="52998224725"))


# --- DIFAL (não contribuinte) --------------------------------------------------

def test_difal_sai_no_item_com_as_chaves_da_focus(venda):
    payload, _ = _montar(venda, [_item_entrada(
        venda.itens[0], "6108",
        difal_aliquota_interestadual=d("12"), difal_aliquota_interna_destino=d("18"), difal_percentual_fcp=d("2"),
    )])
    item = payload["items"][0]
    assert item["cfop"] == "6108"
    assert CHAVES_DIFAL | CHAVES_FCP <= set(item)
    assert item["base_calculo_uf_destino"] == 1000.0
    assert item["aliquota_interestadual"] == 12.0 and item["aliquota_interna_uf_destino"] == 18.0
    assert item["valor_icms_interestadual_uf_destino"] == 60.0
    assert item["valor_icms_interestadual_uf_remetente"] == 120.0
    assert item["percentual_fcp_uf_destino"] == 2.0 and item["valor_fcp_uf_destino"] == 20.0
    assert item["base_calculo_fcp_uf_destino"] == 1000.0
    assert not CHAVES_ST & set(item)


def test_difal_nos_totais_sem_mexer_no_valor_total(venda):
    payload, _ = _montar(venda, [_item_entrada(
        venda.itens[0], "6108", difal_aliquota_interestadual=d("12"), difal_aliquota_interna_destino=d("18"),
    )])
    t = payload["totais"]
    assert t["valor_icms_uf_destino"] == 60.0 and t["valor_total"] == 1000.0
    assert "valor_fcp_uf_destino" not in t and "icms_valor_total_st" not in t   # zero = omitido


def test_local_destino_2_acompanha_o_cfop(venda):
    payload, _ = _montar(venda, [_item_entrada(venda.itens[0], "6102")])
    assert payload["local_destino"] == 2


# --- ICMS-ST (contribuinte) ------------------------------------------------------

def test_st_sai_no_item_e_nos_totais_com_o_valor_total_acrescido(venda):
    payload, resultado = _montar(venda, [_item_entrada(
        venda.itens[0], "6404", cst_icms="10",
        st_aliquota_interestadual=d("12"), st_aliquota_interna_destino=d("18"), st_mva=d("40"), st_reducao_base=d("20"),
    )], total_pagamento=108160)
    item = payload["items"][0]
    assert item["cfop"] == "6404" and item["icms_situacao_tributaria"] == "10"
    assert CHAVES_ST <= set(item)
    assert item["icms_modalidade_base_calculo_st"] == 4
    assert item["icms_base_calculo_st"] == 1120.0 and item["icms_aliquota_st"] == 18.0
    assert item["icms_margem_valor_adicionado_st"] == 40.0 and item["icms_reducao_base_calculo_st"] == 20.0
    assert item["icms_valor_st"] == 81.6
    assert not CHAVES_DIFAL & set(item)

    t = payload["totais"]
    assert t["icms_base_calculo_st"] == 1120.0 and t["icms_valor_total_st"] == 81.6
    assert t["valor_total"] == 1081.6 == float(resultado.totais.valor_total_nota)


def test_st_sem_reducao_omite_a_reducao(venda):
    payload, _ = _montar(venda, [_item_entrada(
        venda.itens[0], "6404", cst_icms="10",
        st_aliquota_interestadual=d("12"), st_aliquota_interna_destino=d("18"), st_mva=d("40"),
    )], total_pagamento=113200)
    assert "icms_reducao_base_calculo_st" not in payload["items"][0]


def test_simples_com_st_usa_os_mesmos_campos_com_csosn_202(venda):
    payload, _ = _montar(venda, [_item_entrada(
        venda.itens[0], "6404", cst_icms=None, csosn="202", aliquota_icms=d("0"),
        st_aliquota_interestadual=d("12"), st_aliquota_interna_destino=d("18"), st_mva=d("40"),
    )], simples=True, total_pagamento=113200)
    item = payload["items"][0]
    assert item["icms_situacao_tributaria"] == "202" and item["icms_valor_st"] == 132.0
    assert not CHAVES_DIFAL & set(item)


# --- Guardrails / o que não muda --------------------------------------------------

def test_operacao_interna_nao_ganha_campo_novo(venda):
    payload, _ = _montar(venda, [_item_entrada(venda.itens[0], "5102", aliquota_icms=d("18"))])
    assert payload["local_destino"] == 1 and payload["items"][0]["cfop"] == "5102"
    assert not (CHAVES_DIFAL | CHAVES_FCP | CHAVES_ST) & set(payload["items"][0])
    assert not CHAVES_TOTAIS_NOVAS & set(payload["totais"])


def test_itens_com_grupos_de_cfop_diferentes_e_recusado():
    ivs = [_item_venda(1, _produto(1), valor_unitario=10000), _item_venda(2, _produto(2, "Mouse"), valor_unitario=10000)]
    venda = _venda(ivs, [_pagamento(20000)], cliente=ClientePF(id=1, nome="Maria", cpf="52998224725"))
    itens = [
        _item_entrada(ivs[0], "6102"),
        _item_entrada(ivs[1], "5102", numero_item=2),
    ]
    with pytest.raises(ValueError, match="CFOP"):
        _montar(venda, itens)


def test_sem_resultado_do_motor_local_destino_continua_1(venda):
    payload = montar_payload_nfe(
        empresa=_empresa(), endereco_empresa=_endereco_empresa(), fiscal_settings=_fiscal_settings(),
        venda=venda, nota_fiscal=None, resultado_calculo=None,
    )
    assert payload["local_destino"] == 1
