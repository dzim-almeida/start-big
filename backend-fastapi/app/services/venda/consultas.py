# ---------------------------------------------------------------------------
# ARQUIVO: services/venda/consultas.py
# DESCRICAO: Venda - buscar uma venda, listar e resumo por status.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from typing import Sequence
from app.db.models.venda import Venda
from app.schemas.vendas import VendaSearchFilters, VendaStatusSummary
from app.db.crud import venda as venda_crud
from app.helpers.set_pagination import _set_pagination
from app.helpers.exceptions import NotFoundException


def get_sale_by_id(db: Session, sale_id: int) -> Venda:
    sale_in_db = venda_crud.get_sale_by_id(db, sale_id=sale_id)
    if not sale_in_db:
        raise NotFoundException(detail="Venda não encontrada")
    return sale_in_db


def get_sales(db: Session, filters: VendaSearchFilters, page: int, limit: int = 100) -> tuple[Sequence[Venda], int, int, dict]:
    skip = (page - 1) * limit

    filters_dict = filters.model_dump(exclude_unset=True)
    
    sales_in_db, total_sales = venda_crud.get_sales_by_search(
        db, filters=filters_dict, skip=skip, limit=limit
    )
    
    total_pages, links = _set_pagination(
        total_items=total_sales, filters=filters_dict, page=page, limit=limit
    )

    return sales_in_db, total_sales, total_pages, links


def get_sales_status(db: Session, funcionario_id: int | None = None) -> Sequence[VendaStatusSummary]:
    return venda_crud.get_sales_status(db, funcionario_id=funcionario_id)
