# ---------------------------------------------------------------------------
# ARQUIVO: services/ordem_servico/itens.py
# DESCRICAO: Ordem de servico - incluir, editar e remover item.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from app.schemas.ordem_servico import (
    OSItemCreate,
    OSItemUpdate,
)
from app.db.models.ordem_servico import OrdemServico as OSModel
from app.db.models.ordem_servico_item import OrdemServicoItem as OSItemModel
from app.db.crud import ordem_servico as os_crud
from app.core.enum import (
    OrdemServicoItemTipo,
)
from app.services.ordem_servico.excecoes import item_not_found_exce
from app.services.ordem_servico.regras import _assert_item_coerente, _assert_item_nao_gerado_pela_fabrica, _assert_os_editavel, _get_os_or_raise, _recalcular_valor_total_os
from app.services.ordem_servico.regras_tipo import _assert_item_sem_origem


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

    valor_item = round(item_data.quantidade * item_data.valor_unitario)
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
    _assert_item_nao_gerado_pela_fabrica(item_in_db)
    _assert_item_sem_origem(item_in_db)            # item do orçamento técnico (08A, D18)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item_in_db, key, value)

    # Recalcula valor_total do item se quantidade ou valor_unitario mudarem
    if "quantidade" in update_data or "valor_unitario" in update_data:
        item_in_db.valor_total = round(item_in_db.quantidade * item_in_db.valor_unitario)

    # Visibilidade e valor precisam continuar coerentes DEPOIS do patch — os dois
    # campos podem vir em requisições separadas, e só aqui dá para ver o estado
    # final. Sem esta guarda, marcar uma peça como embutida sem zerar o valor
    # deixaria a via do cliente com linhas que não somam o total impresso.
    _assert_item_coerente(item_in_db)

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
    _assert_item_nao_gerado_pela_fabrica(item_in_db)
    _assert_item_sem_origem(item_in_db)            # item do orçamento técnico (08A, D18)

    os_crud.delete_os_item(db, item_to_delete=item_in_db)
    db.refresh(os_in_db)
    _recalcular_valor_total_os(os_in_db)

    os_crud.update_ordem_servico(db, os_to_update=os_in_db)
