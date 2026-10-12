# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/dashboard/indicadores.py
# DESCRICAO: Dashboard - totais agregados do periodo e formas de pagamento.
#            Tambem usados pelo financeiro (visao e analise) e pelos relatorios.
# ---------------------------------------------------------------------------

from datetime import datetime
from typing import Sequence, NamedTuple

from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_, and_

from app.db.models.venda import Venda
from app.db.models.ordem_servico import OrdemServico as OSModel
from app.db.models.cliente import Cliente
from app.db.models.funcionario import Funcionario
from app.db.models.venda_pagamento import PagamentoVenda
from app.db.models.ordem_servico_pagamento import OrdemServicoPagamento
from app.db.models.forma_pagamento import FormaPagamento

from app.core.enum import VendaStatus, OrdemServicoStatus


# ===========================================================================
# STATS — Metricas agregadas por periodo (query consolidada)
# ===========================================================================

class StatsAgregados(NamedTuple):
    vendas_total: int
    vendas_count: int
    os_count: int
    clientes_count: int
    os_soma: int
    os_finalizadas_count: int


def get_stats_agregados(
    db: Session,
    data_inicio: datetime,
    data_fim: datetime,
    empresa_id: int,
) -> StatsAgregados:
    """
    Retorna todas as metricas do dashboard em 3 queries (vendas, OS, clientes)
    em vez de 8 separadas. Filtra por empresa_id via Funcionario.
    """
    # Vendas: soma total + contagem (para ticket medio)
    vendas_stmt = select(
        func.coalesce(func.sum(Venda.total), 0).label("vendas_total"),
        func.count(Venda.id).label("vendas_count"),
    ).join(
        Funcionario, Funcionario.id == Venda.funcionario_id
    ).where(
        and_(
            Venda.status == VendaStatus.FINALIZADA,
            Venda.criado_em >= data_inicio,
            Venda.criado_em <= data_fim,
            Funcionario.empresa_id == empresa_id,
        )
    )
    vendas_result = db.execute(vendas_stmt).first()

    # OS: DUAS ancoras de data diferentes, de proposito.
    #
    # Faturamento ancora em data_finalizacao — o dinheiro entra quando a OS
    # fecha, nao quando o equipamento chega no balcao. Antes tudo usava
    # data_criacao, e uma OS aberta em julho e finalizada em agosto lancava
    # receita em julho, num mes em que ela ainda nem tinha sido cobrada.
    #
    # A contagem de OS que ENTRARAM no periodo continua em data_criacao, porque
    # e outra pergunta: quanto movimento chegou na oficina.
    os_finalizadas_stmt = select(
        func.coalesce(func.sum(OSModel.valor_total), 0).label("os_soma"),
        func.count(OSModel.id).label("os_finalizadas_count"),
    ).outerjoin(
        Funcionario, Funcionario.id == OSModel.funcionario_id
    ).where(
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
    os_finalizadas_result = db.execute(os_finalizadas_stmt).first()

    os_entradas_stmt = select(
        func.count(OSModel.id).label("os_count"),
    ).outerjoin(
        Funcionario, Funcionario.id == OSModel.funcionario_id
    ).where(
        and_(
            # Esta É por data de criação, de propósito: mede quanto entrou na
            # oficina no período, não quanto foi faturado.
            OSModel.data_criacao >= data_inicio,
            OSModel.data_criacao <= data_fim,
            or_(
                Funcionario.empresa_id == empresa_id,
                OSModel.funcionario_id.is_(None),
            ),
        )
    )
    os_count = db.scalar(os_entradas_stmt) or 0

    # Clientes: sem empresa_id no modelo, contagem global
    clientes_stmt = select(func.count(Cliente.id)).where(
        and_(
            Cliente.data_criacao >= data_inicio,
            Cliente.data_criacao <= data_fim,
        )
    )
    clientes_count = db.scalar(clientes_stmt) or 0

    return StatsAgregados(
        vendas_total=vendas_result.vendas_total or 0,
        vendas_count=vendas_result.vendas_count or 0,
        os_count=os_count,
        clientes_count=clientes_count,
        os_soma=os_finalizadas_result.os_soma or 0,
        os_finalizadas_count=os_finalizadas_result.os_finalizadas_count or 0,
    )


# ===========================================================================
# MASTER — Formas de pagamento
# ===========================================================================

def get_formas_pagamento_vendas(
    db: Session, data_inicio: datetime, data_fim: datetime, empresa_id: int
) -> Sequence:
    """Pagamentos de vendas agrupados por forma no periodo."""
    stmt = (
        select(
            FormaPagamento.nome,
            func.sum(PagamentoVenda.valor).label("total"),
        )
        .select_from(PagamentoVenda)
        .join(FormaPagamento, FormaPagamento.id == PagamentoVenda.forma_pagamento_id)
        .join(Venda, Venda.id == PagamentoVenda.venda_id)
        .join(Funcionario, Funcionario.id == Venda.funcionario_id)
        .where(and_(
            Venda.status == VendaStatus.FINALIZADA,
            Venda.criado_em >= data_inicio,
            Venda.criado_em <= data_fim,
            Funcionario.empresa_id == empresa_id,
        ))
        .group_by(FormaPagamento.nome)
    )
    return db.execute(stmt).all()


def get_formas_pagamento_os(
    db: Session, data_inicio: datetime, data_fim: datetime, empresa_id: int
) -> Sequence:
    """Pagamentos de OS agrupados por forma no periodo."""
    stmt = (
        select(
            FormaPagamento.nome,
            func.sum(OrdemServicoPagamento.valor).label("total"),
        )
        .select_from(OrdemServicoPagamento)
        .join(FormaPagamento, FormaPagamento.id == OrdemServicoPagamento.forma_pagamento_id)
        .join(OSModel, OSModel.id == OrdemServicoPagamento.ordem_servico_id)
        .outerjoin(Funcionario, Funcionario.id == OSModel.funcionario_id)
        .where(and_(
            OSModel.status == OrdemServicoStatus.FINALIZADA,
            OSModel.data_finalizacao.isnot(None),
            OSModel.data_finalizacao >= data_inicio,
            OSModel.data_finalizacao <= data_fim,
            or_(
                Funcionario.empresa_id == empresa_id,
                OSModel.funcionario_id.is_(None),
            ),
        ))
        .group_by(FormaPagamento.nome)
    )
    return db.execute(stmt).all()
