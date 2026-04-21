from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Sequence

from app.db.models.venda import Venda
from app.db.models.venda_produto import ProdutoVenda
from app.db.models.venda_pagamento import PagamentoVenda
from app.schemas.vendas import VendaCreate, VendaSearchFilters, VendaUpdate, ProdutoVendaCreate, ProdutoVendaUpdate, PagamentoVendaCreate, VendaRead

from app.services.cliente import cliente_exists
from app.services.funcionario import funcionario_exists
from app.services import produto as produto_service

from app.db.crud import venda as venda_crud
from app.db.crud import forma_pagamento as forma_pagamento_crud

from app.core.enum import VendaStatus, TipoProdutoVenda

from app.helpers.set_pagination import _set_pagination
from app.helpers.exceptions import BadRequestException, NotFoundException

def _recalc_total_sale(db: Session, sale_in_db: Venda) -> Venda:

    if sale_in_db.total_bruto < sale_in_db.total_descontos:
        raise BadRequestException(detail="O desconto não pode ser maior que o total da venda")

    total_sale = sale_in_db.total_bruto - sale_in_db.total_descontos

    sale_in_db.subtotal = sale_in_db.total_bruto
    sale_in_db.total = max(0, total_sale)

    return venda_crud.update_sale(db, sale_in_db)

def _payments_valid(db: Session, payments: Sequence[PagamentoVendaCreate]) -> Sequence[PagamentoVenda]:
    sale_payments: Sequence[PagamentoVenda] = []
    for payment in payments:
        payment_type = forma_pagamento_crud.get_forma_pagamento_by_id(db, payment.forma_pagamento_id)
        if not payment_type:
            raise BadRequestException(detail="Pagamentos devem ser uma forma válida")
        if payment.parcelado and payment.qtd_parcelas is None:
            raise BadRequestException(detail="Pagamentos parcelados devem ter no mínimo 1 parcela")
        if not payment.parcelado and payment.qtd_parcelas is not None:
            raise BadRequestException(detail="Pagamentos a vista não deve ter parcelas")
        sale_payments.append(PagamentoVenda(**payment.model_dump()))
    return sale_payments

def create_sale(db: Session, sale: VendaCreate) -> VendaRead:

    # Valida existência de cliente (se informado) e funcionário
    if sale.cliente_id is not None:
        cliente_exists(db, sale.cliente_id)
    funcionario_exists(db, sale.funcionario_id)

    sale_data = Venda(
        **sale.model_dump(exclude_unset=True),
        status=VendaStatus.RASCUNHO
    )

    new_sale = venda_crud.create_sale(db, sale_data=sale_data)

    return VendaRead(
        id=new_sale.id,
        cliente_id=new_sale.cliente_id,
        funcionario_id=new_sale.funcionario_id,
    )

def update_sale(db: Session, sale_id: int, update_data: VendaUpdate) -> Venda:
    sale_in_db = get_sale_by_id(db, sale_id=sale_id)

    data_to_update = update_data.model_dump(exclude_unset=True)

    if "cliente_id" in data_to_update:
        customer_in_db = cliente_exists(db, data_to_update["cliente_id"])
        sale_in_db.cliente_id = customer_in_db.id

    if "funcionario_id" in data_to_update:
        funcionario_in_db = funcionario_exists(db, data_to_update["funcionario_id"])
        sale_in_db.funcionario_id = funcionario_in_db.id

    if "entrega" in data_to_update:
        sale_in_db.entrega = data_to_update["entrega"]

    if "desconto" in data_to_update:
        subtotal_in_db = (sale_in_db.total_bruto or 0)
        descontos = (data_to_update["desconto"] or 0) + (sale_in_db.adiantamento or 0)
        if descontos > subtotal_in_db:
            raise BadRequestException(detail="O desconto não pode ser maior que o total da venda")
        sale_in_db.desconto = data_to_update["desconto"]

    if "adiantamento" in data_to_update:
        subtotal_in_db = (sale_in_db.total_bruto or 0)
        descontos = (data_to_update["adiantamento"] or 0) + (sale_in_db.desconto or 0)
        if descontos > subtotal_in_db:
            raise BadRequestException(detail="O adiantamento não pode ser maior que o total da venda")
        sale_in_db.adiantamento = data_to_update["adiantamento"]

    if "observacao" in data_to_update:
        sale_in_db.observacao = data_to_update["observacao"]

    return venda_crud.update_sale(db, sale_in_db)

def add_item_to_sale(db: Session, sale_id: int, item_data: ProdutoVendaCreate) -> tuple[Venda, ProdutoVenda]:
    sale_in_db = get_sale_by_id(db, sale_id=sale_id)
    if not sale_in_db:
        raise NotFoundException(detail="Venda não encontrada")
    
    quantidade = item_data.quantidade
    valor_unitario = item_data.valor_unitario
    desconto = item_data.desconto

    if item_data.produto_id:
        if item_data.tipo_produto == TipoProdutoVenda.AVULSO:
            raise BadRequestException(detail="Um produto avulso não pode estar cadastrado")
        
        valor_unitario = produto_service.get_produto_value_by_id(db, produto_id=item_data.produto_id)
    
    if item_data.tipo_produto == TipoProdutoVenda.AVULSO and item_data.descricao_avulsa is None:
        raise BadRequestException(detail="Um produto avulso deve ter descrição")

    if desconto > quantidade * valor_unitario:
        raise BadRequestException(detail="O desconto não pode ser maior que o total do produto")
    
    subtotal = quantidade * valor_unitario - desconto

    product_data = ProdutoVenda(
        **item_data.model_dump(exclude={"valor_unitario"}),
        venda_id=sale_id,
        valor_unitario=valor_unitario,
        subtotal=subtotal
    )

    product_in_db = venda_crud.add_product_to_sale(db, product_data)

    sale_in_db = _recalc_total_sale(db, sale_in_db)

    return sale_in_db, product_in_db

def update_item_in_sale(db: Session, sale_id: int, item_id: int, item_update: ProdutoVendaUpdate) -> tuple[Venda, ProdutoVenda]:

    sale_in_db = get_sale_by_id(db, sale_id=sale_id)
    
    item_in_db = venda_crud.get_product_by_id(db, item_id=item_id)
    if not item_in_db or item_in_db.venda_id != sale_id:
        raise NotFoundException(detail="Produto não encontrado")
    
    if item_in_db.tipo_produto == TipoProdutoVenda.CADASTRADO:
        if item_update.descricao_avulsa is not None:
            raise BadRequestException(detail="Um produto cadastrado não pode ter descrição avulsa")
        if item_update.valor_unitario is not None:
            raise BadRequestException(detail="Um produto cadastrado não pode ter valor unitário definido manualmente")

    quantidade = item_update.quantidade or (item_in_db.quantidade or 0)
    preco_unitario = item_update.valor_unitario or (item_in_db.valor_unitario or 0)
    desconto = item_update.desconto or (item_in_db.desconto or 0)
    
    subtotal = quantidade * preco_unitario - desconto
    
    if subtotal < 0:
        raise BadRequestException(detail="O desconto não pode ser maior que o valor total do produto")
        
    item_in_db.descricao_avulsa = item_update.descricao_avulsa or item_in_db.descricao_avulsa
    item_in_db.quantidade = quantidade
    item_in_db.valor_unitario = preco_unitario
    item_in_db.desconto = desconto
    item_in_db.subtotal = subtotal

    item_in_db = venda_crud.update_product_in_sale(db, item_in_db)
    
    sale_in_db = _recalc_total_sale(db, sale_in_db)

    return sale_in_db, item_in_db
    
def remove_item_from_sale(db: Session, sale_id: int, item_id: int) -> None:
    sale_in_db = get_sale_by_id(db, sale_id=sale_id)
    
    item_in_db = venda_crud.get_product_by_id(db, item_id=item_id)
    if not item_in_db or item_in_db.venda_id != sale_id:
        raise NotFoundException(detail="Produto não encontrado")

    venda_crud.remove_product_from_sale(db, item_in_db)
    
    return _recalc_total_sale(db, sale_in_db)

def finish_sale(db: Session, sale_id: int, payments: Sequence[PagamentoVendaCreate]):
    sale_in_db = get_sale_by_id(db, sale_id=sale_id)
    
    if sale_in_db.status != VendaStatus.RASCUNHO:
        raise BadRequestException(detail="Esta venda não pode ser finalizada")
    
    valid_payments_to_db = _payments_valid(db, payments)
    
    total_payments = sum(payment.valor for payment in valid_payments_to_db)
    total_sale = sale_in_db.total or 0

    if total_payments != total_sale:
        raise BadRequestException(detail="Os pagamentos não conferem ao total da venda")
    
    products_in_db = sale_in_db.itens

    for product in products_in_db:
        if product.tipo_produto == TipoProdutoVenda.CADASTRADO:
            produto_service.decrease_product_in_stock(db, produto_id=product.produto_id, quantidade=product.quantidade, funcionario_id=sale_in_db.funcionario_id, venda_id=sale_in_db.id)
    
    sale_in_db.status = VendaStatus.FINALIZADA
    sale_in_db.pagamentos = valid_payments_to_db
    return venda_crud.update_sale(db, sale_in_db)

def cancel_sale(db: Session, sale_id: int) -> Venda:
    sale_in_db = get_sale_by_id(db, sale_id=sale_id)
    
    if sale_in_db.status != VendaStatus.RASCUNHO:
        raise BadRequestException("Esta venda não pode ser cancelada")
    
    sale_in_db.status = VendaStatus.CANCELADA
    return venda_crud.update_sale(db, sale_in_db)

def reopen_sale(db: Session, sale_id: int) -> Venda:
    sale_in_db = get_sale_by_id(db, sale_id=sale_id)
    
    if sale_in_db.status == VendaStatus.RASCUNHO:
        raise BadRequestException(detail="Venda não pode ser reaberta")
    
    sale_in_db.status = VendaStatus.RASCUNHO
    return venda_crud.update_sale(db, sale_in_db)

def get_sale_by_id(db: Session, sale_id: int) -> Venda:
    sale_in_db = venda_crud.get_sale_by_id(db, sale_id=sale_id)
    if not sale_in_db:
        raise NotFoundException(detail="Venda não encontrada")
    return sale_in_db

def get_sales(db: Session, filters: VendaSearchFilters, page: int, limit: int = 100) -> tuple[Sequence[Venda], int, int, dict]:
    skip = (page - 1) * limit

    filters_dict = filters.model_dump(exclude_unset=True)
    
    sales_in_db, total_sales = venda_crud.get_sales_by_search(
        db, filters=filters_dict, skip=skip, limit=limit
    )
    
    total_pages, links = _set_pagination(
        total_items=total_sales, filters=filters_dict, page=page, limit=limit
    )

    return sales_in_db, total_sales, total_pages, links
    

    
        
        
    
    

    
