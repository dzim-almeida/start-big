from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models.venda import Venda
from app.db.models.venda_produto import ProdutoVenda

def create_sale(db: Session, sale_data: Venda) -> Venda:
    db.add(sale_data)
    db.commit()
    db.refresh(sale_data)
    return sale_data

def add_product_to_sale(db: Session, product_data: ProdutoVenda) -> ProdutoVenda:
    db.add(product_data)
    db.commit()
    db.refresh(product_data)
    return product_data

def get_sale_by_id(db: Session, sale_id: int) -> Venda:
    stmt = select(Venda).where(Venda.id == sale_id)
    return db.scalar(stmt)

def update_sale(db: Session, sale: Venda) -> Venda:
    db.flush()
    db.refresh(sale)
    return sale

def update_product_in_sale(db: Session, product: ProdutoVenda) -> ProdutoVenda:
    db.flush()
    db.refresh(product)
    return product

def get_product_by_id(db: Session, item_id: int) -> ProdutoVenda:
    stmt = select(ProdutoVenda).where(ProdutoVenda.id == item_id)
    return db.scalar(stmt)

def remove_product_from_sale(db: Session, product: ProdutoVenda) -> None:
    db.delete(product)