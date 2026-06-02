from sqlalchemy.orm import Session
from typing import Sequence

from app.db.models.orcamento import Orcamento
from app.db.models.orcamento_produto import OrcamentoProduto
from app.db.models.venda import Venda
from app.db.models.venda_produto import ProdutoVenda
from app.schemas.orcamentos import (
    OrcamentoCreate, OrcamentoUpdate, OrcamentoProdutoCreate,
    OrcamentoProdutoUpdate, OrcamentoSearchFilters, OrcamentoStatusSummary,
    ConverterOrcamentoPayload,
)

from app.services.cliente import cliente_exists
from app.services.funcionario import funcionario_exists
from app.services import produto as produto_service

from app.db.crud import orcamento as orcamento_crud
from app.db.crud import venda as venda_crud

from app.core.enum import TipoProdutoVenda

from app.helpers.set_pagination import _set_pagination
from app.helpers.exceptions import BadRequestException, NotFoundException


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _recalc_total_orcamento(db: Session, orcamento_in_db: Orcamento) -> Orcamento:
    if orcamento_in_db.total_bruto < orcamento_in_db.descontos:
        raise BadRequestException(detail="O desconto nao pode ser maior que o total do orcamento")

    total = orcamento_in_db.total_bruto - orcamento_in_db.descontos

    orcamento_in_db.subtotal = orcamento_in_db.total_bruto
    orcamento_in_db.total = total

    return orcamento_crud.update_orcamento(db, orcamento_in_db)


def _apply_discount(orcamento_in_db: Orcamento, discount: int) -> Orcamento:
    discount_remaining = discount
    for index, item in enumerate(orcamento_in_db.itens):
        if index == len(orcamento_in_db.itens) - 1:
            item.desconto = discount_remaining
        else:
            item_discount = ((item.total * discount) // (orcamento_in_db.total or 1))
            item.desconto = item_discount
            discount_remaining -= item_discount
    return orcamento_in_db


# ---------------------------------------------------------------------------
# CRUD Operations
# ---------------------------------------------------------------------------

def create_orcamento(db: Session, orcamento: OrcamentoCreate) -> Orcamento:
    funcionario_exists(db, orcamento.funcionario_id)

    orcamento_data = Orcamento(
        **orcamento.model_dump(exclude_unset=True),
    )

    return orcamento_crud.create_orcamento(db, orcamento_data=orcamento_data)


def update_orcamento(db: Session, orcamento_id: int, update_data: OrcamentoUpdate) -> Orcamento:
    orcamento_in_db = get_orcamento_by_id(db, orcamento_id=orcamento_id)
    if orcamento_in_db.convertido:
        raise BadRequestException(detail="Orcamento convertido nao pode ser editado")

    if update_data.funcionario_id:
        funcionario_in_db = funcionario_exists(db, update_data.funcionario_id)
        orcamento_in_db.funcionario_id = funcionario_in_db.id

    if update_data.entrega is not None:
        orcamento_in_db.entrega = update_data.entrega

    if update_data.desconto is not None:
        if update_data.desconto > orcamento_in_db.subtotal:
            raise BadRequestException(detail="O desconto nao pode ser maior que o total do orcamento")
        orcamento_in_db = _apply_discount(orcamento_in_db=orcamento_in_db, discount=update_data.desconto)

    if update_data.observacao is not None:
        orcamento_in_db.observacao = update_data.observacao

    return _recalc_total_orcamento(db, orcamento_in_db=orcamento_in_db)


def add_item_to_orcamento(db: Session, orcamento_id: int, item_data: OrcamentoProdutoCreate) -> tuple[Orcamento, OrcamentoProduto]:
    orcamento_in_db = get_orcamento_by_id(db, orcamento_id=orcamento_id)
    if orcamento_in_db.convertido:
        raise BadRequestException(detail="Orcamento convertido nao pode ser editado")

    quantidade = item_data.quantidade
    valor_unitario = item_data.valor_unitario
    desconto = item_data.desconto

    if item_data.produto_id:
        if item_data.tipo_produto == TipoProdutoVenda.AVULSO:
            raise BadRequestException(detail="Um produto avulso nao pode estar cadastrado")

        product_in_db = produto_service.get_produto_by_id(db, produto_id=item_data.produto_id)
        if quantidade > product_in_db.estoque.quantidade:
            raise BadRequestException(detail=f"Quantidade em estoque insuficiente para o produto {product_in_db.nome}")

        valor_unitario = product_in_db.estoque.valor_varejo

    if item_data.tipo_produto == TipoProdutoVenda.AVULSO and item_data.descricao_avulsa is None:
        raise BadRequestException(detail="Um produto avulso deve ter descricao")

    if desconto > quantidade * valor_unitario:
        raise BadRequestException(detail="O desconto nao pode ser maior que o total do produto")

    subtotal = quantidade * valor_unitario - desconto

    product_data = OrcamentoProduto(
        **item_data.model_dump(exclude={"valor_unitario"}),
        orcamento_id=orcamento_id,
        valor_unitario=valor_unitario,
        subtotal=subtotal
    )

    product_in_db = orcamento_crud.add_product_to_orcamento(db, product_data)

    orcamento_in_db = _recalc_total_orcamento(db, orcamento_in_db)

    return orcamento_in_db, product_in_db


def update_item_in_orcamento(db: Session, orcamento_id: int, item_id: int, item_update: OrcamentoProdutoUpdate) -> tuple[Orcamento, OrcamentoProduto]:
    orcamento_in_db = get_orcamento_by_id(db, orcamento_id=orcamento_id)
    if orcamento_in_db.convertido:
        raise BadRequestException(detail="Orcamento convertido nao pode ser editado")

    item_in_db = orcamento_crud.get_product_by_id(db, item_id=item_id)
    if not item_in_db or item_in_db.orcamento_id != orcamento_id:
        raise NotFoundException(detail="Produto nao encontrado")

    if item_in_db.tipo_produto == TipoProdutoVenda.CADASTRADO:
        if item_update.descricao_avulsa:
            raise BadRequestException(detail="Um produto cadastrado nao pode ter descricao avulsa")
        if item_update.valor_unitario:
            raise BadRequestException(detail="Um produto cadastrado nao pode ter valor unitario definido manualmente")

    quantidade = item_update.quantidade or (item_in_db.quantidade or 0)

    if item_in_db.tipo_produto == TipoProdutoVenda.CADASTRADO and item_in_db.produto:
        if item_in_db.produto.estoque.quantidade < quantidade:
            raise BadRequestException(detail=f"Quantidade em estoque insuficiente para o produto {item_in_db.nome}")

    preco_unitario = item_update.valor_unitario or (item_in_db.valor_unitario or 0)

    desconto = item_in_db.desconto or 0
    if item_update.desconto is not None:
        desconto = item_update.desconto

    subtotal = quantidade * preco_unitario

    if subtotal < desconto:
        raise BadRequestException(detail="O desconto nao pode ser maior que o valor total do produto")

    item_in_db.descricao_avulsa = item_update.descricao_avulsa or item_in_db.descricao_avulsa
    item_in_db.quantidade = quantidade
    item_in_db.valor_unitario = preco_unitario
    item_in_db.desconto = desconto
    item_in_db.subtotal = subtotal

    item_in_db = orcamento_crud.update_product_in_orcamento(db, item_in_db)

    orcamento_in_db = _recalc_total_orcamento(db, orcamento_in_db)

    return orcamento_in_db, item_in_db


def remove_item_from_orcamento(db: Session, orcamento_id: int, item_id: int) -> Orcamento:
    orcamento_in_db = get_orcamento_by_id(db, orcamento_id=orcamento_id)
    if orcamento_in_db.convertido:
        raise BadRequestException(detail="Orcamento convertido nao pode ser editado")

    item_in_db = orcamento_crud.get_product_by_id(db, item_id=item_id)
    if not item_in_db or item_in_db.orcamento_id != orcamento_id:
        raise NotFoundException(detail="Produto nao encontrado")

    orcamento_crud.remove_product_from_orcamento(db, item_in_db)

    return _recalc_total_orcamento(db, orcamento_in_db)


def delete_orcamento(db: Session, orcamento_id: int) -> None:
    orcamento_in_db = get_orcamento_by_id(db, orcamento_id=orcamento_id)
    if orcamento_in_db.convertido:
        raise BadRequestException(detail="Orcamento convertido nao pode ser excluido")

    orcamento_crud.delete_orcamento(db, orcamento_in_db)


def converter_orcamento(db: Session, orcamento_id: int, payload: ConverterOrcamentoPayload) -> Venda:
    orcamento_in_db = get_orcamento_by_id(db, orcamento_id=orcamento_id)

    if orcamento_in_db.convertido:
        raise BadRequestException(detail="Orcamento ja foi convertido em venda")

    if not orcamento_in_db.itens:
        raise BadRequestException(detail="Orcamento sem itens nao pode ser convertido")

    cliente_exists(db, payload.cliente_id)

    from app.core.enum import VendaStatus

    venda_data = Venda(
        cliente_id=payload.cliente_id,
        funcionario_id=orcamento_in_db.funcionario_id,
        status=VendaStatus.ATIVA,
        entrega=orcamento_in_db.entrega,
        observacao=orcamento_in_db.observacao,
        subtotal=orcamento_in_db.subtotal,
        total=orcamento_in_db.total,
    )

    venda_in_db = venda_crud.create_sale(db, sale_data=venda_data)

    # Copia itens do orcamento para a venda
    for item in orcamento_in_db.itens:
        produto_venda = ProdutoVenda(
            venda_id=venda_in_db.id,
            produto_id=item.produto_id,
            tipo_produto=item.tipo_produto,
            descricao_avulsa=item.descricao_avulsa,
            quantidade=item.quantidade,
            valor_unitario=item.valor_unitario,
            desconto=item.desconto,
            subtotal=item.subtotal,
        )
        venda_crud.add_product_to_sale(db, produto_venda)

    # Marca orcamento como convertido
    orcamento_in_db.convertido = True
    orcamento_in_db.venda_id = venda_in_db.id
    orcamento_crud.update_orcamento(db, orcamento_in_db)

    return venda_in_db


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

def get_orcamento_by_id(db: Session, orcamento_id: int) -> Orcamento:
    orcamento_in_db = orcamento_crud.get_orcamento_by_id(db, orcamento_id=orcamento_id)
    if not orcamento_in_db:
        raise NotFoundException(detail="Orcamento nao encontrado")
    return orcamento_in_db


def get_orcamentos(db: Session, filters: OrcamentoSearchFilters, page: int, limit: int = 100) -> tuple[Sequence[Orcamento], int, int, dict]:
    skip = (page - 1) * limit

    filters_dict = filters.model_dump(exclude_unset=True)

    orcamentos_in_db, total = orcamento_crud.get_orcamentos_by_search(
        db, filters=filters_dict, skip=skip, limit=limit
    )

    total_pages, links = _set_pagination(
        total_items=total, filters=filters_dict, page=page, limit=limit
    )

    return orcamentos_in_db, total, total_pages, links


def get_orcamentos_status(db: Session, funcionario_id: int | None = None) -> OrcamentoStatusSummary:
    return orcamento_crud.get_orcamentos_status(db, funcionario_id=funcionario_id)
