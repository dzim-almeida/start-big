from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.venda import Venda
from app.db.models.venda_produto import ProdutoVenda
from app.schemas.vendas import VendaCreate, VendaUpdate, ProdutoVendaCreate, ProdutoVendaUpdate, AddProdutoVendaRead

from app.services.cliente import cliente_exists
from app.services.funcionario import funcionario_exists

from app.db.crud import venda as venda_crud
from app.db.crud import venda as venda_crud

from app.core.enum import VendaStatus, TipoProdutoVenda

_not_found_exception = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Venda não encontrada"
)

_not_found_exception_prd = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Produto não encontrado"
)

_bad_request_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Requisição inválida"
)

def create_sale(db: Session, sale: VendaCreate) -> Venda:

    # Valida existência de cliente e funcionário
    cliente_exists(db, sale.cliente_id)
    funcionario_exists(db, sale.funcionario_id)

    sale_data = Venda(
        **sale.model_dump(exclude_unset=True),
        status=VendaStatus.RASCUNHO
    )

    return venda_crud.create_sale(db, sale_data=sale_data)

def update_sale(db: Session, sale_id: int, update_data: VendaUpdate) -> Venda:

    sale_in_db = venda_crud.get_sale_by_id(db, sale_id=sale_id)
    if not sale_in_db:
        raise _not_found_exception

    data_to_update = update_data.model_dump(exclude_unset=True)

    if "cliente_id" in data_to_update:
        cliente_exists(db, data_to_update["cliente_id"])

    if "funcionario_id" in data_to_update:
        funcionario_exists(db, data_to_update["funcionario_id"])

    if "entrega" in data_to_update:
        sale_in_db.entrega = data_to_update["entrega"]

    if "desconto" in data_to_update:
        total_in_db = sale_in_db.total or 0 + sale_in_db.entrega or 0
        descontos = data_to_update["desconto"] or 0 + sale_in_db.adiantamento or 0
        if descontos > total_in_db:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O desconto não pode ser maior que o total da venda"
            )
        sale_in_db.desconto = data_to_update["desconto"]

    if "adiantamento" in data_to_update:
        total_in_db = sale_in_db.total or 0 + sale_in_db.entrega or 0
        descontos = data_to_update["adiantamento"] or 0 + sale_in_db.desconto or 0
        if descontos > total_in_db:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O adiantamento não pode ser maior que o total da venda"
            )
        sale_in_db.adiantamento = data_to_update["adiantamento"]

    if "observacao" in data_to_update:
        sale_in_db.observacao = data_to_update["observacao"]

    return venda_crud.update_sale(db, sale_in_db)

def add_item_to_sale(db: Session, sale_id: int, item_data: ProdutoVendaCreate) -> AddProdutoVendaRead:
    print("Adicionando item à venda")
    sale_in_db = venda_crud.get_sale_by_id(db, sale_id=sale_id)
    if not sale_in_db:
        raise _not_found_exception
    
    print("Venda encontrada:", sale_in_db)
    
    data_to_add = item_data.model_dump(exclude_unset=True)

    print("Dados do item a adicionar:", data_to_add)
    
    if "produto_id" in data_to_add and data_to_add["tipo_produto"] == TipoProdutoVenda.AVULSO:
        raise _bad_request_exception
    
    if data_to_add["tipo_produto"] == TipoProdutoVenda.AVULSO and "descricao_avulsa" not in data_to_add:
        raise _bad_request_exception
    
    print("Validação do tipo de produto passou")
    
    quantidade = data_to_add.get("quantidade", 0)
    valor_unitario = data_to_add.get("valor_unitario", 0)
    desconto = data_to_add.get("desconto", 0)

    print(f"Quantidade: {quantidade}, Valor Unitário: {valor_unitario}, Desconto: {desconto}")

    if desconto > quantidade * valor_unitario:
        raise _bad_request_exception
    
    print("Validação do desconto passou")

    subtotal = quantidade * valor_unitario - desconto

    product_data = ProdutoVenda(
        **data_to_add,
        venda_id=sale_id,
        subtotal=subtotal
    )

    print("Criando ProdutoVenda com os dados:", product_data)

    product_in_db = venda_crud.add_product_to_sale(db, product_data)

    f_subtotal = sale_in_db.subtotal + subtotal
    f_descont = sale_in_db.desconto + desconto
    f_total = sale_in_db.total + subtotal - desconto

    sale_in_db.subtotal = f_subtotal
    sale_in_db.desconto = f_descont
    sale_in_db.total = f_total

    sale_in_db = venda_crud.update_sale(db, sale_in_db)

    finance_summary = {
        "subtotal": f_subtotal,
        "desconto": f_descont,
        "total": f_total
    }

    print("Resumo financeiro atualizado:", finance_summary)

    return AddProdutoVendaRead(
        resumo_financeiro=finance_summary,
        produto_adicionado=product_in_db.__dict__,
    )

def update_item_in_sale(db: Session, sale_id: int, item_id: int, item_update: ProdutoVendaUpdate) -> AddProdutoVendaRead:

    sale_in_db = venda_crud.get_sale_by_id(db, sale_id=sale_id)
    if not sale_in_db:
        raise _not_found_exception
    
    item_in_db = venda_crud.get_product_by_id(db, item_id=item_id)
    if not item_in_db or item_in_db.venda_id != sale_id:
        raise _not_found_exception_prd
    
    data_to_update = item_update.model_dump(exclude_unset=True)

    prev_quantidade = item_in_db.quantidade or 0
    prev_valor_unitario = item_in_db.valor_unitario or 0
    prev_desconto = item_in_db.desconto or 0

    quantidade = data_to_update["quantidade"] or item_in_db.quantidade or 0
    preco_unitario = data_to_update["valor_unitario"] or item_in_db.valor_unitario or 0
    desconto = data_to_update["desconto"] or item_in_db.desconto or 0

    if item_in_db.tipo_produto == TipoProdutoVenda.AVULSO and "produto_id" in data_to_update:
        raise _bad_request_exception
    
    subtotal = quantidade * preco_unitario - desconto
    
    if "desconto" in data_to_update:
        if subtotal < 0:
            raise _bad_request_exception
        
    item_in_db.quantidade = quantidade
    item_in_db.valor_unitario = preco_unitario
    item_in_db.desconto = desconto
    item_in_db.subtotal = subtotal

    item_in_db = venda_crud.update_product_in_sale(db, item_in_db)

    dif_subtotal = subtotal - (prev_quantidade * prev_valor_unitario - prev_desconto)
    dif_desconto = desconto - prev_desconto
    dif_total = dif_subtotal - dif_desconto

    sale_in_db.subtotal = (sale_in_db.subtotal or 0) + dif_subtotal
    sale_in_db.desconto = (sale_in_db.desconto or 0) + dif_desconto
    sale_in_db.total = (sale_in_db.total or 0) + dif_total
    sale_in_db = venda_crud.update_sale(db, sale_in_db)

    return AddProdutoVendaRead(
        produto_adicionado=item_in_db.__dict__,
        resumo_financeiro={
            "subtotal": sale_in_db.subtotal,
            "desconto": sale_in_db.desconto,
            "total": sale_in_db.total
        }
    )
    
def remove_item_from_sale(db: Session, sale_id: int, item_id: int) -> None:
    sale_in_db = venda_crud.get_sale_by_id(db, sale_id=sale_id)
    if not sale_in_db:
        raise _not_found_exception
    
    item_in_db = venda_crud.get_product_by_id(db, item_id=item_id)
    if not item_in_db or item_in_db.venda_id != sale_id:
        raise _not_found_exception_prd

    f_subtotal = sale_in_db.subtotal - item_in_db.subtotal
    f_desconto = sale_in_db.desconto - item_in_db.desconto
    f_total = sale_in_db.total - item_in_db.subtotal + item_in_db.desconto

    sale_in_db.subtotal = f_subtotal
    sale_in_db.desconto = f_desconto
    sale_in_db.total = f_total

    venda_crud.remove_product_from_sale(db, item_in_db)
    venda_crud.update_sale(db, sale_in_db)
    

    
