# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/empresa/consultas.py
# DESCRICAO: Empresa (banco) - buscar por id e a empresa atual.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional

from app.db.models.empresa import Empresa as EmpresaModel


# ===========================================================================
# LEITURA (READ)
# ===========================================================================

def get_empresa_by_id(db: Session, empresa_id: int) -> Optional[EmpresaModel]:
    """
    Busca uma empresa pela Chave Primária (ID).

    Args:
        db (Session): Sessão de banco de dados ativa.
        empresa_id (int): O ID da empresa (PK).

    Returns:
        Optional[EmpresaModel]: O objeto EmpresaModel se encontrado, ou None.
    """
    stmt = select(EmpresaModel).where(EmpresaModel.id == empresa_id)
    return db.scalars(stmt).first()


def get_empresa_atual(db: Session) -> Optional[EmpresaModel]:
    """
    Retorna a empresa da instalação (aplicação single-tenant: existe uma
    única empresa criada no setup). Usada para descobrir o segmento de negócio.

    Returns:
        Optional[EmpresaModel]: A primeira/única empresa, ou None se ainda não houver setup.
    """
    stmt = select(EmpresaModel).order_by(EmpresaModel.id).limit(1)
    return db.scalars(stmt).first()
