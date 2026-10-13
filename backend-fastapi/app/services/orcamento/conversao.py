# ---------------------------------------------------------------------------
# ARQUIVO: services/orcamento/conversao.py
# DESCRICAO: Orcamento - converter o orcamento em venda.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from app.db.models.venda import Venda
from app.db.models.venda_produto import ProdutoVenda
from app.schemas.orcamentos import ConverterOrcamentoPayload
from app.services.cliente import cliente_exists
from app.db.crud import orcamento as orcamento_crud
from app.db.crud import venda as venda_crud
from app.helpers.exceptions import BadRequestException
from app.services.orcamento.consultas import get_orcamento_by_id


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
            # G3: sem isto, o orcamento "2 FD" virava venda "2 UN" em silencio.
            embalagem_id=item.embalagem_id,
            fator_embalagem=item.fator_embalagem or 1,
            sigla_embalagem=item.sigla_embalagem,
        )
        venda_crud.add_product_to_sale(db, produto_venda)

    # Regras de preço por quantidade (§6.1): o orçamento sai com o preço de
    # tabela, e a venda nasce com as regras que a loja ligou — igual a montar
    # o carrinho no caixa. Sem regra ligada, não muda nada (B8).
    from app.services import regras_preco as regras_preco_service
    from app.services import venda as venda_service
    db.refresh(venda_in_db)
    if regras_preco_service.aplicar_na_venda(db, venda_in_db):
        venda_service._recalc_total_sale(db, venda_in_db, aplicar_regras=False)

    # Marca orcamento como convertido
    orcamento_in_db.convertido = True
    orcamento_in_db.venda_id = venda_in_db.id
    orcamento_crud.update_orcamento(db, orcamento_in_db)

    return venda_in_db
