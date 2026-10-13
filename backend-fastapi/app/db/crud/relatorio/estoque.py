# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/relatorio/estoque.py
# DESCRICAO: Relatorios (crud) - vendas por produto e produtos em estoque.
# ---------------------------------------------------------------------------

from datetime import datetime
from typing import Sequence
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from app.db.models.venda import Venda
from app.db.models.venda_produto import ProdutoVenda
from app.db.models.produto import Produto
from app.db.models.estoque import Estoque
from app.db.models.funcionario import Funcionario
from app.core.enum import (
    VendaStatus,
)


# ===========================================================================
# ESTOQUE / CURVA ABC (Fase 4a)
# ===========================================================================

def get_vendas_por_produto(
    db: Session, data_inicio: datetime, data_fim: datetime, empresa_id: int
) -> Sequence:
    """Faturamento e quantidade por produto CADASTRADO nas vendas finalizadas do período.

    Base da Curva ABC. Faturamento = Σ(subtotal - desconto) do item (nível-item, já
    pós-desconto do item). Itens avulsos (produto_id NULL) ficam de fora — não têm
    produto de estoque para classificar. Escopo por empresa via funcionário da venda.
    """
    # Menos o desconto da regra de preço (R1/R3, §6.1) — é receita que não entrou.
    faturamento = func.coalesce(
        func.sum(ProdutoVenda.subtotal - ProdutoVenda.desconto - ProdutoVenda.desconto_regra), 0
    )
    stmt = (
        select(
            Produto.id.label("produto_id"),
            Produto.nome,
            Produto.codigo_produto.label("sku"),
            Produto.categoria,
            faturamento.label("faturamento"),
            # Na unidade base (D12 do plano de embalagens): "2 FD" de 12 conta 24.
            func.coalesce(func.sum(ProdutoVenda.quantidade * ProdutoVenda.fator_embalagem), 0).label("quantidade"),
        )
        .join(Venda, Venda.id == ProdutoVenda.venda_id)
        .join(Funcionario, Funcionario.id == Venda.funcionario_id)
        .join(Produto, Produto.id == ProdutoVenda.produto_id)
        .where(
            and_(
                Venda.status == VendaStatus.FINALIZADA,
                Venda.criado_em >= data_inicio,
                Venda.criado_em <= data_fim,
                Funcionario.empresa_id == empresa_id,
                ProdutoVenda.produto_id.isnot(None),
            )
        )
        .group_by(Produto.id, Produto.nome, Produto.codigo_produto, Produto.categoria)
        .order_by(faturamento.desc())
    )
    return db.execute(stmt).all()


def get_produtos_estoque(db: Session) -> Sequence:
    """Posição de estoque de todos os produtos ATIVOS (nome, sku, custo, mínimos).

    Produto não tem empresa_id (banco é single-store por loja) — retorna global,
    igual ao get_estoque_baixo do dashboard. Base dos KPIs de valor imobilizado,
    da lista "abaixo do mínimo" e do cruzamento com vendas para achar os "parados".
    """
    stmt = (
        select(
            Produto.id.label("produto_id"),
            Produto.nome,
            Produto.codigo_produto.label("sku"),
            Produto.categoria,
            Estoque.quantidade,
            Estoque.valor_entrada,
            Estoque.custo_medio,
            Estoque.valor_varejo,
            Estoque.quantidade_minima,
            Estoque.quantidade_ideal,
        )
        .join(Estoque, Estoque.id == Produto.id)
        .where(Produto.ativo == True)
        .order_by(Produto.nome.asc())
    )
    return db.execute(stmt).all()
