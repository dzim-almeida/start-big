# ---------------------------------------------------------------------------
# ARQUIVO: services/orcamento/cadastro.py
# DESCRICAO: Orcamento - criar, editar e apagar.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from app.db.models.orcamento import Orcamento
from app.schemas.orcamentos import OrcamentoCreate, OrcamentoUpdate
from app.services.funcionario import funcionario_exists
from app.db.crud import orcamento as orcamento_crud
from app.helpers.exceptions import BadRequestException
from app.services.orcamento.calculo import _apply_discount, _recalc_total_orcamento
from app.services.orcamento.consultas import get_orcamento_by_id


# ---------------------------------------------------------------------------
# CRUD Operations
# ---------------------------------------------------------------------------

def create_orcamento(db: Session, orcamento: OrcamentoCreate) -> Orcamento:
    funcionario_exists(db, orcamento.funcionario_id)

    orcamento_data = Orcamento(
        **orcamento.model_dump(exclude_unset=True),
    )

    return orcamento_crud.create_orcamento(db, orcamento_data=orcamento_data)


def update_orcamento(db: Session, orcamento_id: int, update_data: OrcamentoUpdate) -> Orcamento:
    orcamento_in_db = get_orcamento_by_id(db, orcamento_id=orcamento_id)
    if orcamento_in_db.convertido:
        raise BadRequestException(detail="Orcamento convertido nao pode ser editado")

    if update_data.funcionario_id:
        funcionario_in_db = funcionario_exists(db, update_data.funcionario_id)
        orcamento_in_db.funcionario_id = funcionario_in_db.id

    if update_data.entrega is not None:
        orcamento_in_db.entrega = update_data.entrega

    if update_data.desconto is not None:
        if update_data.desconto > orcamento_in_db.subtotal:
            raise BadRequestException(detail="O desconto nao pode ser maior que o total do orcamento")
        orcamento_in_db = _apply_discount(orcamento_in_db=orcamento_in_db, discount=update_data.desconto)

    if update_data.observacao is not None:
        orcamento_in_db.observacao = update_data.observacao

    return _recalc_total_orcamento(db, orcamento_in_db=orcamento_in_db)


def delete_orcamento(db: Session, orcamento_id: int) -> None:
    orcamento_in_db = get_orcamento_by_id(db, orcamento_id=orcamento_id)
    if orcamento_in_db.convertido:
        raise BadRequestException(detail="Orcamento convertido nao pode ser excluido")

    orcamento_crud.delete_orcamento(db, orcamento_in_db)
