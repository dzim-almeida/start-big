# ---------------------------------------------------------------------------
# ARQUIVO: services/orcamento/itens.py
# DESCRICAO: Orcamento - incluir, editar e remover item.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from app.db.models.orcamento import Orcamento
from app.db.models.orcamento_produto import OrcamentoProduto
from app.schemas.orcamentos import OrcamentoProdutoCreate, OrcamentoProdutoUpdate
from app.services import produto as produto_service
from app.services.produto import embalagem as embalagem_service
from app.services import quantidade_venda
from app.db.crud import orcamento as orcamento_crud
from app.core.enum import TipoProdutoVenda
from app.helpers.exceptions import BadRequestException, NotFoundException
from app.services.orcamento.calculo import _recalc_total_orcamento
from app.services.orcamento.consultas import get_orcamento_by_id


def add_item_to_orcamento(db: Session, orcamento_id: int, item_data: OrcamentoProdutoCreate) -> tuple[Orcamento, OrcamentoProduto]:
    orcamento_in_db = get_orcamento_by_id(db, orcamento_id=orcamento_id)
    if orcamento_in_db.convertido:
        raise BadRequestException(detail="Orcamento convertido nao pode ser editado")

    quantidade = item_data.quantidade
    valor_unitario = item_data.valor_unitario
    desconto = item_data.desconto

    product_data = OrcamentoProduto(
        **item_data.model_dump(exclude={"valor_unitario", "embalagem_id"}),
        orcamento_id=orcamento_id,
    )

    if item_data.embalagem_id is not None and item_data.tipo_produto != TipoProdutoVenda.CADASTRADO:
        raise BadRequestException(detail="So produto cadastrado e vendido por embalagem")

    if item_data.produto_id:
        if item_data.tipo_produto == TipoProdutoVenda.AVULSO:
            raise BadRequestException(detail="Um produto avulso nao pode estar cadastrado")

        product_in_db = produto_service.get_produto_by_id(db, produto_id=item_data.produto_id)

        # Mesmo carimbo da venda: o orcamento "2 FD" precisa virar venda "2 FD" (G3).
        valor_unitario = embalagem_service.aplicar_embalagem_na_linha(
            db, product_data, product_in_db, item_data.embalagem_id, orcamento_in_db.funcionario.empresa_id
        )
        quantidade_venda.exigir_quantidade_permitida(quantidade, product_in_db, product_data.fator_embalagem)
        if product_data.quantidade_base > product_in_db.estoque.quantidade:
            raise BadRequestException(detail=f"Quantidade em estoque insuficiente para o produto {product_in_db.nome}")

    if item_data.tipo_produto == TipoProdutoVenda.AVULSO and item_data.descricao_avulsa is None:
        raise BadRequestException(detail="Um produto avulso deve ter descricao")
    if item_data.tipo_produto == TipoProdutoVenda.AVULSO:
        quantidade_venda.exigir_quantidade_permitida(quantidade, None)

    bruto = quantidade_venda.subtotal_da_linha(quantidade, valor_unitario)
    if desconto > bruto:
        raise BadRequestException(detail="O desconto nao pode ser maior que o total do produto")

    subtotal = bruto - desconto

    product_data.valor_unitario = valor_unitario
    product_data.subtotal = subtotal

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
    if item_update.quantidade is not None:
        quantidade_venda.exigir_quantidade_permitida(
            quantidade,
            item_in_db.produto if item_in_db.tipo_produto == TipoProdutoVenda.CADASTRADO else None,
            item_in_db.fator_embalagem,
        )

    if item_in_db.tipo_produto == TipoProdutoVenda.CADASTRADO and item_in_db.produto:
        if item_in_db.produto.estoque.quantidade < quantidade * (item_in_db.fator_embalagem or 1):
            raise BadRequestException(detail=f"Quantidade em estoque insuficiente para o produto {item_in_db.nome}")

    preco_unitario = item_update.valor_unitario or (item_in_db.valor_unitario or 0)

    desconto = item_in_db.desconto or 0
    if item_update.desconto is not None:
        desconto = item_update.desconto

    subtotal = quantidade_venda.subtotal_da_linha(quantidade, preco_unitario)

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
