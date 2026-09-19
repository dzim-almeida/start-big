# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/tax_engine/consolidador.py
# DESCRIÇÃO: Consolidação dos totais do cabeçalho da NF-e a partir dos itens.
#            A SEFAZ rejeita notas onde a soma dos itens diverge dos totais.
# ---------------------------------------------------------------------------

from decimal import Decimal

from .constants import PRECISAO, ROUND_MODE
from .types import ImpostosItem, ItemEntrada, TotaisNota


def consolidar_totais(
    itens_entrada: list[ItemEntrada],
    itens_impostos: list[ImpostosItem],
) -> TotaisNota:
    """
    Soma os valores calculados nos itens para gerar os totais do cabeçalho.

    A SEFAZ exige que header == sum(itens) para cada campo.
    O valor_total_nota NÃO soma impostos — ICMS, PIS, COFINS já estão
    embutidos no valor dos produtos (não são adicionados ao total).

    Args:
        itens_entrada: Lista de ItemEntrada (valor_bruto de cada item).
        itens_impostos: Lista de ImpostosItem (tributos calculados).

    Returns:
        TotaisNota com todos os campos consolidados.
    """
    total_base_icms = sum(
        i.icms_base_calculo for i in itens_impostos
    ).quantize(PRECISAO, ROUND_MODE)

    total_icms = sum(
        i.icms_valor for i in itens_impostos
    ).quantize(PRECISAO, ROUND_MODE)

    # DIFAL/FCP: só os itens interestaduais têm valor; os demais somam zero.
    total_difal = sum(
        (i.difal_valor or Decimal("0")) for i in itens_impostos
    ).quantize(PRECISAO, ROUND_MODE)

    total_fcp = sum(
        (i.fcp_valor or Decimal("0")) for i in itens_impostos
    ).quantize(PRECISAO, ROUND_MODE)

    total_base_fcp = sum(
        (i.fcp_base_calculo or Decimal("0")) for i in itens_impostos
    ).quantize(PRECISAO, ROUND_MODE)

    # ICMS-ST: retido pelo substituto, cobrado a mais do destinatário.
    total_base_st = sum(
        (i.icms_st_base_calculo or Decimal("0")) for i in itens_impostos
    ).quantize(PRECISAO, ROUND_MODE)

    total_st = sum(
        (i.icms_st_valor or Decimal("0")) for i in itens_impostos
    ).quantize(PRECISAO, ROUND_MODE)

    total_pis = sum(
        i.pis_valor for i in itens_impostos
    ).quantize(PRECISAO, ROUND_MODE)

    total_cofins = sum(
        i.cofins_valor for i in itens_impostos
    ).quantize(PRECISAO, ROUND_MODE)

    total_frete = sum(
        i.valor_frete for i in itens_impostos
    ).quantize(PRECISAO, ROUND_MODE)

    total_seguro = sum(
        i.valor_seguro for i in itens_impostos
    ).quantize(PRECISAO, ROUND_MODE)

    total_desconto = sum(
        i.valor_desconto for i in itens_impostos
    ).quantize(PRECISAO, ROUND_MODE)

    total_despesas = sum(
        i.valor_outras_despesas for i in itens_impostos
    ).quantize(PRECISAO, ROUND_MODE)

    total_produtos = sum(
        ie.valor_bruto for ie in itens_entrada
    ).quantize(PRECISAO, ROUND_MODE)

    # Total da nota: produtos + frete + seguro + despesas - desconto
    # Impostos (ICMS, PIS, COFINS) NÃO somam — já estão embutidos.
    # DIFAL e FCP também não: vão em <ICMSUFDest>, fora do vNF.
    # O ICMS-ST SIM: é encargo cobrado a mais do destinatário (vNF = ... + vST).
    total_nota = (
        total_produtos + total_frete + total_seguro + total_despesas - total_desconto + total_st
    ).quantize(PRECISAO, ROUND_MODE)

    return TotaisNota(
        base_calculo_icms=total_base_icms,
        valor_icms=total_icms,
        valor_pis=total_pis,
        valor_cofins=total_cofins,
        valor_difal=total_difal,
        valor_fcp=total_fcp,
        base_calculo_fcp=total_base_fcp,
        base_calculo_icms_st=total_base_st,
        valor_icms_st=total_st,
        valor_frete=total_frete,
        valor_seguro=total_seguro,
        valor_desconto=total_desconto,
        valor_outras_despesas=total_despesas,
        valor_total_produtos=total_produtos,
        valor_total_nota=total_nota,
    )
