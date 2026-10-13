# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/relatorio/contador.py
# DESCRICAO: Relatorios (crud) - linhas fiscais de venda e OS para o PGDAS-D.
# ---------------------------------------------------------------------------

from datetime import datetime
from typing import Sequence
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_
from app.db.models.venda import Venda
from app.db.models.venda_produto import ProdutoVenda
from app.db.models.produto import Produto
from app.db.models.produto_fiscal import ProdutoFiscal
from app.db.models.ordem_servico import OrdemServico as OSModel
from app.db.models.ordem_servico_item import OrdemServicoItem
from app.db.models.funcionario import Funcionario
from app.core.enum import (
    VendaStatus,
    OrdemServicoStatus,
    OrdemServicoItemAprovacao,
)


# ---------------------------------------------------------------------------
# RECEITA PARA O CONTADOR (segregação do PGDAS-D)
# ---------------------------------------------------------------------------

def get_linhas_venda_fiscal(
    db: Session, data_inicio: datetime, data_fim: datetime, empresa_id: int
) -> Sequence:
    """Cada linha das vendas finalizadas do período, líquida, com o cadastro fiscal.

    Mesmo filtro do faturamento (criado_em, FINALIZADA, empresa pelo
    funcionário), para os totais baterem. Avulso e produto sem ficha fiscal
    voltam com os códigos nulos.
    """
    stmt = (
        select(
            ProdutoVenda.produto_id,
            func.coalesce(Produto.nome, ProdutoVenda.descricao_avulsa).label("nome"),
            (ProdutoVenda.subtotal - ProdutoVenda.desconto - ProdutoVenda.desconto_regra).label("valor"),
            ProdutoFiscal.csosn,
            ProdutoFiscal.cst_icms,
            ProdutoFiscal.cst_pis,
            ProdutoFiscal.cst_cofins,
        )
        .join(Venda, Venda.id == ProdutoVenda.venda_id)
        .join(Funcionario, Funcionario.id == Venda.funcionario_id)
        .outerjoin(Produto, Produto.id == ProdutoVenda.produto_id)
        .outerjoin(ProdutoFiscal, ProdutoFiscal.produto_id == ProdutoVenda.produto_id)
        .where(
            and_(
                Venda.status == VendaStatus.FINALIZADA,
                Venda.criado_em >= data_inicio,
                Venda.criado_em <= data_fim,
                Funcionario.empresa_id == empresa_id,
            )
        )
    )
    return db.execute(stmt).all()


def get_extras_vendas(
    db: Session, data_inicio: datetime, data_fim: datetime, empresa_id: int
):
    """Σ total, Σ frete e Σ acréscimo (juros) das vendas do mesmo recorte."""
    stmt = (
        select(
            func.coalesce(func.sum(Venda.total), 0).label("total"),
            func.coalesce(func.sum(Venda.entrega), 0).label("entrega"),
            func.coalesce(func.sum(Venda.acrescimo), 0).label("acrescimo"),
        )
        .join(Funcionario, Funcionario.id == Venda.funcionario_id)
        .where(
            and_(
                Venda.status == VendaStatus.FINALIZADA,
                Venda.criado_em >= data_inicio,
                Venda.criado_em <= data_fim,
                Funcionario.empresa_id == empresa_id,
            )
        )
    )
    return db.execute(stmt).one()


def get_itens_os_fiscal(
    db: Session, data_inicio: datetime, data_fim: datetime, empresa_id: int
) -> Sequence:
    """Itens das OS finalizadas no período (sem os REPROVADOS), com os valores
    da OS para o rateio do desconto e o cadastro fiscal das peças.

    Mesma âncora e mesmo escopo do faturamento de OS (data_finalizacao; OS sem
    funcionário entra).
    """
    stmt = (
        select(
            OSModel.id.label("os_id"),
            OSModel.valor_total.label("os_total"),
            OSModel.valor_bruto.label("os_bruto"),
            OSModel.desconto.label("os_desconto"),
            OSModel.taxa_entrega.label("os_taxa"),
            OSModel.acrescimo.label("os_acrescimo"),
            OrdemServicoItem.tipo,
            OrdemServicoItem.produto_id,
            OrdemServicoItem.nome,
            OrdemServicoItem.valor_total.label("valor"),
            ProdutoFiscal.csosn,
            ProdutoFiscal.cst_icms,
            ProdutoFiscal.cst_pis,
            ProdutoFiscal.cst_cofins,
        )
        .join(OrdemServicoItem, OrdemServicoItem.ordem_servico_id == OSModel.id)
        .outerjoin(Funcionario, Funcionario.id == OSModel.funcionario_id)
        .outerjoin(ProdutoFiscal, ProdutoFiscal.produto_id == OrdemServicoItem.produto_id)
        .where(
            and_(
                OSModel.status == OrdemServicoStatus.FINALIZADA,
                OSModel.data_finalizacao.isnot(None),
                OSModel.data_finalizacao >= data_inicio,
                OSModel.data_finalizacao <= data_fim,
                or_(
                    Funcionario.empresa_id == empresa_id,
                    OSModel.funcionario_id.is_(None),
                ),
                OrdemServicoItem.status_aprovacao != OrdemServicoItemAprovacao.REPROVADO,
            )
        )
        .order_by(OSModel.id, OrdemServicoItem.id)
    )
    return db.execute(stmt).all()


def get_os_finalizadas_sem_itens_total(
    db: Session, data_inicio: datetime, data_fim: datetime, empresa_id: int
) -> int:
    """Σ valor_total das OS finalizadas do período que não têm item que conte.

    Raro (OS só com taxa de entrega, ou tudo reprovado), mas existe: sem isto o
    total do relatório não bateria com o faturamento de OS.
    """
    conta = (
        select(OrdemServicoItem.id)
        .where(
            and_(
                OrdemServicoItem.ordem_servico_id == OSModel.id,
                OrdemServicoItem.status_aprovacao != OrdemServicoItemAprovacao.REPROVADO,
            )
        )
        .exists()
    )
    stmt = (
        select(func.coalesce(func.sum(OSModel.valor_total), 0))
        .outerjoin(Funcionario, Funcionario.id == OSModel.funcionario_id)
        .where(
            and_(
                OSModel.status == OrdemServicoStatus.FINALIZADA,
                OSModel.data_finalizacao.isnot(None),
                OSModel.data_finalizacao >= data_inicio,
                OSModel.data_finalizacao <= data_fim,
                or_(
                    Funcionario.empresa_id == empresa_id,
                    OSModel.funcionario_id.is_(None),
                ),
                ~conta,
            )
        )
    )
    return db.execute(stmt).scalar() or 0
