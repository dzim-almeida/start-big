# ---------------------------------------------------------------------------
# ARQUIVO: crud/ordem_servico.py
# DESCRICAO: Queries SQL via SQLAlchemy para manipulação de Ordens de Serviço.
#
# Estrutura das funções:
#   LEITURA  → select sem efeito colateral; retorna model ou None
#   ESCRITA  → modifica estado do banco; usa flush() + refresh() (sem commit)
#              O commit é responsabilidade do _handle_db_transaction no endpoint.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session, aliased
from sqlalchemy import select, func, or_, case
from typing import Sequence
from datetime import datetime

from app.db.models.ordem_servico import OrdemServico as OSModel
from app.db.models.ordem_servico_item import OrdemServicoItem as OSItemModel
from app.db.models.ordem_servico_pagamento import OrdemServicoPagamento as OSPagamentoModel
from app.db.models.ordem_servico_foto import OrdemServicoFoto as OSFotoModel
from app.db.models.ordem_servico_equipamento import OrdemServicoEquipamento as OSEquipamentoModel

from app.db.models.cliente import Cliente as ClienteModel, ClientePF as ClientePFModel, ClientePJ as ClientePJModel

from app.core.enum import OrdemServicoStatus, OrdemServicoPrioridade


# ===========================================================================
# LEITURA (READ) — Ordem de Serviço
# ===========================================================================

def get_ordem_servico_by_id(db: Session, os_id: int) -> OSModel | None:
    """Busca OS pelo ID interno. Usado em operações internas de sub-recursos."""
    return db.scalar(select(OSModel).where(OSModel.id == os_id))


def get_ordem_servico_by_numero_os(db: Session, numero_os: str) -> OSModel | None:
    """Busca OS pelo número sequencial público (ex: OS-2026-000001)."""
    return db.scalar(select(OSModel).where(OSModel.numero_os == numero_os))


def get_ordens_servico_by_search(
    db: Session,
    filters: dict,
    skip: int,
    limit: int = 20
) -> tuple[Sequence[OSModel], int]:
    """
    Busca avançada de OS com filtros dinâmicos e paginação.

    Filtros suportados:
      search        → busca por numero_os, nome do cliente PF, razão social/nome fantasia PJ
      status        → filtra por OrdemServicoStatus
      priority_sort → se True, ordena por prioridade (URGENTE=1 → BAIXA=4)
    """
    query = select(OSModel)

    search = filters.get("search")
    if search:
        # Aliases necessários para a herança polimórfica do modelo Cliente
        client_pj = aliased(ClientePJModel)
        client_pf = aliased(ClientePFModel)

        query = (
            query
            .join(OSModel.equipamento)
            .join(OSEquipamentoModel.cliente)
            .outerjoin(client_pj, ClienteModel.id == client_pj.id)
            .outerjoin(client_pf, ClienteModel.id == client_pf.id)
        )

        like_search = f"%{search}%"
        query = query.where(
            or_(
                OSModel.numero_os.ilike(like_search),
                OSEquipamentoModel.numero_serie.ilike(like_search),
                OSEquipamentoModel.modelo.ilike(like_search),
                client_pf.nome.ilike(like_search),
                client_pj.razao_social.ilike(like_search),
                client_pj.nome_fantasia.ilike(like_search)
            )
        )

    status = filters.get("status")
    if status:
        query = query.where(OSModel.status == status)

    sort_by_priority = filters.get("priority_sort")
    if sort_by_priority:
        # Ordem customizada: URGENTE > ALTA > NORMAL > BAIXA
        order_priority = case(
            (OSModel.prioridade == OrdemServicoPrioridade.URGENTE, 1),
            (OSModel.prioridade == OrdemServicoPrioridade.ALTA, 2),
            (OSModel.prioridade == OrdemServicoPrioridade.NORMAL, 3),
            (OSModel.prioridade == OrdemServicoPrioridade.BAIXA, 4),
            else_=5,
        )
        query = query.order_by(
            order_priority.asc(),
            OSModel.data_criacao.desc()
        )
    else:
        query = query.order_by(OSModel.id.desc())

    count_stmt = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_stmt) or 0

    stmt = query.offset(skip).limit(limit)
    order_services = db.scalars(stmt).unique().all()

    return order_services, total


def get_ordens_servico_by_cliente_id(
    db: Session,
    cliente_id: int,
    skip: int,
    limit: int = 10
) -> tuple[Sequence[OSModel], int]:
    """
    Busca OS vinculadas a um cliente específico via equipamento.

    Retorna tupla (lista_os, total) ordenada por data_criacao desc.
    """
    query = (
        select(OSModel)
        .join(OSModel.equipamento)
        .where(OSEquipamentoModel.cliente_id == cliente_id)
        .order_by(OSModel.data_criacao.desc())
    )

    count_stmt = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_stmt) or 0

    stmt = query.offset(skip).limit(limit)
    order_services = db.scalars(stmt).unique().all()

    return order_services, total


def get_ordem_servico_stats(db: Session) -> dict:
    """Retorna estatísticas agregadas: total, abertas, finalizadas e ticket médio."""
    subq_values = (
        select(
            OSPagamentoModel.ordem_servico_id,
            func.sum(OSPagamentoModel.valor).label("valor_total")
        )
        .group_by(OSPagamentoModel.ordem_servico_id)
        .subquery()
    )

    stmt = select(
        func.count(OSModel.id).label("total"),
        func.count(OSModel.id).filter(OSModel.status == OrdemServicoStatus.ABERTA).label("abertas"),
        func.count(OSModel.id).filter(OSModel.status == OrdemServicoStatus.FINALIZADA).label("finalizadas"),
        func.avg(subq_values.c.valor_total).label("ticket_medio")
    ).outerjoin(subq_values, OSModel.id == subq_values.c.ordem_servico_id)

    result = db.execute(stmt).first()

    return {
        "total": result.total or 0,
        "abertas": result.abertas or 0,
        "finalizadas": result.finalizadas or 0,
        "ticket_medio": int(result.ticket_medio or 0),
    }


def get_next_numero(db: Session) -> str:
    """Gera o próximo número sequencial de OS (ex: OS-2026-000001)."""
    year = datetime.now().year
    prefix = f"OS-{year}-"

    stmt = (
        select(OSModel.numero_os)
        .where(OSModel.numero_os.like(f"{prefix}%"))
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
# LEITURA (READ) — Itens, Fotos
# ===========================================================================

def get_os_item_by_id(db: Session, item_id: int) -> OSItemModel | None:
    """Busca um item de OS pelo ID."""
    return db.scalar(select(OSItemModel).where(OSItemModel.id == item_id))


def get_os_foto_by_id(db: Session, foto_id: int) -> OSFotoModel | None:
    """Busca uma foto de OS pelo ID."""
    return db.scalar(select(OSFotoModel).where(OSFotoModel.id == foto_id))


# ===========================================================================
# ESCRITA (CREATE / UPDATE) — Ordem de Serviço
# ===========================================================================

def create_ordem_servico(db: Session, os_to_add: OSModel) -> OSModel:
    """Adiciona e persiste uma nova OS no banco."""
    db.add(os_to_add)
    db.flush()
    db.refresh(os_to_add)
    return os_to_add


def update_ordem_servico(db: Session, os_to_update: OSModel) -> OSModel:
    """Persiste alterações em uma OS existente."""
    db.flush()
    db.refresh(os_to_update)
    return os_to_update


# ===========================================================================
# ESCRITA (CREATE / UPDATE / DELETE) — Itens
# ===========================================================================

def create_os_item(db: Session, item_to_add: OSItemModel) -> OSItemModel:
    """Adiciona um novo item a uma OS."""
    db.add(item_to_add)
    db.flush()
    db.refresh(item_to_add)
    return item_to_add


def update_os_item(db: Session, item_to_update: OSItemModel) -> OSItemModel:
    """Persiste alterações em um item de OS."""
    db.flush()
    db.refresh(item_to_update)
    return item_to_update


def delete_os_item(db: Session, item_to_delete: OSItemModel) -> None:
    """Remove um item de OS do banco."""
    db.delete(item_to_delete)
    db.flush()


# ===========================================================================
# ESCRITA (CREATE) — Pagamentos
# ===========================================================================

def create_os_pagamento(db: Session, pagamento_to_add: OSPagamentoModel) -> OSPagamentoModel:
    """
    Adiciona um pagamento à OS.
    Pagamentos são criados exclusivamente no fluxo de finalização.
    """
    db.add(pagamento_to_add)
    db.flush()
    db.refresh(pagamento_to_add)
    return pagamento_to_add


# ===========================================================================
# ESCRITA (CREATE / DELETE) — Fotos
# ===========================================================================

def create_os_foto(db: Session, foto_to_add: OSFotoModel) -> OSFotoModel:
    """Registra uma nova foto de OS no banco."""
    db.add(foto_to_add)
    db.flush()
    db.refresh(foto_to_add)
    return foto_to_add


def delete_os_foto(db: Session, foto_to_delete: OSFotoModel) -> None:
    """Remove o registro de uma foto de OS do banco."""
    db.delete(foto_to_delete)
    db.flush()
