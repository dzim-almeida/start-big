# ---------------------------------------------------------------------------
# ARQUIVO: services/ordem_servico.py
# DESCRICAO: Regras de negocio para Ordens de Servico.
# ---------------------------------------------------------------------------

from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.ordem_servico import (
    OrdemServicoCreate, OrdemServicoUpdate, OrdemServicoFinalizar,
    OrdemServicoCancelar, OrdemServicoQuery, OrdemServicoStats,
    OrdemServicoRead,
)
from app.db.models.ordem_servico import OrdemServico as OSModel
from app.db.models.ordem_servico_item import OrdemServicoItem as OSItemModel
from app.db.models.ordem_servico_pagamento import OrdemServicoPagamento as OSPagamentoModel
from app.db.crud import ordem_servico as os_crud
from app.db.crud import cliente as cliente_crud
from app.core.enum import OrdemServicoStatus, OrdemServicoPrioridade

OS_URL = 'ordens-servico/'

not_found_exce = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Ordem de Servico nao encontrada"
)

invalid_status_exce = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Status da OS nao permite esta operacao"
)


# ===========================================================================
# CRIACAO (CREATE)
# ===========================================================================

def create_ordem_servico(db: Session, os_data: OrdemServicoCreate) -> OSModel:
    """Cria uma nova OS com itens."""
    # Valida cliente
    cliente = cliente_crud.get_cliente_by_id(db, cliente_id=os_data.cliente_id)
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente nao encontrado"
        )

    # Gera numero sequencial
    numero = os_crud.get_next_numero(db)

    # Monta o modelo (excluindo itens para tratar separado)
    os_dict = os_data.model_dump(exclude={"itens"}, exclude_unset=True)
    os_dict["numero"] = numero
    os_dict["status"] = OrdemServicoStatus.ABERTA

    # Calcula valor total dos itens
    valor_total = 0
    itens_data = os_data.itens or []
    for item_data in itens_data:
        valor_total += item_data.quantidade * item_data.valor_unitario

    os_dict["valor_total"] = valor_total

    os_model = OSModel(**os_dict)

    # Cria a OS
    os_criada = os_crud.create_ordem_servico(db, os_model)

    # Cria os itens
    for item_data in itens_data:
        item = OSItemModel(
            ordem_servico_id=os_criada.id,
            servico_id=item_data.servico_id,
            descricao=item_data.descricao,
            quantidade=item_data.quantidade,
            valor_unitario=item_data.valor_unitario,
            valor_total=item_data.quantidade * item_data.valor_unitario,
        )
        os_crud.create_os_item(db, item)

    # Recarrega com relacionamentos
    db.refresh(os_criada)
    return os_crud.get_ordem_servico_by_id(db, os_criada.id)


# ===========================================================================
# LEITURA (READ)
# ===========================================================================

def get_ordem_servico_by_id(db: Session, os_id: int) -> OSModel:
    """Busca OS completa pelo ID."""
    os_in_db = os_crud.get_ordem_servico_by_id(db, os_id)
    if not os_in_db:
        raise not_found_exce
    return os_in_db


def get_ordens_servico_by_search(db: Session, filters: dict, page: int, limit: int) -> OrdemServicoQuery:
    """Busca OS com filtros e paginacao."""
    skip = (page - 1) * limit
    (ordens, total_items) = os_crud.get_ordens_servico_by_search(db, filters=filters, skip=skip, limit=limit)

    total_pages = (
        total_items // limit
        if total_items % limit == 0
        else total_items // limit + 1
    ) if total_items > 0 else 0

    buscar_val = filters.get('buscar') if filters.get('buscar') is not None else ""
    status_val = filters.get('status') if filters.get('status') is not None else ""

    links = {
        "next": f"{OS_URL}?page={page + 1}&limit={limit}&buscar={buscar_val}&status={status_val}" if page < total_pages else None,
        "prev": f"{OS_URL}?page={page - 1}&limit={limit}&buscar={buscar_val}&status={status_val}" if page > 1 else None,
    }

    return OrdemServicoQuery(
        filters=filters,
        items=ordens,
        total_items=total_items,
        page=page,
        limit=limit,
        total_pages=total_pages,
        links=links,
    )


def get_ordens_servico_by_cliente(db: Session, cliente_id: int):
    """Busca todas as OS de um cliente."""
    return os_crud.get_ordens_servico_by_cliente(db, cliente_id)


def get_ordem_servico_stats(db: Session) -> OrdemServicoStats:
    """Retorna estatisticas agregadas."""
    stats_data = os_crud.get_ordem_servico_stats(db)
    return OrdemServicoStats(**stats_data)


def get_next_numero(db: Session) -> dict:
    """Retorna o proximo numero de OS."""
    numero = os_crud.get_next_numero(db)
    return {"numero": numero}


# ===========================================================================
# ATUALIZACAO (UPDATE)
# ===========================================================================

def update_ordem_servico(db: Session, os_id: int, os_data: OrdemServicoUpdate) -> OSModel:
    """Atualiza dados de uma OS existente."""
    os_in_db = os_crud.get_ordem_servico_by_id(db, os_id)
    if not os_in_db:
        raise not_found_exce

    data_update = os_data.model_dump(exclude={"itens"}, exclude_unset=True)

    # Atualiza campos
    for key, value in data_update.items():
        setattr(os_in_db, key, value)

    # Atualiza itens se fornecidos
    if os_data.itens is not None:
        # Remove itens antigos
        os_crud.delete_os_items_by_os_id(db, os_id)

        # Cria novos itens
        valor_total = 0
        for item_data in os_data.itens:
            item_dict = item_data.model_dump(exclude_unset=True)
            quantidade = item_dict.get("quantidade", 1)
            valor_unitario = item_dict.get("valor_unitario", 0)
            valor_item = quantidade * valor_unitario

            item = OSItemModel(
                ordem_servico_id=os_id,
                servico_id=item_dict.get("servico_id"),
                descricao=item_dict.get("descricao", ""),
                quantidade=quantidade,
                valor_unitario=valor_unitario,
                valor_total=valor_item,
            )
            os_crud.create_os_item(db, item)
            valor_total += valor_item

        os_in_db.valor_total = valor_total

    os_crud.update_ordem_servico(db, os_in_db)
    return os_crud.get_ordem_servico_by_id(db, os_id)


# ===========================================================================
# ACOES DE STATUS
# ===========================================================================

def finalizar_ordem_servico(db: Session, os_id: int, data: OrdemServicoFinalizar) -> OSModel:
    """Finaliza uma OS: aplica solucao, registra pagamentos, muda status."""
    os_in_db = os_crud.get_ordem_servico_by_id(db, os_id)
    if not os_in_db:
        raise not_found_exce

    # Valida status (nao pode finalizar uma OS ja finalizada ou cancelada)
    if os_in_db.status in (OrdemServicoStatus.FINALIZADA, OrdemServicoStatus.CANCELADA):
        raise invalid_status_exce

    # Aplica solucao
    os_in_db.solucao = data.solucao
    os_in_db.status = OrdemServicoStatus.FINALIZADA
    os_in_db.data_finalizacao = datetime.now()

    if data.observacoes:
        os_in_db.observacoes = data.observacoes

    if data.desconto is not None:
        os_in_db.desconto = data.desconto

    # Registra pagamentos
    for pag_data in data.pagamentos:
        pagamento = OSPagamentoModel(
            ordem_servico_id=os_id,
            forma_pagamento_id=pag_data.forma_pagamento_id,
            valor=pag_data.valor,
            parcelas=pag_data.parcelas,
            bandeira_cartao=pag_data.bandeira_cartao,
            detalhes=pag_data.detalhes,
        )
        os_crud.create_os_pagamento(db, pagamento)

    os_crud.update_ordem_servico(db, os_in_db)
    return os_crud.get_ordem_servico_by_id(db, os_id)


def cancelar_ordem_servico(db: Session, os_id: int, data: OrdemServicoCancelar) -> OSModel:
    """Cancela uma OS."""
    os_in_db = os_crud.get_ordem_servico_by_id(db, os_id)
    if not os_in_db:
        raise not_found_exce

    if os_in_db.status == OrdemServicoStatus.CANCELADA:
        raise invalid_status_exce

    os_in_db.status = OrdemServicoStatus.CANCELADA

    if data.motivo:
        obs_atual = os_in_db.observacoes or ""
        os_in_db.observacoes = f"{obs_atual}\n[CANCELAMENTO] {data.motivo}".strip()

    os_crud.update_ordem_servico(db, os_in_db)
    return os_crud.get_ordem_servico_by_id(db, os_id)


def reabrir_ordem_servico(db: Session, os_id: int) -> OSModel:
    """Reabre uma OS finalizada ou cancelada."""
    os_in_db = os_crud.get_ordem_servico_by_id(db, os_id)
    if not os_in_db:
        raise not_found_exce

    if os_in_db.status not in (OrdemServicoStatus.FINALIZADA, OrdemServicoStatus.CANCELADA):
        raise invalid_status_exce

    os_in_db.status = OrdemServicoStatus.EM_ANDAMENTO
    os_crud.update_ordem_servico(db, os_in_db)
    return os_crud.get_ordem_servico_by_id(db, os_id)


def toggle_ativo_ordem_servico(db: Session, os_id: int) -> OSModel:
    """Inverte o status ativo da OS (soft delete)."""
    os_in_db = os_crud.get_ordem_servico_by_id(db, os_id)
    if not os_in_db:
        raise not_found_exce

    os_in_db.ativo = not os_in_db.ativo
    os_crud.update_ordem_servico(db, os_in_db)
    return os_crud.get_ordem_servico_by_id(db, os_id)
