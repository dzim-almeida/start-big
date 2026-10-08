# ---------------------------------------------------------------------------
# ARQUIVO: test/services/fiscal/test_payload_embalagem.py
# DESCRIÇÃO: Linha de fardo/caixa na NF-e/NFC-e (plano de embalagens, fase 4).
#
# O que se prova aqui: D8 (comercial = embalagem, tributável = unidade),
# D9 (GTIN tudo-ou-nada), 629/630 fechando, snapshot com o fator e a linha de
# UNIDADE saindo exatamente como antes.
# ---------------------------------------------------------------------------

from decimal import Decimal

import pytest

from app.core.gtin import codigo_interno_embalagem
from app.db.models.produto import Produto
from app.db.models.produto_embalagem import ProdutoEmbalagem
from app.db.models.produto_fiscal import ProdutoFiscal
from app.db.models.venda import Venda
from app.db.models.venda_produto import ProdutoVenda
from app.services.fiscal.embalagem_nota import conferir_valores_do_item
from app.services.fiscal.payload_builder import _montar_itens, _montar_itens_devolucao
from app.services.fiscal.snapshot import montar_itens_snapshot

GTIN_UNIDADE = "7891234567895"
DUN_FARDO = "17891234567892"


def _produto(codigo_barras=GTIN_UNIDADE):
    produto = Produto(id=1, nome="Cerveja Lata", codigo_produto="CERV", unidade_medida="UN",
                      codigo_barras=codigo_barras)
    produto.fiscal = ProdutoFiscal(produto_id=1, ncm="22030000", cfop_padrao="5405", origem_mercadoria=0,
                                   unidade_tributavel="UN", cst_icms="60", csosn="500")
    return produto


def _linha(produto, quantidade, valor_unitario, fator=1, sigla=None, codigo_embalagem=None):
    item = ProdutoVenda(id=1, produto_id=1, produto=produto, quantidade=quantidade,
                        valor_unitario=valor_unitario, subtotal=quantidade * valor_unitario, desconto=0)
    if fator > 1:
        item.fator_embalagem = fator
        item.sigla_embalagem = sigla
        item.embalagem = ProdutoEmbalagem(id=10, sigla=sigla, fator=fator, codigo_barras=codigo_embalagem)
    return item


def _itens(*linhas):
    venda = Venda(id=1)
    venda.itens = list(linhas)
    return _montar_itens(venda, simples_nacional=False)


def test_linha_de_unidade_sai_exatamente_como_antes():
    [item] = _itens(_linha(_produto(), 3, 450))
    assert item["unidade_comercial"] == "UN" and item["quantidade_comercial"] == 3.0
    assert item["codigo_barras_comercial"] == GTIN_UNIDADE
    # O payload de sempre não manda os tributáveis de quantidade/valor.
    assert "quantidade_tributavel" not in item and "valor_unitario_tributavel" not in item


def test_fardo_vai_com_comercial_na_embalagem_e_tributavel_na_unidade():
    [item] = _itens(_linha(_produto(), 2, 4800, fator=12, sigla="FD", codigo_embalagem=DUN_FARDO))
    assert (item["unidade_comercial"], item["quantidade_comercial"], item["valor_unitario_comercial"]) == ("FD", 2.0, 48.0)
    assert item["valor_bruto"] == 96.0
    assert (item["unidade_tributavel"], item["quantidade_tributavel"], item["valor_unitario_tributavel"]) == ("UN", 24.0, 4.0)
    assert item["codigo_barras_comercial"] == DUN_FARDO
    assert item["codigo_barras_tributavel"] == GTIN_UNIDADE
    assert conferir_valores_do_item(item) == []


def test_preco_que_nao_divide_certo_ainda_fecha_a_630():
    # 1 CX de 24 a R$ 102,59: vUnTrib = 4,2745833333 — qTrib × vUnTrib ≈ vProd.
    [item] = _itens(_linha(_produto(), 1, 10259, fator=24, sigla="CX", codigo_embalagem=DUN_FARDO))
    assert item["quantidade_tributavel"] == 24.0
    q_trib = Decimal(str(item["quantidade_tributavel"]))
    v_un = Decimal(str(item["valor_unitario_tributavel"]))
    assert abs(q_trib * v_un - Decimal("102.59")) <= Decimal("0.01")
    assert conferir_valores_do_item(item) == []


@pytest.mark.parametrize("codigo_embalagem, codigo_unidade", [
    (codigo_interno_embalagem(10), GTIN_UNIDADE),  # código interno (D18): DV certo, mas não é GTIN público
    (None, GTIN_UNIDADE),              # fardo sem código
    (DUN_FARDO, None),                 # unidade sem código
    (DUN_FARDO, "123"),                # unidade com código interno
    (DUN_FARDO, DUN_FARDO),            # GTIN-14 nunca vai no cEANTrib
])
def test_gtin_e_tudo_ou_nada(codigo_embalagem, codigo_unidade):
    [item] = _itens(_linha(_produto(codigo_unidade), 1, 4800, fator=12, sigla="FD", codigo_embalagem=codigo_embalagem))
    assert (item["codigo_barras_comercial"], item["codigo_barras_tributavel"]) == ("SEM GTIN", "SEM GTIN")


def test_snapshot_congela_o_fator_e_a_unidade_tributavel():
    linhas = [_linha(_produto(), 2, 4800, fator=12, sigla="FD", codigo_embalagem=DUN_FARDO), _linha(_produto(), 3, 450)]
    payload = {"items": _itens(*linhas)}
    fardo, unidade = montar_itens_snapshot(payload)
    assert (fardo.unidade, fardo.quantidade_milesimos, fardo.fator_embalagem) == ("FD", 2000, 12)
    assert (fardo.unidade_tributavel, fardo.codigo_barras_tributavel) == ("UN", GTIN_UNIDADE)
    assert (unidade.fator_embalagem, unidade.unidade_tributavel) == (1, None)


def test_devolucao_de_um_fardo_sai_com_qtrib_da_unidade():
    payload = {"items": _itens(_linha(_produto(), 2, 4800, fator=12, sigla="FD", codigo_embalagem=DUN_FARDO))}
    [snap] = montar_itens_snapshot(payload)

    class Imp:  # tributos zerados: aqui só interessa quantidade/unidade
        numero_item = 1
        icms_origem = "0"; icms_situacao_tributaria = "60"; icms_modalidade_base_calculo = 3
        icms_base_calculo = icms_aliquota = icms_valor = 0
        pis_situacao_tributaria = cofins_situacao_tributaria = "01"
        pis_base_calculo = pis_aliquota = pis_valor = 0
        cofins_base_calculo = cofins_aliquota = cofins_valor = 0

    class Resultado:
        itens = [Imp()]

    [item] = _montar_itens_devolucao([(snap, 1000, "1411")], Resultado(), simples_nacional=False)
    assert (item["unidade_comercial"], item["quantidade_comercial"], item["valor_bruto"]) == ("FD", 1.0, 48.0)
    assert (item["unidade_tributavel"], item["quantidade_tributavel"], item["valor_unitario_tributavel"]) == ("UN", 12.0, 4.0)
    assert (item["codigo_barras_comercial"], item["codigo_barras_tributavel"]) == (DUN_FARDO, GTIN_UNIDADE)
    assert conferir_valores_do_item(item) == []
