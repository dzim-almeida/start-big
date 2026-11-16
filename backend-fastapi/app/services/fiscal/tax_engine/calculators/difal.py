# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/tax_engine/calculators/difal.py
# DESCRIÇÃO: Diferencial de alíquota (DIFAL) e FCP da venda interestadual a
#            consumidor final não contribuinte (EC 87/2015).
#
# Duas fórmulas, escolhidas pela regra do perfil (`calculo_base_dupla`):
#
#   Base simples (maioria das UFs)
#     DIFAL = Base × (interna destino − interestadual)
#     FCP   = Base × %FCP
#
#   Base dupla (AL, BA, CE, MA, PA, PE, PI, ...) — o imposto "por dentro"
#     Base'  = Base / (1 − interna destino)
#     DIFAL  = Base' × interna destino − Base × interestadual
#     FCP    = Base' × %FCP
#
# Função pura: sem banco, sem HTTP, mesmo arredondamento do ICMS.
# ---------------------------------------------------------------------------

from dataclasses import dataclass
from decimal import Decimal

from ..constants import PRECISAO, ROUND_MODE

ZERO = Decimal("0")
CEM = Decimal("100")


@dataclass
class ResultadoDIFAL:
    """DIFAL/FCP de um item — o que o grupo ICMSUFDest do XML vai carregar."""

    base_calculo: Decimal               # simples ou dupla, conforme a regra
    aliquota_interna_destino: Decimal
    aliquota_interestadual: Decimal
    valor_difal: Decimal                # ICMS devido à UF de destino

    fcp_base_calculo: Decimal
    fcp_aliquota: Decimal
    fcp_valor: Decimal

    icms_interestadual_valor: Decimal   # ICMS próprio do remetente, pela interestadual


def _arredondar(valor: Decimal) -> Decimal:
    return valor.quantize(PRECISAO, ROUND_MODE)


def calcular_difal(
    base_icms: Decimal,
    aliquota_interestadual: Decimal,
    aliquota_interna_destino: Decimal,
    percentual_fcp: Decimal = ZERO,
    base_dupla: bool = False,
) -> ResultadoDIFAL:
    """
    Args:
        base_icms: base do ICMS próprio SEM redução (produto + frete + seguro
            + despesas − desconto). A redução do CST 20 é benefício da origem
            e não alcança o diferencial do destino.
        aliquota_*: em pontos percentuais (Decimal("12") = 12%).

    Raises:
        ValueError: alíquota interna ≥ 100% em base dupla (divisão por zero).
    """
    icms_inter = _arredondar(base_icms * aliquota_interestadual / CEM)

    if base_dupla:
        fator = CEM - aliquota_interna_destino
        if fator <= ZERO:
            raise ValueError("Alíquota interna do destino ≥ 100% — cálculo por base dupla impossível.")
        base_difal = _arredondar(base_icms * CEM / fator)
        icms_destino = _arredondar(base_difal * aliquota_interna_destino / CEM)
        difal = _arredondar(icms_destino - icms_inter)
    else:
        base_difal = _arredondar(base_icms)
        difal = _arredondar(base_icms * (aliquota_interna_destino - aliquota_interestadual) / CEM)

    # Interestadual maior que a interna (ex.: Zona Franca) não gera crédito
    # reverso: o diferencial é simplesmente zero.
    if difal < ZERO:
        difal = _arredondar(ZERO)

    return ResultadoDIFAL(
        base_calculo=base_difal,
        aliquota_interna_destino=aliquota_interna_destino,
        aliquota_interestadual=aliquota_interestadual,
        valor_difal=difal,
        fcp_base_calculo=base_difal,
        fcp_aliquota=percentual_fcp,
        fcp_valor=_arredondar(base_difal * percentual_fcp / CEM),
        icms_interestadual_valor=icms_inter,
    )
