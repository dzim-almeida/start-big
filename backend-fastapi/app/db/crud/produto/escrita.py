# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/produto/escrita.py
# DESCRICAO: Produtos (banco) - criar e atualizar.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from app.db.models.produto import Produto as ProdutoModel


# ===========================================================================
# ESCRITA (CREATE / UPDATE)
# ===========================================================================

def create_produto(db: Session, produto_to_add: ProdutoModel) -> ProdutoModel:
    """Adiciona e persiste um novo produto (cascade para estoque)."""
    db.add(produto_to_add)
    db.flush()
    db.refresh(produto_to_add)
    return produto_to_add


def update_produto(db: Session, produto_to_update: ProdutoModel) -> ProdutoModel:
    """Persiste alterações em um produto rastreado pela sessão."""
    db.flush()
    db.refresh(produto_to_update)
    return produto_to_update
