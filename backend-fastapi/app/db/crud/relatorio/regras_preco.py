# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/relatorio/regras_preco.py
# DESCRICAO: Relatorios (crud) - vendas com regra de preco por quantidade.
# ---------------------------------------------------------------------------

from datetime import datetime
from typing import Sequence
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, case
from app.db.models.venda import Venda
from app.db.models.venda_produto import ProdutoVenda
from app.db.models.produto import Produto
from app.db.models.funcionario import Funcionario
from app.core.enum import (
    VendaStatus,
)


def get_vendas_por_regra_preco(
    db: Session, data_inicio: datetime, data_fim: datetime, empresa_id: int
) -> Sequence:
    """Linhas vendidas com regra de preço (R1/R2/R3), por produto e regra.

    Base do relatório "vendas por regra de preço" (fase 6 das embalagens). Só
    vendas FINALIZADAS do período; `MANUAL` (preço trocado pelo gerente) não é
    regra e fica de fora.

    `abatimento` é o que a regra deixou de cobrar, nas duas formas que ela tem:
    R1/R3 guardam em `desconto_regra`; a R2 muda o preço, então a diferença é
    (cheio − praticado) × quantidade. `faturamento` é o mesmo da Curva ABC —
    subtotal menos os dois descontos — para os dois relatórios baterem.
    """
    abatimento_r2 = case(
        (
            and_(ProdutoVenda.regra_preco == "R2", ProdutoVenda.valor_unitario_tabela.isnot(None)),
            (ProdutoVenda.valor_unitario_tabela - ProdutoVenda.valor_unitario) * ProdutoVenda.quantidade,
        ),
        else_=0,
    )
    faturamento = func.coalesce(
        func.sum(ProdutoVenda.subtotal - ProdutoVenda.desconto - ProdutoVenda.desconto_regra), 0
    )
    stmt = (
        select(
            ProdutoVenda.regra_preco.label("regra"),
            Produto.id.label("produto_id"),
            Produto.nome,
            Produto.codigo_produto.label("sku"),
            func.count(func.distinct(ProdutoVenda.venda_id)).label("qtd_vendas"),
            func.coalesce(func.sum(ProdutoVenda.quantidade * ProdutoVenda.fator_embalagem), 0).label("unidades"),
            faturamento.label("faturamento"),
            func.coalesce(func.sum(ProdutoVenda.desconto_regra + abatimento_r2), 0).label("abatimento"),
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
                ProdutoVenda.regra_preco.in_(("R1", "R2", "R3")),
            )
        )
        .group_by(ProdutoVenda.regra_preco, Produto.id, Produto.nome, Produto.codigo_produto)
        .order_by(func.sum(ProdutoVenda.desconto_regra + abatimento_r2).desc())
    )
    return db.execute(stmt).all()


def get_vendas_com_regra_count(
    db: Session, data_inicio: datetime, data_fim: datetime, empresa_id: int
) -> int:
    """Quantas vendas finalizadas do período tiveram ao menos uma linha com regra.

    Separada da consulta por produto: uma venda com duas regras apareceria em
    dois grupos, e somar `qtd_vendas` contaria a mesma venda duas vezes.
    """
    stmt = (
        select(func.count(func.distinct(ProdutoVenda.venda_id)))
        .join(Venda, Venda.id == ProdutoVenda.venda_id)
        .join(Funcionario, Funcionario.id == Venda.funcionario_id)
        .where(
            and_(
                Venda.status == VendaStatus.FINALIZADA,
                Venda.criado_em >= data_inicio,
                Venda.criado_em <= data_fim,
                Funcionario.empresa_id == empresa_id,
                ProdutoVenda.regra_preco.in_(("R1", "R2", "R3")),
            )
        )
    )
    return db.execute(stmt).scalar() or 0


def get_vendas_com_regra_por_regra(
    db: Session, data_inicio: datetime, data_fim: datetime, empresa_id: int
) -> dict[str, int]:
    """Vendas distintas por regra: {"R1": 4, "R3": 1}. Mesma razão da contagem acima."""
    stmt = (
        select(ProdutoVenda.regra_preco, func.count(func.distinct(ProdutoVenda.venda_id)))
        .join(Venda, Venda.id == ProdutoVenda.venda_id)
        .join(Funcionario, Funcionario.id == Venda.funcionario_id)
        .where(
            and_(
                Venda.status == VendaStatus.FINALIZADA,
                Venda.criado_em >= data_inicio,
                Venda.criado_em <= data_fim,
                Funcionario.empresa_id == empresa_id,
                ProdutoVenda.regra_preco.in_(("R1", "R2", "R3")),
            )
        )
        .group_by(ProdutoVenda.regra_preco)
    )
    return {regra: qtd for regra, qtd in db.execute(stmt).all()}
