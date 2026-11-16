# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/funcionario/escrita.py
# DESCRICAO: Funcionarios (banco) - criar e atualizar.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session

from app.db.models.funcionario import Funcionario as FuncionarioModel


# ===========================================================================
# ESCRITA (CREATE / UPDATE)
# ===========================================================================

def create_funcionario(db: Session, funcionario_to_add: FuncionarioModel) -> FuncionarioModel:
    """Persiste novo funcionário."""
    db.add(funcionario_to_add)
    db.flush()
    db.refresh(funcionario_to_add)
    return funcionario_to_add


def update_funcionario_in_db(db: Session, funcionario_to_update: FuncionarioModel) -> FuncionarioModel:
    """Persiste alterações."""
    db.flush()
    db.refresh(funcionario_to_update)
    return funcionario_to_update
