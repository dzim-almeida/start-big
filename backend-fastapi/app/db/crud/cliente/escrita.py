# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/cliente/escrita.py
# DESCRICAO: Clientes - criar, atualizar e desativar.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session

from app.db.models.cliente import Cliente as ClienteModel


# ===========================================================================
# ESCRITA (CREATE / UPDATE / DESATIVAR 'DELETE')
# ===========================================================================

def create_cliente(db: Session, cliente_to_add: ClienteModel) -> ClienteModel:
    """Adiciona e persiste um novo cliente (PF ou PJ) no banco."""
    db.add(cliente_to_add)
    db.flush()
    db.refresh(cliente_to_add)
    return cliente_to_add


def update_cliente(db: Session, cliente_to_update: ClienteModel) -> ClienteModel:
    """Atualiza o estado de um cliente já anexado à sessão."""
    db.flush()
    db.refresh(cliente_to_update)
    return cliente_to_update


def deactivate_cliente(db: Session, cliente: ClienteModel) -> None:
    """Realiza a exclusão lógica do cliente (inativação)."""
    cliente.ativo = False
    db.flush()
