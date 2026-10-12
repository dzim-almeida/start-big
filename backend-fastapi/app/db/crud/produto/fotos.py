# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/produto/fotos.py
# DESCRICAO: Produtos (banco) - fotos.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from typing import Optional
from app.db.models.produto_fotos import ProdutoFoto as ProdutoFotoModel


def get_produto_image_by_id(db: Session, image_id: int) -> ProdutoFotoModel:
    stmt = select(ProdutoFotoModel).where(ProdutoFotoModel.id == image_id)
    return db.scalars(stmt).first()


def get_produto_principal_image(db: Session, produto_id: int) -> Optional[ProdutoFotoModel]:
    stmt = select(ProdutoFotoModel).where(
        and_(
            ProdutoFotoModel.produto_id == produto_id,
            ProdutoFotoModel.principal == True
        )
    )
    return db.scalars(stmt).first()


def create_produto_image(db: Session, image_to_add: ProdutoFotoModel) -> ProdutoFotoModel:
    db.add(image_to_add)
    db.flush()
    db.refresh(image_to_add)
    return image_to_add


# ===========================================================================
# DELEÇÃO (DELETE)
# ===========================================================================

def delete_produto_image(db: Session, image_to_delete: ProdutoFotoModel) -> ProdutoFotoModel:
    db.delete(image_to_delete)
    db.flush()
