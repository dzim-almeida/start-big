# ---------------------------------------------------------------------------
# ARQUIVO: services/dashboard.py
# DESCRICAO: Logica de negocio para o Dashboard.
#            Calcula periodos, variacoes percentuais e bandas de urgencia.
# ---------------------------------------------------------------------------

from datetime import datetime, date, timedelta
from calendar import monthrange

from sqlalchemy.orm import Session

from app.db.crud import dashboard as dashboard_crud
from app.schemas.dashboard import (
    DashboardStats,
    OSVencendoItem,
    OSVencendoResponse,
    EstoqueBaixoItem,
    EstoqueBaixoResponse,
    UltimaVendaItem,
    UltimasVendasResponse,
)


# ===========================================================================
# HELPERS
# ===========================================================================

def _calcular_periodo(periodo: str) -> tuple[datetime, datetime, datetime, datetime]:
    """
    Retorna (inicio_atual, fim_atual, inicio_anterior, fim_anterior)
    para o periodo solicitado.
    """
    hoje = date.today()

    if periodo == "hoje":
        inicio = datetime.combine(hoje, datetime.min.time())
        fim = datetime.now()
        ontem = hoje - timedelta(days=1)
        inicio_ant = datetime.combine(ontem, datetime.min.time())
        fim_ant = datetime.combine(ontem, datetime.max.time())

    elif periodo == "semana":
        # Segunda-feira da semana atual
        inicio = datetime.combine(hoje - timedelta(days=hoje.weekday()), datetime.min.time())
        fim = datetime.now()
        # Semana anterior: segunda a domingo
        inicio_ant = inicio - timedelta(days=7)
        fim_ant = datetime.combine(inicio.date() - timedelta(days=1), datetime.max.time())

    else:  # mes
        inicio = datetime.combine(hoje.replace(day=1), datetime.min.time())
        fim = datetime.now()
        # Mes anterior
        if hoje.month == 1:
            mes_ant = 12
            ano_ant = hoje.year - 1
        else:
            mes_ant = hoje.month - 1
            ano_ant = hoje.year
        ultimo_dia_ant = monthrange(ano_ant, mes_ant)[1]
        inicio_ant = datetime.combine(date(ano_ant, mes_ant, 1), datetime.min.time())
        fim_ant = datetime.combine(date(ano_ant, mes_ant, ultimo_dia_ant), datetime.max.time())

    return inicio, fim, inicio_ant, fim_ant


def _calcular_variacao(atual: float, anterior: float) -> float:
    """Calcula variacao percentual entre dois valores."""
    if anterior == 0:
        return 100.0 if atual > 0 else 0.0
    return round(((atual - anterior) / anterior) * 100, 1)


def _calcular_urgencia(data_previsao: datetime) -> str:
    """Determina a faixa de urgencia com base na data de previsao."""
    hoje = date.today()
    diff = (data_previsao.date() - hoje).days

    if diff <= 0:
        return "vermelho"
    elif diff <= 3:
        return "amarelo"
    else:
        return "verde"


def _calcular_ticket_medio(stats: "dashboard_crud.StatsAgregados") -> int:
    """Calcula ticket medio combinado (vendas + OS finalizadas) a partir dos dados agregados."""
    soma_total = stats.vendas_total + stats.os_soma
    qtd_total = stats.vendas_count + stats.os_finalizadas_count
    if qtd_total == 0:
        return 0
    return int(soma_total / qtd_total)


# ===========================================================================
# STATS
# ===========================================================================

def get_dashboard_stats(db: Session, periodo: str, empresa_id: int) -> DashboardStats:
    """Retorna as 4 metricas com variacao percentual vs periodo anterior."""
    inicio, fim, inicio_ant, fim_ant = _calcular_periodo(periodo)

    # 2 queries consolidadas (atual + anterior) em vez de 8 separadas
    atual = dashboard_crud.get_stats_agregados(db, inicio, fim, empresa_id)
    anterior = dashboard_crud.get_stats_agregados(db, inicio_ant, fim_ant, empresa_id)

    ticket_atual = _calcular_ticket_medio(atual)
    ticket_ant = _calcular_ticket_medio(anterior)

    return DashboardStats(
        vendas_total=atual.vendas_total,
        vendas_total_variacao=_calcular_variacao(atual.vendas_total, anterior.vendas_total),
        os_count=atual.os_count,
        os_count_variacao=_calcular_variacao(atual.os_count, anterior.os_count),
        novos_clientes=atual.clientes_count,
        novos_clientes_variacao=_calcular_variacao(atual.clientes_count, anterior.clientes_count),
        ticket_medio=ticket_atual,
        ticket_medio_variacao=_calcular_variacao(ticket_atual, ticket_ant),
    )


# ===========================================================================
# OS VENCENDO
# ===========================================================================

def get_os_vencendo(db: Session, empresa_id: int) -> OSVencendoResponse:
    """Retorna OS proximas/passadas do prazo com banda de urgencia."""
    rows = dashboard_crud.get_os_vencendo(db, empresa_id)

    items = [
        OSVencendoItem(
            numero_os=row.numero_os,
            cliente_nome=row.cliente_nome,
            defeito_relatado=row.defeito_relatado,
            data_previsao=row.data_previsao,
            urgencia=_calcular_urgencia(row.data_previsao),
        )
        for row in rows
    ]

    return OSVencendoResponse(items=items)


# ===========================================================================
# ESTOQUE BAIXO
# ===========================================================================

def get_estoque_baixo(db: Session) -> EstoqueBaixoResponse:
    """Retorna produtos com estoque zerado ou abaixo do minimo."""
    rows = dashboard_crud.get_estoque_baixo(db)

    items = [
        EstoqueBaixoItem(
            produto_id=row.produto_id,
            nome=row.nome,
            quantidade=row.quantidade,
            quantidade_minima=row.quantidade_minima,
            status="zerado" if row.quantidade == 0 else "baixo",
        )
        for row in rows
    ]

    return EstoqueBaixoResponse(items=items)


# ===========================================================================
# ULTIMAS VENDAS
# ===========================================================================

def get_ultimas_vendas(db: Session, empresa_id: int) -> UltimasVendasResponse:
    """Retorna as vendas mais recentes."""
    rows = dashboard_crud.get_ultimas_vendas(db, empresa_id)

    items = [
        UltimaVendaItem(
            id=row.id,
            numero_venda=row.numero_venda,
            cliente_nome=row.cliente_nome,
            total=row.total,
            status=row.status.value,
            criado_em=row.criado_em,
        )
        for row in rows
    ]

    return UltimasVendasResponse(items=items)
