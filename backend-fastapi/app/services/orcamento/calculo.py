# ---------------------------------------------------------------------------
# ARQUIVO: services/orcamento/calculo.py
# DESCRICAO: Orcamento - total e desconto.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from app.db.models.orcamento import Orcamento
from app.db.crud import orcamento as orcamento_crud
from app.helpers.exceptions import BadRequestException


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _recalc_total_orcamento(db: Session, orcamento_in_db: Orcamento) -> Orcamento:
    if orcamento_in_db.total_bruto < orcamento_in_db.descontos:
        raise BadRequestException(detail="O desconto nao pode ser maior que o total do orcamento")

    total = orcamento_in_db.total_bruto - orcamento_in_db.descontos

    orcamento_in_db.subtotal = orcamento_in_db.total_bruto
    orcamento_in_db.total = total

    return orcamento_crud.update_orcamento(db, orcamento_in_db)


def _apply_discount(orcamento_in_db: Orcamento, discount: int) -> Orcamento:
    discount_remaining = discount
    for index, item in enumerate(orcamento_in_db.itens):
        if index == len(orcamento_in_db.itens) - 1:
            item.desconto = discount_remaining
        else:
            item_discount = ((item.total * discount) // (orcamento_in_db.total or 1))
            item.desconto = item_discount
            discount_remaining -= item_discount
    return orcamento_in_db
