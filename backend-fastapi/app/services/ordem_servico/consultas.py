# ---------------------------------------------------------------------------
# ARQUIVO: services/ordem_servico/consultas.py
# DESCRICAO: Ordem de servico - leitura, busca, estatisticas, abandono e atrasadas.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from app.schemas.ordem_servico import (
    OrdemServicoQuery,
    OrdemServicoStats
)
from app.db.models.ordem_servico import OrdemServico as OSModel
from app.db.crud import ordem_servico as os_crud
from app.db.crud import cliente as cliente_crud
from app.helpers.set_pagination import _set_pagination
from app.services.ordem_servico.excecoes import cliente_not_found_exce, os_not_found_exce


# ===========================================================================
# LEITURA (READ)
# ===========================================================================

def get_ordem_servico_by_numero_os(db: Session, numero_os: str) -> OSModel:
    """Busca OS pelo número sequencial público. Lança 404 se não encontrada."""
    os_in_db = os_crud.get_ordem_servico_by_numero_os(db, numero_os=numero_os)
    if not os_in_db:
        raise os_not_found_exce
    return os_in_db


def get_ordem_servico_by_search(db: Session, filters: dict, page: int, limit: int) -> OrdemServicoQuery:
    """Retorna lista paginada de OS com filtros dinâmicos."""
    skip = (page - 1) * limit
    (order_service_in_db, total_items) = os_crud.get_ordens_servico_by_search(
        db, filters=filters, skip=skip, limit=limit
    )

    (total_pages, link) = _set_pagination(
        total_items=total_items, filters=filters, page=page, limit=limit
    )

    return OrdemServicoQuery(
        filters=filters,
        items=order_service_in_db,
        total_items=total_items,
        page=page,
        limit=limit,
        total_pages=total_pages,
        links=link,
    )


def get_ordens_servico_by_cliente_id(
    db: Session, cliente_id: int, page: int, limit: int
) -> OrdemServicoQuery:
    """Retorna lista paginada de OS vinculadas a um cliente específico."""
    cliente_in_db = cliente_crud.get_cliente_by_id(db, cliente_id=cliente_id)
    if not cliente_in_db:
        raise cliente_not_found_exce

    skip = (page - 1) * limit
    (order_service_in_db, total_items) = os_crud.get_ordens_servico_by_cliente_id(
        db, cliente_id=cliente_id, skip=skip, limit=limit
    )

    filters = {"cliente_id": cliente_id}
    (total_pages, link) = _set_pagination(
        total_items=total_items, filters=filters, page=page, limit=limit
    )

    return OrdemServicoQuery(
        filters=filters,
        items=order_service_in_db,
        total_items=total_items,
        page=page,
        limit=limit,
        total_pages=total_pages,
        links=link,
    )


def get_ordem_servico_stats(db: Session, funcionario_id: int | None = None) -> OrdemServicoStats:
    """Retorna estatísticas agregadas das OS."""
    return os_crud.get_ordem_servico_stats(db, funcionario_id=funcionario_id)


def get_os_abandono(db: Session, empresa_id: int, funcionario_id: int | None = None) -> list[OSModel]:
    """Retorna OS finalizadas cujo prazo de abandono já venceu, usando config da empresa."""
    from app.services.configuracao_os import get_or_create_configuracao_os
    config = get_or_create_configuracao_os(db, empresa_id)
    return os_crud.get_os_abandono(db, empresa_id, config.prazo_abandono_dias, funcionario_id=funcionario_id)


def get_os_atrasadas(db: Session, empresa_id: int, funcionario_id: int | None = None) -> list[OSModel]:
    """Retorna OS abertas com prazo de entrega vencido."""
    return os_crud.get_os_atrasadas(db, empresa_id, funcionario_id=funcionario_id)
