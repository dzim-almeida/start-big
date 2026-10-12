# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/empresa/escrita.py
# DESCRICAO: Empresa (banco) - criar e atualizar.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session

from app.db.models.empresa import Empresa as EmpresaModel


# ===========================================================================
# ESCRITA (CREATE)
# ===========================================================================

def create_empresa(db: Session, empresa_to_add: EmpresaModel) -> EmpresaModel:
    """
    Persiste a empresa no banco de dados.

    Args:
        db (Session): Sessão de banco de dados ativa.
        empresa_to_add (EmpresaModel): O objeto ORM de empresa a ser adicionado.

    Returns:
        EmpresaModel: O objeto EmpresaModel recém-criado, após refresh (com ID populado).
    """
    db.add(empresa_to_add)
    db.flush()
    db.refresh(empresa_to_add)
    return empresa_to_add


def update_empresa(db: Session, empresa_to_update: EmpresaModel) -> EmpresaModel:
    db.flush()
    db.refresh(empresa_to_update)
    return empresa_to_update
