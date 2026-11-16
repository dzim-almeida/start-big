# ---------------------------------------------------------------------------
# ARQUIVO: services/fornecedor/consultas.py
# DESCRICAO: Fornecedor - busca.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from typing import Sequence, Optional
from app.db.models.fornecedor import Fornecedor as FornecedorModel
from app.db.crud import fornecedor as fornecedor_crud


# =========================
# Serviço: Buscar Fornecedores
# =========================
def get_fornecedor_by_search(db: Session, search: Optional[str]) -> Sequence[FornecedorModel]:
    """
    Busca fornecedores ativos por critério de busca (nome, fantasia ou CNPJ).

    Args:
        db (Session): Sessão de banco de dados ativa.
        search (str | None): Termo de busca opcional (nome, cnpj, ie).

    Returns:
        Sequence[FornecedorModel]: Lista de objetos FornecedorModel encontrados.
    """
    return fornecedor_crud.get_fornecedor_by_search(db, search)
