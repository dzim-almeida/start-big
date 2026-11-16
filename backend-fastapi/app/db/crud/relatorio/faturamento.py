# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/relatorio/faturamento.py
# DESCRICAO: Relatorios (crud) - series de faturamento por dia e juros por responsavel.
# ---------------------------------------------------------------------------

from datetime import datetime
from typing import Sequence
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_
from app.core.tempo import data_local_sql
from app.db.models.venda import Venda
from app.db.models.venda_pagamento import PagamentoVenda
from app.db.models.ordem_servico import OrdemServico as OSModel
from app.db.models.ordem_servico_pagamento import OrdemServicoPagamento
from app.db.models.funcionario import Funcionario
from app.core.enum import (
    VendaStatus,
    OrdemServicoStatus,
)


def get_faturamento_vendas_por_dia(
    db: Session, data_inicio: datetime, data_fim: datetime, empresa_id: int
) -> Sequence:
    """Soma das vendas finalizadas agrupada por dia (func.date), da empresa."""
    stmt = (
        select(
            data_local_sql(Venda.criado_em).label("dia"),
            func.coalesce(func.sum(Venda.total), 0).label("total"),
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
        .group_by(data_local_sql(Venda.criado_em))
    )
    return db.execute(stmt).all()


def get_faturamento_os_por_dia(
    db: Session, data_inicio: datetime, data_fim: datetime, empresa_id: int
) -> Sequence:
    """Soma das OS finalizadas agrupada por dia (func.date), da empresa.

    Ancorado em data_finalizacao: a receita da OS pertence ao dia em que ela foi
    fechada, nao ao dia em que o equipamento entrou. Bate com o get_stats_agregados
    do dashboard, que usa a mesma ancora.
    """
    stmt = (
        select(
            data_local_sql(OSModel.data_finalizacao).label("dia"),
            func.coalesce(func.sum(OSModel.valor_total), 0).label("total"),
        )
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
            )
        )
        .group_by(data_local_sql(OSModel.data_finalizacao))
    )
    return db.execute(stmt).all()


# ---------------------------------------------------------------------------
# JUROS DE CARTAO
#
# O juros de um pagamento sempre vai para a operadora; o que muda e quem paga.
# Repassado (CLIENTE), ele esta embutido no total da venda/OS e portanto inflou
# o faturamento bruto. Absorvido (LOJA), ele nao esta em lugar nenhum do total,
# mas saiu do bolso da loja. Nos dois casos precisa ser descontado para chegar
# ao liquido — por isso as somas vem separadas por responsavel.
#
# Os filtros de periodo/empresa espelham get_formas_pagamento_* do dashboard,
# para que o desconto caia exatamente sobre o mesmo conjunto que formou o bruto.
# ---------------------------------------------------------------------------

def get_juros_vendas_por_responsavel(
    db: Session, data_inicio: datetime, data_fim: datetime, empresa_id: int
) -> Sequence:
    """Soma de juros dos pagamentos de venda, agrupada por responsavel."""
    stmt = (
        select(
            PagamentoVenda.juros_responsavel.label("responsavel"),
            func.coalesce(func.sum(PagamentoVenda.juros_valor), 0).label("total"),
        )
        .select_from(PagamentoVenda)
        .join(Venda, Venda.id == PagamentoVenda.venda_id)
        .join(Funcionario, Funcionario.id == Venda.funcionario_id)
        .where(
            and_(
                Venda.status == VendaStatus.FINALIZADA,
                Venda.criado_em >= data_inicio,
                Venda.criado_em <= data_fim,
                Funcionario.empresa_id == empresa_id,
            )
        )
        .group_by(PagamentoVenda.juros_responsavel)
    )
    return db.execute(stmt).all()


def get_juros_os_por_responsavel(
    db: Session, data_inicio: datetime, data_fim: datetime, empresa_id: int
) -> Sequence:
    """Soma de juros dos pagamentos de OS, agrupada por responsavel."""
    stmt = (
        select(
            OrdemServicoPagamento.juros_responsavel.label("responsavel"),
            func.coalesce(func.sum(OrdemServicoPagamento.juros_valor), 0).label("total"),
        )
        .select_from(OrdemServicoPagamento)
        .join(OSModel, OSModel.id == OrdemServicoPagamento.ordem_servico_id)
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
            )
        )
        .group_by(OrdemServicoPagamento.juros_responsavel)
    )
    return db.execute(stmt).all()
