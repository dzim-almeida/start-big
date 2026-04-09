# ---------------------------------------------------------------------------
# ARQUIVO: services/ordem_servico.py
# DESCRICAO: Regras de negócio para Ordens de Serviço.
#
# Fluxo de status permitidos:
#   ABERTA → EM_ANDAMENTO → AGUARDANDO_PECAS → AGUARDANDO_APROVACAO
#          → AGUARDANDO_RETIRADA → FINALIZADA
#   Qualquer status ativo → CANCELADA
#   FINALIZADA / CANCELADA → EM_ANDAMENTO  (via /reabrir)
#
# Regras financeiras:
#   valor_bruto = soma dos itens (quantidade × valor_unitario)
#   valor_total = valor_bruto - desconto
#   Finalização só é permitida se sum(pagamentos) + valor_entrada == valor_total
# ---------------------------------------------------------------------------

from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.ordem_servico import (
    OrdemServicoCreate,
    OrdemServicoUpdate,
    OSEquipamentoUpdate,
    OSItemCreate,
    OSItemUpdate,
    OrdemServicoFinalizar,
    OrdemServicoCancelar,
    OrdemServicoQuery,
    OrdemServicoStats
)

from app.db.models.ordem_servico import OrdemServico as OSModel
from app.db.models.ordem_servico_equipamento import OrdemServicoEquipamento as OSEquipamentoModel
from app.db.models.ordem_servico_item import OrdemServicoItem as OSItemModel
from app.db.models.ordem_servico_pagamento import OrdemServicoPagamento as OSPagamentoModel

from app.db.crud import ordem_servico as os_crud
from app.db.crud import cliente as cliente_crud
from app.db.crud import funcionario as funcionario_crud
from app.db.crud import forma_pagamento as fp_crud

from app.core.enum import OrdemServicoItemTipo, OrdemServicoStatus
from app.helpers.set_pagination import _set_pagination


# ===========================================================================
# EXCEÇÕES REUTILIZÁVEIS
# ===========================================================================

os_not_found_exce = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Ordem de Serviço não encontrada"
)

cliente_not_found_exce = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Cliente não encontrado"
)

funcionario_not_found_exce = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Funcionário não encontrado"
)

item_not_found_exce = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Item não encontrado nesta OS"
)

forma_pagamento_not_found_exce = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Forma de pagamento não encontrada ou inativa"
)

os_fechada_exce = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Esta operação não é permitida para OS com status FINALIZADA ou CANCELADA"
)

os_nao_pode_reabrir_exce = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Apenas OS com status FINALIZADA ou CANCELADA podem ser reabertas"
)

pagamento_valor_invalido_exce = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="A soma dos pagamentos não confere com o valor total da OS"
)

status_invalido_exce = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Use os endpoints /finalizar ou /cancelar para essas transições de status"
)


# ===========================================================================
# HELPERS PRIVADOS
# ===========================================================================

def _get_os_or_raise(db: Session, numero_os: str) -> OSModel:
    """Busca OS pelo número ou lança 404."""
    os_in_db = os_crud.get_ordem_servico_by_numero_os(db, numero_os=numero_os)
    if not os_in_db:
        raise os_not_found_exce
    return os_in_db


def _assert_os_editavel(os_in_db: OSModel) -> None:
    """Lança 409 se a OS estiver FINALIZADA ou CANCELADA."""
    if os_in_db.status in (OrdemServicoStatus.FINALIZADA, OrdemServicoStatus.CANCELADA):
        raise os_fechada_exce


def _recalcular_valor_total_os(os_in_db: OSModel) -> None:
    """
    Recalcula valor_bruto e valor_total com base nos itens atuais da OS.
    Deve ser chamado sempre que itens ou desconto forem alterados.
    """
    valor_bruto = sum(item.valor_total for item in os_in_db.itens)
    os_in_db.valor_bruto = valor_bruto
    os_in_db.valor_total = max(0, valor_bruto - (os_in_db.desconto or 0) + (os_in_db.taxa_entrega or 0) + (os_in_db.acrescimo or 0))


# ===========================================================================
# CRIAÇÃO (CREATE)
# ===========================================================================

def create_ordem_servico(db: Session, os_to_create: OrdemServicoCreate) -> OSModel:
    """
    Cria uma nova OS com equipamento e itens em uma única transação.

    Valida: cliente existe, funcionário existe (se informado).
    Gera: número sequencial, valor_bruto e valor_total.
    """
    cliente_in_db = cliente_crud.get_cliente_by_id(db, cliente_id=os_to_create.cliente_id)
    if not cliente_in_db:
        raise cliente_not_found_exce

    funcionario_in_db = None
    if os_to_create.funcionario_id:
        funcionario_in_db = funcionario_crud.get_funcionario_by_id(db, funcionario_id=os_to_create.funcionario_id)
        if not funcionario_in_db:
            raise funcionario_not_found_exce

    next_number = os_crud.get_next_numero(db)
    valor_bruto_os = 0
    itens_model = []

    for item in os_to_create.itens:
        valor_item = item.quantidade * item.valor_unitario
        valor_bruto_os += valor_item
        item_data = item.model_dump(exclude={"item_id"}, exclude_unset=True)
        itens_model.append(OSItemModel(
            **item_data,
            produto_id=item.item_id if item.item_id and item.tipo == OrdemServicoItemTipo.PRODUTO else None,
            servico_id=item.item_id if item.item_id and item.tipo == OrdemServicoItemTipo.SERVICO else None,
            valor_total=valor_item
        ))

    desconto = os_to_create.desconto or 0
    valor_total_os = max(0, valor_bruto_os - desconto)

    equipamento_data = os_to_create.equipamento.model_dump(exclude_unset=True)
    equipamento_to_db = OSEquipamentoModel(**equipamento_data, cliente=cliente_in_db)

    os_data = os_to_create.model_dump(
        exclude={"cliente_id", "itens", "equipamento", "valor_bruto"},
        exclude_unset=True
    )
    os_to_db = OSModel(
        **os_data,
        status=OrdemServicoStatus.ABERTA,
        valor_total=valor_total_os,
        valor_bruto=valor_bruto_os,
        numero_os=next_number,
        equipamento=equipamento_to_db,
        itens=itens_model,
        funcionario=funcionario_in_db,
    )

    return os_crud.create_ordem_servico(db, os_to_add=os_to_db)


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


def get_ordem_servico_stats(db: Session) -> OrdemServicoStats:
    """Retorna estatísticas agregadas das OS."""
    return os_crud.get_ordem_servico_stats(db)


# ===========================================================================
# ATUALIZAÇÃO (UPDATE)
# ===========================================================================

def update_ordem_servico(db: Session, numero_os: str, data: OrdemServicoUpdate) -> OSModel:
    """
    Atualiza campos gerais de uma OS.

    Restrições:
    - OS FINALIZADA ou CANCELADA não pode ser editada.
    - Transições para FINALIZADA e CANCELADA são bloqueadas (use /finalizar ou /cancelar).
    - Se desconto mudar, valor_total é recalculado automaticamente.
    - Se funcionario_id mudar, o funcionário é validado no banco.
    """
    os_in_db = _get_os_or_raise(db, numero_os)
    _assert_os_editavel(os_in_db)

    update_data = data.model_dump(exclude_unset=True)

    # Bloqueia transições que têm endpoints próprios
    new_status = update_data.get("status")
    if new_status in (OrdemServicoStatus.FINALIZADA, OrdemServicoStatus.CANCELADA):
        raise status_invalido_exce

    # Valida novo funcionário se informado
    novo_funcionario_id = update_data.pop("funcionario_id", None)
    if novo_funcionario_id is not None:
        funcionario_in_db = funcionario_crud.get_funcionario_by_id(db, funcionario_id=novo_funcionario_id)
        if not funcionario_in_db:
            raise funcionario_not_found_exce
        os_in_db.funcionario = funcionario_in_db

    # Aplica os demais campos
    for key, value in update_data.items():
        setattr(os_in_db, key, value)

    # Recalcula total se desconto foi alterado
    if "desconto" in update_data:
        _recalcular_valor_total_os(os_in_db)

    return os_crud.update_ordem_servico(db, os_to_update=os_in_db)


def update_equipamento_os(db: Session, numero_os: str, data: OSEquipamentoUpdate) -> OSModel:
    """
    Atualiza informações do equipamento de uma OS.

    Permite também trocar o cliente proprietário via cliente_id.
    Restrição: OS FINALIZADA ou CANCELADA não pode ser editada.
    """
    os_in_db = _get_os_or_raise(db, numero_os)
    _assert_os_editavel(os_in_db)

    equipamento = os_in_db.equipamento
    update_data = data.model_dump(exclude_unset=True)

    # Valida e troca o cliente se solicitado
    novo_cliente_id = update_data.pop("cliente_id", None)
    if novo_cliente_id is not None:
        cliente_in_db = cliente_crud.get_cliente_by_id(db, cliente_id=novo_cliente_id)
        if not cliente_in_db:
            raise cliente_not_found_exce
        equipamento.cliente = cliente_in_db

    for key, value in update_data.items():
        setattr(equipamento, key, value)

    return os_crud.update_ordem_servico(db, os_to_update=os_in_db)


# ===========================================================================
# ITENS (CREATE / UPDATE / DELETE)
# ===========================================================================

def add_item_to_os(db: Session, numero_os: str, item_data: OSItemCreate) -> OSModel:
    """
    Adiciona um novo item (produto ou serviço) a uma OS existente.

    Recalcula valor_bruto e valor_total após a inserção.
    Restrição: OS FINALIZADA ou CANCELADA não pode receber novos itens.
    """
    os_in_db = _get_os_or_raise(db, numero_os)
    _assert_os_editavel(os_in_db)

    valor_item = item_data.quantidade * item_data.valor_unitario
    item_dict = item_data.model_dump(exclude={"item_id"}, exclude_unset=True)

    novo_item = OSItemModel(
        **item_dict,
        ordem_servico_id=os_in_db.id,
        produto_id=item_data.item_id if item_data.item_id and item_data.tipo == OrdemServicoItemTipo.PRODUTO else None,
        servico_id=item_data.item_id if item_data.item_id and item_data.tipo == OrdemServicoItemTipo.SERVICO else None,
        valor_total=valor_item,
    )

    os_crud.create_os_item(db, item_to_add=novo_item)
    db.refresh(os_in_db)  # Recarrega a lista de itens atualizada
    _recalcular_valor_total_os(os_in_db)

    return os_crud.update_ordem_servico(db, os_to_update=os_in_db)


def update_item_os(db: Session, numero_os: str, item_id: int, data: OSItemUpdate) -> OSModel:
    """
    Atualiza um item de OS.

    Verifica que o item pertence à OS informada antes de atualizar.
    Recalcula valor_bruto e valor_total após a atualização.
    """
    os_in_db = _get_os_or_raise(db, numero_os)
    _assert_os_editavel(os_in_db)

    item_in_db = os_crud.get_os_item_by_id(db, item_id=item_id)
    if not item_in_db or item_in_db.ordem_servico_id != os_in_db.id:
        raise item_not_found_exce

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item_in_db, key, value)

    # Recalcula valor_total do item se quantidade ou valor_unitario mudarem
    if "quantidade" in update_data or "valor_unitario" in update_data:
        item_in_db.valor_total = item_in_db.quantidade * item_in_db.valor_unitario

    os_crud.update_os_item(db, item_to_update=item_in_db)
    db.refresh(os_in_db)
    _recalcular_valor_total_os(os_in_db)

    return os_crud.update_ordem_servico(db, os_to_update=os_in_db)


def remove_item_from_os(db: Session, numero_os: str, item_id: int) -> None:
    """
    Remove um item de uma OS.

    Verifica que o item pertence à OS informada.
    Recalcula valor_bruto e valor_total após a remoção.
    Restrição: OS FINALIZADA ou CANCELADA não pode ter itens removidos.
    """
    os_in_db = _get_os_or_raise(db, numero_os)
    _assert_os_editavel(os_in_db)

    item_in_db = os_crud.get_os_item_by_id(db, item_id=item_id)
    if not item_in_db or item_in_db.ordem_servico_id != os_in_db.id:
        raise item_not_found_exce

    os_crud.delete_os_item(db, item_to_delete=item_in_db)
    db.refresh(os_in_db)
    _recalcular_valor_total_os(os_in_db)

    os_crud.update_ordem_servico(db, os_to_update=os_in_db)


# ===========================================================================
# AÇÕES DE STATUS
# ===========================================================================

def finalizar_ordem_servico(db: Session, numero_os: str, data: OrdemServicoFinalizar) -> OSModel:
    """
    Finaliza uma OS registrando a solução e os pagamentos.

    Regras de negócio:
    1. OS não pode estar FINALIZADA ou CANCELADA.
    2. Se desconto for informado, recalcula valor_total antes da validação.
    3. A soma dos pagamentos deve ser exatamente igual ao valor_total.
    4. Cada forma_pagamento_id deve existir e estar ativa no catálogo.
    5. Status → FINALIZADA, data_finalizacao → now().
    """
    os_in_db = _get_os_or_raise(db, numero_os)
    _assert_os_editavel(os_in_db)

    # Aplica campos financeiros se informados
    if data.desconto is not None:
        os_in_db.desconto = data.desconto
    if data.valor_entrada is not None:
        os_in_db.valor_entrada = data.valor_entrada
    if data.taxa_entrega is not None:
        os_in_db.taxa_entrega = data.taxa_entrega
    if data.acrescimo is not None:
        os_in_db.acrescimo = data.acrescimo

    # Recalcula valor_total com todos os campos financeiros atualizados
    _recalcular_valor_total_os(os_in_db)

    # Valida valor total dos pagamentos (pagamentos + entrada = valor_total)
    total_pagamentos = sum(p.valor for p in data.pagamentos)
    valor_entrada = os_in_db.valor_entrada or 0
    if (total_pagamentos + valor_entrada) != os_in_db.valor_total:
        raise pagamento_valor_invalido_exce

    # Valida e cria cada pagamento
    for pagamento_data in data.pagamentos:
        forma_pagamento = fp_crud.get_forma_pagamento_by_id(db, fp_id=pagamento_data.forma_pagamento_id)
        if not forma_pagamento or not forma_pagamento.ativo:
            raise forma_pagamento_not_found_exce

        pagamento = OSPagamentoModel(
            ordem_servico_id=os_in_db.id,
            forma_pagamento_id=pagamento_data.forma_pagamento_id,
            valor=pagamento_data.valor,
            parcelas=pagamento_data.parcelas,
            bandeira_cartao=pagamento_data.bandeira_cartao,
            detalhes=pagamento_data.detalhes,
        )
        os_crud.create_os_pagamento(db, pagamento_to_add=pagamento)

    # Aplica finalização
    os_in_db.solucao = data.solucao
    os_in_db.status = OrdemServicoStatus.FINALIZADA
    os_in_db.data_finalizacao = datetime.now()

    if data.observacoes:
        os_in_db.observacoes = data.observacoes

    return os_crud.update_ordem_servico(db, os_to_update=os_in_db)


def cancelar_ordem_servico(db: Session, numero_os: str, data: OrdemServicoCancelar) -> OSModel:
    """
    Cancela uma OS.

    O motivo, se informado, é acrescentado ao campo observações.
    Restrição: OS já CANCELADA não pode ser cancelada novamente.
    """
    os_in_db = _get_os_or_raise(db, numero_os)

    if os_in_db.status == OrdemServicoStatus.CANCELADA:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta OS já está cancelada"
        )

    os_in_db.status = OrdemServicoStatus.CANCELADA

    if data.motivo:
        obs_atual = os_in_db.observacoes or ""
        os_in_db.observacoes = f"{obs_atual}\n[CANCELAMENTO] {data.motivo}".strip()

    return os_crud.update_ordem_servico(db, os_to_update=os_in_db)


def reabrir_ordem_servico(db: Session, numero_os: str) -> OSModel:
    """
    Reabre uma OS FINALIZADA ou CANCELADA.

    Limpa: status → EM_ANDAMENTO, data_finalizacao → None, solucao → None.
    Remove os pagamentos existentes (necessário pois os valores podem ser renegociados).
    """
    os_in_db = _get_os_or_raise(db, numero_os)

    if os_in_db.status not in (OrdemServicoStatus.FINALIZADA, OrdemServicoStatus.CANCELADA):
        raise os_nao_pode_reabrir_exce

    # Remove pagamentos existentes (cascade via relacionamento SQLAlchemy)
    os_in_db.pagamentos = []

    os_in_db.status = OrdemServicoStatus.EM_ANDAMENTO
    os_in_db.data_finalizacao = None
    os_in_db.solucao = None

    return os_crud.update_ordem_servico(db, os_to_update=os_in_db)
