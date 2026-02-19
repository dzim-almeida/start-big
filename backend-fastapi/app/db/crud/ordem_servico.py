# ---------------------------------------------------------------------------
# ARQUIVO: crud/ordem_servico.py
# DESCRICAO: Queries SQL via SQLAlchemy para manipulacao de Ordens de Servico.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func
from typing import Sequence
from datetime import datetime

from app.db.models.ordem_servico import OrdemServico as OSModel
from app.db.models.ordem_servico_item import OrdemServicoItem as OSItemModel
from app.db.models.ordem_servico_pagamento import OrdemServicoPagamento as OSPagamentoModel
from app.db.models.ordem_servico_foto import OrdemServicoFoto as OSFotoModel
from app.core.enum import OrdemServicoStatus


# ===========================================================================
# LEITURA (READ)
# ===========================================================================

def get_ordem_servico_by_id(db: Session, os_id: int) -> OSModel | None:
    """Busca OS pelo ID com eager loading de relacionamentos."""
    stmt = (
        select(OSModel)
        .options(
            joinedload(OSModel.cliente),
            joinedload(OSModel.funcionario),
            joinedload(OSModel.itens),
            joinedload(OSModel.pagamentos),
            joinedload(OSModel.fotos),
        )
        .where(OSModel.id == os_id)
    )
    return db.scalars(stmt).unique().first()


def get_ordens_servico_by_search(
    db: Session,
    filters: dict,
    skip: int,
    limit: int = 10
) -> tuple[Sequence[OSModel], int]:
    """Busca avancada de OS com filtros dinamicos e paginacao."""
    query = (
        select(OSModel)
        .options(
            joinedload(OSModel.cliente),
            joinedload(OSModel.funcionario),
        )
    )

    # Filtro de texto (numero, equipamento, defeito)
    buscar = filters.get("buscar")
    if buscar:
        search_pattern = f"%{buscar}%"
        query = query.where(
            OSModel.numero.ilike(search_pattern)
            | OSModel.equipamento.ilike(search_pattern)
            | OSModel.defeito_relatado.ilike(search_pattern)
        )

    # Filtro de status
    status = filters.get("status")
    if status and status != "todos":
        query = query.where(OSModel.status == status)

    # Filtro de cliente
    cliente_id = filters.get("cliente_id")
    if cliente_id:
        query = query.where(OSModel.cliente_id == cliente_id)

    # Filtro de funcionario
    funcionario_id = filters.get("funcionario_id")
    if funcionario_id:
        query = query.where(OSModel.funcionario_id == funcionario_id)

    query = query.order_by(OSModel.id.desc())

    # Conta o total
    count_stmt = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_stmt) or 0

    # Aplica paginacao
    stmt = query.offset(skip).limit(limit)
    ordens = db.scalars(stmt).unique().all()

    return ordens, total


def get_ordens_servico_by_cliente(db: Session, cliente_id: int) -> Sequence[OSModel]:
    """Busca todas as OS de um cliente."""
    stmt = (
        select(OSModel)
        .options(
            joinedload(OSModel.cliente),
            joinedload(OSModel.funcionario),
        )
        .where(OSModel.cliente_id == cliente_id)
        .order_by(OSModel.id.desc())
    )
    return db.scalars(stmt).unique().all()


def get_ordem_servico_stats(db: Session) -> dict:
    """Retorna estatisticas agregadas das OS."""
    stmt = select(
        func.count(OSModel.id).label("total"),
        func.count(OSModel.id).filter(OSModel.status == OrdemServicoStatus.ABERTA).label("abertas"),
        func.count(OSModel.id).filter(
            OSModel.status.in_([
                OrdemServicoStatus.EM_ANDAMENTO,
                OrdemServicoStatus.AGUARDANDO_PECAS,
                OrdemServicoStatus.AGUARDANDO_APROVACAO,
                OrdemServicoStatus.AGUARDANDO_RETIRADA,
            ])
        ).label("em_andamento"),
        func.count(OSModel.id).filter(OSModel.status == OrdemServicoStatus.FINALIZADA).label("finalizadas"),
        func.count(OSModel.id).filter(OSModel.status == OrdemServicoStatus.CANCELADA).label("canceladas"),
    )
    result = db.execute(stmt).one()
    return {
        "total": result.total,
        "abertas": result.abertas,
        "em_andamento": result.em_andamento,
        "finalizadas": result.finalizadas,
        "canceladas": result.canceladas,
    }


def get_next_numero(db: Session) -> str:
    """Gera o proximo numero sequencial de OS (ex: OS-2026-000001)."""
    year = datetime.now().year
    prefix = f"OS-{year}-"

    stmt = (
        select(OSModel.numero)
        .where(OSModel.numero.like(f"{prefix}%"))
        .order_by(OSModel.id.desc())
        .limit(1)
    )
    last_numero = db.scalar(stmt)

    if last_numero:
        last_seq = int(last_numero.replace(prefix, ""))
        next_seq = last_seq + 1
    else:
        next_seq = 1

    return f"{prefix}{next_seq:06d}"


# ===========================================================================
# ESCRITA (CREATE / UPDATE)
# ===========================================================================

def create_ordem_servico(db: Session, os_to_add: OSModel) -> OSModel:
    """Adiciona e persiste uma nova OS no banco."""
    db.add(os_to_add)
    db.flush()
    db.refresh(os_to_add)
    return os_to_add


def update_ordem_servico(db: Session, os_to_update: OSModel) -> OSModel:
    """Atualiza o estado de uma OS ja anexada a sessao."""
    db.flush()
    db.refresh(os_to_update)
    return os_to_update


def create_os_item(db: Session, item: OSItemModel) -> OSItemModel:
    """Adiciona um item a uma OS."""
    db.add(item)
    db.flush()
    db.refresh(item)
    return item


def delete_os_items_by_os_id(db: Session, os_id: int) -> None:
    """Remove todos os itens de uma OS."""
    stmt = select(OSItemModel).where(OSItemModel.ordem_servico_id == os_id)
    items = db.scalars(stmt).all()
    for item in items:
        db.delete(item)
    db.flush()


def create_os_pagamento(db: Session, pagamento: OSPagamentoModel) -> OSPagamentoModel:
    """Adiciona um pagamento a uma OS."""
    db.add(pagamento)
    db.flush()
    db.refresh(pagamento)
    return pagamento


def get_os_foto_by_id(db: Session, foto_id: int) -> OSFotoModel | None:
    """Busca foto pelo ID."""
    stmt = select(OSFotoModel).where(OSFotoModel.id == foto_id)
    return db.scalars(stmt).first()


def create_os_foto(db: Session, foto: OSFotoModel) -> OSFotoModel:
    """Adiciona uma foto a uma OS."""
    db.add(foto)
    db.flush()
    db.refresh(foto)
    return foto


def delete_os_foto(db: Session, foto: OSFotoModel) -> None:
    """Remove uma foto."""
    db.delete(foto)
    db.flush()
