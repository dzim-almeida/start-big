# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/fornecedor/escrita.py
# DESCRICAO: Fornecedor (crud) - criar e atualizar.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from app.db.models.fornecedor import Fornecedor as FornecedorModel


def create_fornecedor(db: Session, fornecedor_to_add: FornecedorModel) -> FornecedorModel:
    """
    Adiciona um novo fornecedor (e seus endereços associados em cascata)
    ao banco de dados.
    """
    db.add(fornecedor_to_add)
    db.flush()
    db.refresh(fornecedor_to_add)
    return fornecedor_to_add


def update_fornecedor(db: Session, fornecedor_to_update: FornecedorModel) -> FornecedorModel:
    """
    Persiste as alterações feitas em um objeto Fornecedor na sessão.
    """
    db.flush()
    db.refresh(fornecedor_to_update)
    return fornecedor_to_update
