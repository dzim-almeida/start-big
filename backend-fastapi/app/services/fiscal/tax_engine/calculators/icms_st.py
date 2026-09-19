# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/tax_engine/calculators/icms_st.py
# DESCRIÇÃO: ICMS por Substituição Tributária na venda interestadual a
#            contribuinte, com o remetente como substituto (Conv. 142/2018).
#
#   Base ST   = (produto + frete + seguro + despesas − desconto) × (1 + MVA)
#   Base ST'  = Base ST × (1 − redução)            (se a regra reduz)
#   Débito    = Base ST' × alíquota interna do destino
#   ICMS-ST   = Débito − ICMS próprio                (piso zero)
#
# Diferente do DIFAL, o ICMS-ST é cobrado A MAIS do destinatário: entra no
# valor total da nota (vNF) — quem soma é o consolidador.
#
# Função pura: sem banco, sem HTTP, mesmo arredondamento do ICMS.
# ---------------------------------------------------------------------------

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from ..constants import PRECISAO, ROUND_MODE

ZERO = Decimal("0")
CEM = Decimal("100")

# modBCST 4 = Margem Valor Agregado (%)
MODALIDADE_BASE_ST_MVA = 4


@dataclass
class ResultadoICMSST:
    """ICMS-ST de um item — o que o grupo ICMS10/70 (ou ICMSSN201/202) leva."""

    base_calculo_st: Decimal
    mva: Decimal
    aliquota_interna_destino: Decimal
    aliquota_interestadual: Decimal
    valor_icms_proprio: Decimal        # o que foi abatido do débito no destino
    valor_icms_st: Decimal             # retido, nunca negativo
    reducao_base_st: Optional[Decimal] = None


def _arredondar(valor: Decimal) -> Decimal:
    return valor.quantize(PRECISAO, ROUND_MODE)


def calcular_icms_st(
    base_inicial: Decimal,
    aliquota_interestadual: Decimal,
    aliquota_interna_destino: Decimal,
    mva: Decimal,
    reducao_base_st: Optional[Decimal] = None,
    icms_proprio_informado: Optional[Decimal] = None,
) -> ResultadoICMSST:
    """
    Args:
        base_inicial: base do ICMS próprio, sem redução.
        icms_proprio_informado: o ICMS próprio REAL do item (regime normal —
            com a redução do CST 70, se houver). None = calcula pela
            alíquota interestadual, que é a dedução do remetente do Simples
            (que não destaca ICMS próprio, mas abate o valor que seria devido).
    """
    if icms_proprio_informado is not None:
        icms_proprio = icms_proprio_informado
    else:
        icms_proprio = _arredondar(base_inicial * aliquota_interestadual / CEM)

    base_st = _arredondar(base_inicial * (CEM + mva) / CEM)
    reducao = reducao_base_st if reducao_base_st and reducao_base_st > ZERO else None
    if reducao is not None:
        base_st = _arredondar(base_st * (CEM - reducao) / CEM)

    debito_destino = _arredondar(base_st * aliquota_interna_destino / CEM)
    valor_st = _arredondar(debito_destino - icms_proprio)
    if valor_st < ZERO:
        valor_st = _arredondar(ZERO)

    return ResultadoICMSST(
        base_calculo_st=base_st,
        mva=mva,
        aliquota_interna_destino=aliquota_interna_destino,
        aliquota_interestadual=aliquota_interestadual,
        valor_icms_proprio=icms_proprio,
        valor_icms_st=valor_st,
        reducao_base_st=reducao,
    )
