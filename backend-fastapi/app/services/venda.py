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

def _not_found_exeception(status_code: int = status.HTTP_404_NOT_FOUND, detail: str = "Não encontrado"):
    return HTTPException(
        status_code=status_code,
        detail=detail
    )

def _bad_request_exception(status_code: int = status.HTTP_400_BAD_REQUEST, detail: str = "Requisição inválida"):
    return HTTPException(
        status_code=status_code,
        detail=detail
    )

def _recalcular_subtotal_vendas(db: Session, sale: Venda) -> Venda:
    subtotal_sale = sum(item.subtotal for item in sale.itens)
    
    desconto = sale.desconto or 0
    adiantamento = sale.adiantamento or 0
    entrega = sale.entrega or 0

    if subtotal_sale + entrega < desconto + adiantamento:
        raise _bad_request_exception(detail="O desconto não pode ser maior que o total da venda")

    total_sale = subtotal_sale + entrega - desconto - adiantamento

    sale.subtotal = subtotal_sale
    sale.total = max(0, total_sale)

    return venda_crud.update_sale(db, sale)

def create_sale(db: Session, sale: VendaCreate) -> VendaRead:

    # Valida existência de cliente e funcionário
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
        cliente_exists(db, data_to_update["cliente_id"])

    if "funcionario_id" in data_to_update:
        funcionario_exists(db, data_to_update["funcionario_id"])

    if "entrega" in data_to_update:
        sale_in_db.entrega = data_to_update["entrega"]

    if "desconto" in data_to_update:
        total_in_db = (sale_in_db.subtotal or 0) + (sale_in_db.entrega or 0)
        descontos = (data_to_update["desconto"] or 0) + (sale_in_db.adiantamento or 0)
        if descontos > total_in_db:
            raise _bad_request_exception(detail="O desconto não pode ser maior que o total da venda")
        sale_in_db.desconto = data_to_update["desconto"]

    if "adiantamento" in data_to_update:
        total_in_db = (sale_in_db.subtotal or 0) + (sale_in_db.entrega or 0)
        descontos = (data_to_update["adiantamento"] or 0) + (sale_in_db.desconto or 0)
        if descontos > total_in_db:
            raise _bad_request_exception(detail="O adiantamento não pode ser maior que o total da venda")
        sale_in_db.adiantamento = data_to_update["adiantamento"]

    if "observacao" in data_to_update:
        sale_in_db.observacao = data_to_update["observacao"]

    return venda_crud.update_sale(db, sale_in_db)

def add_item_to_sale(db: Session, sale_id: int, item_data: ProdutoVendaCreate) -> tuple[Venda, ProdutoVenda]:
    sale_in_db = get_sale_by_id(db, sale_id=sale_id)
        
    data_to_add = item_data.model_dump(exclude_unset=True)
    
    if "produto_id" in data_to_add and data_to_add["tipo_produto"] == TipoProdutoVenda.AVULSO:
        raise _bad_request_exception(detail="Um produto avulso não pode estar cadastrado")
    
    if data_to_add["tipo_produto"] == TipoProdutoVenda.AVULSO and "descricao_avulsa" not in data_to_add:
        raise _bad_request_exception(detail="Um produto avulso deve ter descrição")
        
    quantidade = data_to_add.get("quantidade", 0)
    valor_unitario = data_to_add.get("valor_unitario", 0)
    desconto = data_to_add.get("desconto", 0)

    if desconto > quantidade * valor_unitario:
        raise _bad_request_exception(detail="O desconto não pode ser maior que o total do produto")
    
    subtotal = quantidade * valor_unitario - desconto

    product_data = ProdutoVenda(
        **data_to_add,
        venda_id=sale_id,
        subtotal=subtotal
    )

    product_in_db = venda_crud.add_product_to_sale(db, product_data)

    sale_in_db.itens.append(product_in_db)

    sale_in_db = _recalcular_subtotal_vendas(db, sale_in_db)

    return sale_in_db, product_in_db

def update_item_in_sale(db: Session, sale_id: int, item_id: int, item_update: ProdutoVendaUpdate) -> tuple[Venda, ProdutoVenda]:

    sale_in_db = get_sale_by_id(db, sale_id=sale_id)
    
    item_in_db = venda_crud.get_product_by_id(db, item_id=item_id)
    if not item_in_db or item_in_db.venda_id != sale_id:
        raise _not_found_exeception(detail="Produto não encontrado")
    
    data_to_update = item_update.model_dump(exclude_unset=True)

    quantidade = data_to_update.get("quantidade", item_in_db.quantidade or 0)
    preco_unitario = data_to_update.get("valor_unitario", item_in_db.valor_unitario or 0)
    desconto = data_to_update.get("desconto", item_in_db.desconto or 0)

    if item_in_db.tipo_produto == TipoProdutoVenda.AVULSO and "produto_id" in data_to_update:
        raise _bad_request_exception(detail="Um produto avulso não pode estar cadastrado")
    
    subtotal = quantidade * preco_unitario - desconto
    
    if "desconto" in data_to_update:
        if subtotal < 0:
            raise _bad_request_exception(detail="O desconto não pode ser maior que o valor total do produto")
        
    item_in_db.quantidade = quantidade
    item_in_db.valor_unitario = preco_unitario
    item_in_db.desconto = desconto
    item_in_db.subtotal = subtotal

    item_in_db = venda_crud.update_product_in_sale(db, item_in_db)
    
    sale_in_db = _recalcular_subtotal_vendas(db, sale_in_db)

    return sale_in_db, item_in_db
    
def remove_item_from_sale(db: Session, sale_id: int, item_id: int) -> None:
    sale_in_db = get_sale_by_id(db, sale_id=sale_id)
    
    item_in_db = venda_crud.get_product_by_id(db, item_id=item_id)
    if not item_in_db or item_in_db.venda_id != sale_id:
        raise _not_found_exeception(detail="Produto não encontrado")

    venda_crud.remove_product_from_sale(db, item_in_db)
    
    return _recalcular_subtotal_vendas(db, sale_in_db)

def finish_sale(db: Session, sale_id: int, payments: Sequence[PagamentoVendaCreate]):
    sale_in_db = get_sale_by_id(db, sale_id=sale_id)
    
    if sale_in_db.status != VendaStatus.RASCUNHO:
        raise _bad_request_exception(detail="Esta venda não pode ser finalizada")
    
    valid_payments_to_db = payments_valid(db, payments)
    
    total_payments = sum(payment.valor for payment in valid_payments_to_db)
    total_sale = sale_in_db.total or 0

    if total_payments != total_sale:
        raise _bad_request_exception(detail="Os pagamentos não conferem ao total da venda")
    
    products_in_db = sale_in_db.itens

    for product in products_in_db:
        if product.tipo_produto == TipoProdutoVenda.CADASTRADO:
            produto_service.decrease_product_in_stock(db, produto_id=product.produto_id, quantidade=product.quantidade, funcionario_id=sale_in_db.funcionario_id, venda_id=sale_in_db.id)
    
    sale_in_db.status = VendaStatus.FINALIZADA
    sale_in_db.pagamentos = valid_payments_to_db
    return venda_crud.update_sale(db, sale_in_db)

def payments_valid(db: Session, payments: Sequence[PagamentoVendaCreate]) -> Sequence[PagamentoVenda]:
    sale_payments: Sequence[PagamentoVenda] = []
    for payment in payments:
        payment_type = forma_pagamento_crud.get_forma_pagamento_by_id(db, payment.forma_pagamento_id)
        if not payment_type:
            raise _bad_request_exception(detail="O pagamento dev ser uma forma válida")
        if payment.parcelado and payment.qtd_parcelas is None:
            raise _bad_request_exception(detail="Pagamentos parcelados devem ter no mínimo 1 parcela")
        if not payment.parcelado and payment.qtd_parcelas is not None:
            raise _bad_request_exception(detail="Pagamentos a vista não deve ter parcelas")
        sale_payments.append(PagamentoVenda(**payment.__dict__))
    return sale_payments

def cancel_sale(db: Session, sale_id: int) -> Venda:
    sale_in_db = get_sale_by_id(db, sale_id=sale_id)
    
    if sale_in_db.status != VendaStatus.RASCUNHO:
        raise _bad_request_exception("Esta venda não pode ser cancelada")
    
    sale_in_db.status = VendaStatus.CANCELADA
    return venda_crud.update_sale(db, sale_in_db)

def reopen_sale(db: Session, sale_id: int) -> Venda:
    sale_in_db = get_sale_by_id(db, sale_id=sale_id)
    
    if sale_in_db.status == VendaStatus.RASCUNHO:
        raise _bad_request_exception(detail="Venda não pode ser reaberta")
    
    sale_in_db.status = VendaStatus.RASCUNHO
    return venda_crud.update_sale(db, sale_in_db)

def get_sale_by_id(db: Session, sale_id: int) -> Venda:
    sale_in_db = venda_crud.get_sale_by_id(db, sale_id=sale_id)
    if not sale_in_db:
        raise _not_found_exeception(detail="Venda não encontrada")
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
    

    
        
        
    
    

    
