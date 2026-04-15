from sqlalchemy.orm import Session, aliased
from sqlalchemy import select, func, or_, case, cast, String
from app.db.models.venda import Venda
from app.db.models.venda_produto import ProdutoVenda
from app.db.models.cliente import ClientePF, ClientePJ
from app.db.models.funcionario import Funcionario
from typing import Sequence

def create_sale(db: Session, sale_data: Venda) -> Venda:
    db.add(sale_data)
    db.flush()
    db.refresh(sale_data)
    return sale_data

def add_product_to_sale(db: Session, product_data: ProdutoVenda) -> ProdutoVenda:
    db.add(product_data)
    db.flush()
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
    db.flush()

def get_sales_by_search(
    db: Session,
    filters: dict,
    skip: int = 0,
    limit: int = 20,
) -> tuple[Sequence[Venda], int]:
    
    query = select(Venda)
    
    search = filters.get("search")
    if search:
        cliente_pj = aliased(ClientePJ)
        cliente_pf = aliased(ClientePF)

        query = (
            query
            .join(Funcionario, Funcionario.id == Venda.funcionario_id)
            .outerjoin(Venda.cliente)
            .outerjoin(cliente_pj, cliente_pj.id == Venda.cliente_id)
            .outerjoin(cliente_pf, cliente_pf.id == Venda.cliente_id)
        )

        like_search = f"%{search}%"
        query = query.where(
            or_(
                cast(Venda.id, String).startswith(like_search),
                cliente_pf.nome.ilike(like_search),
                cliente_pj.razao_social.ilike(like_search),
                cliente_pj.nome_fantasia.ilike(like_search),
                Funcionario.nome.ilike(like_search)
            )
        )

    status = filters.get("status")
    if status:
        query = query.where(Venda.status == status)

    count_stmt = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_stmt) or 0   

    stmt = query.order_by(Venda.id.desc()).offset(skip).limit(limit)
    sales = db.scalars(stmt).unique().all()

    return sales, total
