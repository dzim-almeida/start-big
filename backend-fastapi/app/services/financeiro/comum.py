# ---------------------------------------------------------------------------
# ARQUIVO: services/financeiro/comum.py
# DESCRICAO: Financeiro - helpers e constantes usados por varios assuntos do
#            pacote (aqui para os submodulos nao se importarem em circulo).
# ---------------------------------------------------------------------------

from datetime import date
from typing import Any, Dict, Optional


# ===========================================================================
# QUEM FEZ — o funcionário do token (pagar, receber e alertas usam)
# ===========================================================================

def _funcionario_do_token(usuario_token: Dict[str, Any]) -> tuple[Optional[int], Optional[str]]:
    """(id, nome) de quem está operando, para o rastro.

    Tolerante a ausência: o Master pode não ter funcionário vinculado, e recusar
    o lançamento por isso deixaria o dono sem conseguir usar o próprio módulo.
    """
    return usuario_token.get("funcionario_id"), usuario_token.get("nome")


# ===========================================================================
# DATAS — somar meses (recorrência de contas a pagar)
# ===========================================================================

def _somar_meses(base: date, meses: int) -> date:
    """`base` mais N meses, ANCORADO no dia de `base`.

    Encolhe quando o dia não existe no mês de destino (31 em fevereiro vira 28),
    e nunca vaza para o dia 1º do mês seguinte -- vazar atrasaria o alerta em um
    mês inteiro justamente na conta que vence no fim do mês.

    ANCORAR IMPORTA. Calcular cada parcela a partir da ANTERIOR faz o dia
    encolhido ficar encolhido: 31/jan viraria 28/fev e depois 28/mar, quando o
    correto é 31/mar. O erro cresce em silêncio ao longo do parcelamento.
    """
    total = base.month - 1 + meses
    ano = base.year + total // 12
    mes = total % 12 + 1

    dia = base.day
    while dia > 1:
        try:
            return date(ano, mes, dia)
        except ValueError:
            dia -= 1
    return date(ano, mes, 1)


# ===========================================================================
# CONTAS A RECEBER — constante e helper usados por promessas, contas e conciliação
# ===========================================================================

ENTIDADE_CONTA_RECEBER = "CONTA_RECEBER"


def _nome_do_cliente(cliente) -> Optional[str]:
    return getattr(cliente, "nome", None) if cliente else None
