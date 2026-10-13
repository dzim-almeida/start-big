# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/servico/escrita.py
# DESCRICAO: Servico (crud) - criar e atualizar.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from app.db.models.servico import Servico as ServicoModel


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
