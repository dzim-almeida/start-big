# ---------------------------------------------------------------------------
# ARQUIVO: servico_crud.py
# MÓDULO: Acesso a Dados (Repository)
# DESCRIÇÃO: Executa queries SQL via SQLAlchemy para manipulação de Serviços.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import Sequence

from app.db.models.servico import Servico as ServicoModel
from app.schemas.servico import ServicoFilterParams


# ===========================================================================
# LEITURA (READ)
# ===========================================================================

def get_servico_by_id(db: Session, servico_id: int) -> ServicoModel | None:
    """Busca serviço pelo ID (PK)."""
    stmt = select(ServicoModel).where(ServicoModel.id == servico_id)
    servico_in_db = db.scalars(stmt).first()
    return servico_in_db

def get_servico_by_search(
    db: Session,
    filters: dict, 
    skip: int,
    limit: int = 20
) -> tuple[Sequence[ServicoModel], int]:
    """
    Busca Avançada de Serviços com filtros dinâmicos.
    """
    query = select(ServicoModel)

    # Filtro de texto (Descrição)
    search = filters.get("search")
    if search:
        query = query.where(ServicoModel.descricao.ilike(f"%{search}%"))

    # Filtro de status (Trata explicitamente True/False)
    active = filters.get("active")
    if active is not None:
        query = query.where(ServicoModel.ativo == active)

    query = query.order_by(ServicoModel.id.desc())

    # Conta o total com os filtros aplicados
    count_stmt = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_stmt) or 0

    # Aplica paginação
    stmt = query.offset(skip).limit(limit)
    servicos = db.scalars(stmt).all()

    return servicos, total

def get_servico_stats(db: Session) -> dict:
    """Retorna estatísticas agregadas dos serviços."""
    stmt = select(
        func.count(ServicoModel.id).label("total"),
        func.count(ServicoModel.id).filter(ServicoModel.ativo == True).label("ativos"),
        func.count(ServicoModel.id).filter(ServicoModel.ativo == False).label("inativos"),
        func.coalesce(func.avg(ServicoModel.valor), 0).label("media_valor"),
    )
    result = db.execute(stmt).one()
    return {
        "total": result.total,
        "ativos": result.ativos,
        "inativos": result.inativos,
        "media_valor": int(result.media_valor),
    }


def get_servico_by_description(db: Session, description_to_search: str) -> ServicoModel | None:
    """Busca serviço pela descrição exata (útil para verificar duplicidade)."""
    stmt = select(ServicoModel).where(ServicoModel.descricao == description_to_search)
    servico_in_db = db.scalars(stmt).first()
    return servico_in_db

# ===========================================================================
# ESCRITA (CREATE / UPDATE)
# ===========================================================================

def create_servico(db: Session, servico_to_add: ServicoModel) -> ServicoModel:
    """Adiciona e persiste um novo serviço no banco."""
    db.add(servico_to_add)
    db.flush() # Gera o ID sem comitar a transação final ainda
    db.refresh(servico_to_add)
    return servico_to_add

def update_servico(db: Session, servico_to_update: ServicoModel) -> ServicoModel:
    """Atualiza o estado de um serviço já anexado à sessão."""
    db.flush()
    db.refresh(servico_to_update)
    return servico_to_update