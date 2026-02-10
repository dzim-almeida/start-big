# ---------------------------------------------------------------------------
# ARQUIVO: servico_crud.py
# MÓDULO: Acesso a Dados (Repository)
# DESCRIÇÃO: Executa queries SQL via SQLAlchemy para manipulação de Serviços.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import Sequence

from app.db.models.servico import Servico as ServicoModel

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
    search: str | None,
    skip: int,
    limit: int = 20
) -> tuple[Sequence[ServicoModel], int]:
    """
    Busca Simples de Serviços.
    
    Retorna serviços cuja descrição comece com o termo pesquisado.
    Se nenhum termo for fornecido, retorna todos os serviços ativos.

    Args:
        search (str | None): Termo a ser buscado (case sensitive dependendo do DB).
        
    Returns:
        Sequence[ServicoModel]: Lista de serviços que correspondem aos critérios.
    """
    if not search:
        query = select(ServicoModel)
    else:
        query = select(ServicoModel).where(
            ServicoModel.descricao.ilike(f"{search}%")
        )

    # Conta o total de registros antes da repartição
    count_stmt = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_stmt) or 0

    stmt = query.offset(skip).limit(limit)
    servicos = db.scalars(stmt).all()

    return servicos, total

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