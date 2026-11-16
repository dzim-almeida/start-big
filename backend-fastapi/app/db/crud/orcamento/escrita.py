# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/orcamento/escrita.py
# DESCRICAO: Orcamento (crud) - criar, atualizar e apagar orcamento e itens.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from app.db.models.orcamento import Orcamento
from app.db.models.orcamento_produto import OrcamentoProduto


def create_orcamento(db: Session, orcamento_data: Orcamento) -> Orcamento:
    db.add(orcamento_data)
    db.flush()
    db.refresh(orcamento_data)
    return orcamento_data


def add_product_to_orcamento(db: Session, product_data: OrcamentoProduto) -> OrcamentoProduto:
    db.add(product_data)
    db.flush()
    db.refresh(product_data)
    return product_data


def update_orcamento(db: Session, orcamento: Orcamento) -> Orcamento:
    db.flush()
    db.refresh(orcamento)
    return orcamento


def update_product_in_orcamento(db: Session, product: OrcamentoProduto) -> OrcamentoProduto:
    db.flush()
    db.refresh(product)
    return product


def remove_product_from_orcamento(db: Session, product: OrcamentoProduto) -> None:
    db.delete(product)
    db.flush()


def delete_orcamento(db: Session, orcamento: Orcamento) -> None:
    db.delete(orcamento)
    db.flush()
