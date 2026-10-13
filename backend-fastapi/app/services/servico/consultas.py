# ---------------------------------------------------------------------------
# ARQUIVO: services/servico/consultas.py
# DESCRICAO: Servico - busca e estatisticas.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from app.schemas.servico import ServicoQuery, ServicoStats
from app.db.crud import servico as servico_crud


SERVICE_URL = 'servicos/'


# ===========================================================================
# LÓGICA DE LEITURA (READ)
# ===========================================================================

def get_servico_by_search(db: Session, filters: dict, page: int, limit: int) -> ServicoQuery:
    """
    Intermediário para busca de serviços.
    Repassa a query string para o CRUD realizar a filtragem.
    """

    # Quantidades de Elementos Desnecessários
    skip = (page - 1) * limit

    (servicos_in_db, total_items) = servico_crud.get_servico_by_search(db, filters=filters, skip=skip, limit=limit)

    total_pages = (
        # Retorna total_items // limit se resto 0
        total_items // limit
        if total_items % limit == 0 
        # Caso contrário, retorna resultado + 1
        else total_items // limit + 1
    )

    # Trata os valores para não aparecer "None" na URL
    search_val = filters.get('search') if filters.get('search') is not None else ""
    active_val = filters.get('active') if filters.get('active') is not None else ""

    links = {
        "next": f"{SERVICE_URL}?page={page + 1}&limit={limit}&search={search_val}&active={active_val}" if page < total_pages else None,
        "prev": f"{SERVICE_URL}?page={page - 1}&limit={limit}&search={search_val}&active={active_val}" if page > 1 else None
    }

    servicos_query = ServicoQuery(
        filters=filters,
        items=servicos_in_db,
        total_items=total_items,
        page=page,
        limit=limit,
        total_pages=total_pages,
        links=links,
    )

    return servicos_query


def get_servico_stats(db: Session) -> ServicoStats:
    """Retorna estatísticas agregadas dos serviços."""
    stats_data = servico_crud.get_servico_stats(db)
    return ServicoStats(**stats_data)
