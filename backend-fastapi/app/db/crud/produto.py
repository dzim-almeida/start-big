# ---------------------------------------------------------------------------
# ARQUIVO: crud/produto.py
# MÓDULO: Acesso a Dados (Repository)
# DESCRIÇÃO: Executa queries SQL via SQLAlchemy para Produtos.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from sqlalchemy import select, or_, and_
from typing import Sequence, Optional

from app.db.models.produto import Produto as ProdutoModel
from app.db.models.produto_fotos import ProdutoFoto as ProdutoFotoModel

# ===========================================================================
# LEITURA (READ)
# ===========================================================================

def get_produto_by_search(db: Session, search: str) -> Sequence[ProdutoModel]:
    """
    Busca produtos ativos por correspondência parcial de Nome ou início do Código.
    
    Args:
        search (str): Termo de busca.
        
    Returns:
        Sequence[ProdutoModel]: Lista de produtos encontrados.
    """
    if not search:
        stmt = select(ProdutoModel)
    else:
        conditions = or_(
            ProdutoModel.nome.ilike(f"{search}%"),
            ProdutoModel.codigo_produto.startswith(search)
        )
        
        stmt = select(ProdutoModel).where(
            and_(
                conditions
            )
        )
    
    return db.scalars(stmt).all()

def get_produto_by_id(db: Session, produto_id: int) -> Optional[ProdutoModel]:
    """Busca produto pela chave primária (ID)."""
    stmt = select(ProdutoModel).where(ProdutoModel.id == produto_id)
    return db.scalars(stmt).first()

def get_produto_by_code(db: Session, produto_code: str) -> Optional[ProdutoModel]:
    """Busca produto pelo código único (SKU)."""
    stmt = select(ProdutoModel).where(
        and_(
            ProdutoModel.codigo_produto == produto_code,
            ProdutoModel.ativo == True
        )
    )
    return db.scalars(stmt).first()

def get_produto_image_by_id(db: Session, image_id: int) -> ProdutoFotoModel:
    stmt = select(ProdutoFotoModel).where(ProdutoFotoModel.id == image_id)
    return db.scalars(stmt).first()

# ===========================================================================
# ESCRITA (CREATE / UPDATE)
# ===========================================================================

def create_produto(db: Session, produto_to_add: ProdutoModel) -> ProdutoModel:
    """Adiciona e persiste um novo produto (cascade para estoque)."""
    db.add(produto_to_add)
    db.flush()
    db.refresh(produto_to_add)
    return produto_to_add

def create_produto_image(db: Session, image_to_add: ProdutoFotoModel) -> ProdutoFotoModel:
    db.add(image_to_add)
    db.flush()
    db.refresh(image_to_add)
    return image_to_add

def update_produto(db: Session, produto_to_update: ProdutoModel) -> ProdutoModel:
    """Persiste alterações em um produto rastreado pela sessão."""
    db.flush()
    db.refresh(produto_to_update)
    return produto_to_update

# ===========================================================================
# DELEÇÃO (DELETE)
# ===========================================================================

def delete_produto_image(db: Session, image_to_delete: ProdutoFotoModel) -> ProdutoFotoModel:
    db.delete(image_to_delete)
    db.flush()