# ---------------------------------------------------------------------------
# ARQUIVO: services/orcamento/consultas.py
# DESCRICAO: Orcamento - buscar um orcamento, listar e resumo por status.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from typing import Sequence
from app.db.models.orcamento import Orcamento
from app.schemas.orcamentos import OrcamentoSearchFilters, OrcamentoStatusSummary
from app.db.crud import orcamento as orcamento_crud
from app.helpers.set_pagination import _set_pagination
from app.helpers.exceptions import NotFoundException


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

def get_orcamento_by_id(db: Session, orcamento_id: int) -> Orcamento:
    orcamento_in_db = orcamento_crud.get_orcamento_by_id(db, orcamento_id=orcamento_id)
    if not orcamento_in_db:
        raise NotFoundException(detail="Orcamento nao encontrado")
    return orcamento_in_db


def get_orcamentos(db: Session, filters: OrcamentoSearchFilters, page: int, limit: int = 100) -> tuple[Sequence[Orcamento], int, int, dict]:
    skip = (page - 1) * limit

    filters_dict = filters.model_dump(exclude_unset=True)

    orcamentos_in_db, total = orcamento_crud.get_orcamentos_by_search(
        db, filters=filters_dict, skip=skip, limit=limit
    )

    total_pages, links = _set_pagination(
        total_items=total, filters=filters_dict, page=page, limit=limit
    )

    return orcamentos_in_db, total, total_pages, links


def get_orcamentos_status(db: Session, funcionario_id: int | None = None) -> OrcamentoStatusSummary:
    return orcamento_crud.get_orcamentos_status(db, funcionario_id=funcionario_id)
