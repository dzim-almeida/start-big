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
    MeuResumoStats,
    MinhaFilaItem,
    MinhaFilaResponse,
    OSAtrasadaItem,
    OSAtrasadaResponse,
    OSAguardandoRetiradaItem,
    OSAguardandoRetiradaResponse,
    AtividadeItem,
    AtividadeHojeResponse,
    RankingFuncionarioItem,
    RankingFuncionariosResponse,
    OSPorStatusItem,
    OSPorStatusResponse,
    FormaPagamentoItem,
    FormasPagamentoResponse,
    OSAtrasadaEmpresaItem,
    OSAtrasadaEmpresaResponse,
)


# ===========================================================================
# HELPERS
# ===========================================================================

def _calcular_periodo(periodo: str) -> tuple[datetime, datetime, datetime, datetime]:
    """
    Retorna (inicio_atual, fim_atual, inicio_anterior, fim_anterior) em UTC.
    O SQLite armazena timestamps via func.now() em UTC, entao todas as
    comparacoes devem usar UTC para evitar divergencias de fuso horario.
    """
    agora = datetime.utcnow()
    hoje = agora.date()

    if periodo == "hoje":
        inicio = datetime.combine(hoje, datetime.min.time())
        fim = agora
        ontem = hoje - timedelta(days=1)
        inicio_ant = datetime.combine(ontem, datetime.min.time())
        fim_ant = datetime.combine(ontem, datetime.max.time())

    elif periodo == "semana":
        inicio = datetime.combine(hoje - timedelta(days=hoje.weekday()), datetime.min.time())
        fim = agora
        inicio_ant = inicio - timedelta(days=7)
        fim_ant = datetime.combine(inicio.date() - timedelta(days=1), datetime.max.time())

    else:  # mes
        inicio = datetime.combine(hoje.replace(day=1), datetime.min.time())
        fim = agora
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

def get_meu_resumo(db: Session, periodo: str, funcionario_id: int) -> MeuResumoStats:
    """Stats pessoais do funcionario logado, filtradas pelo seu ID."""
    inicio, fim, _, _ = _calcular_periodo(periodo)
    dados = dashboard_crud.get_meu_resumo_stats(db, inicio, fim, funcionario_id)
    return MeuResumoStats(
        minhas_vendas_valor=dados.minhas_vendas_valor,
        minhas_vendas_count=dados.minhas_vendas_count,
        minhas_os_abertas=dados.minhas_os_abertas,
        minhas_os_concluidas=dados.minhas_os_concluidas,
    )


def get_minhas_os_vencendo(db: Session, funcionario_id: int) -> OSVencendoResponse:
    """OS do funcionario proximas/passadas do prazo."""
    rows = dashboard_crud.get_minhas_os_vencendo(db, funcionario_id)
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


def get_minhas_ultimas_vendas(db: Session, funcionario_id: int) -> UltimasVendasResponse:
    """Ultimas vendas do funcionario logado."""
    rows = dashboard_crud.get_minhas_ultimas_vendas(db, funcionario_id)
    items = [
        UltimaVendaItem(
            id=row.id,
            cliente_nome=row.cliente_nome,
            total=row.total,
            status=row.status.value,
            criado_em=row.criado_em,
        )
        for row in rows
    ]
    return UltimasVendasResponse(items=items)


def get_minha_fila(db: Session, funcionario_id: int) -> MinhaFilaResponse:
    """Fila de trabalho: OS abertas do funcionario ordenadas por prioridade e prazo."""
    rows = dashboard_crud.get_minha_fila(db, funcionario_id)
    items = [
        MinhaFilaItem(
            numero_os=row.numero_os,
            cliente_nome=row.cliente_nome,
            defeito_relatado=row.defeito_relatado,
            prioridade=row.prioridade.value,
            status=row.status.value,
            data_previsao=row.data_previsao,
        )
        for row in rows
    ]
    return MinhaFilaResponse(items=items)


def get_minhas_os_atrasadas(db: Session, funcionario_id: int) -> OSAtrasadaResponse:
    """OS com prazo vencido do funcionario."""
    rows = dashboard_crud.get_minhas_os_atrasadas(db, funcionario_id)
    hoje = date.today()
    items = [
        OSAtrasadaItem(
            numero_os=row.numero_os,
            cliente_nome=row.cliente_nome,
            defeito_relatado=row.defeito_relatado,
            data_previsao=row.data_previsao,
            dias_atraso=(hoje - row.data_previsao.date()).days,
        )
        for row in rows
    ]
    return OSAtrasadaResponse(items=items, total=len(items))


def get_os_aguardando_retirada(db: Session, funcionario_id: int) -> OSAguardandoRetiradaResponse:
    """OS prontas aguardando retirada do cliente."""
    rows = dashboard_crud.get_os_aguardando_retirada(db, funcionario_id)
    items = [
        OSAguardandoRetiradaItem(
            numero_os=row.numero_os,
            cliente_nome=row.cliente_nome,
            equipamento=f"{row.tipo_equipamento.value} {row.marca} {row.modelo}",
            data_finalizacao=row.data_finalizacao,
        )
        for row in rows
    ]
    return OSAguardandoRetiradaResponse(items=items)


def get_minha_atividade_hoje(db: Session, funcionario_id: int) -> AtividadeHojeResponse:
    """Timeline de vendas e OS do funcionario criadas hoje."""
    vendas = dashboard_crud.get_minhas_vendas_hoje(db, funcionario_id)
    ordens = dashboard_crud.get_minhas_os_hoje(db, funcionario_id)

    itens_venda = [
        AtividadeItem(
            tipo="venda",
            referencia=f"#{row.id}",
            cliente_nome=row.cliente_nome,
            valor=row.total,
            status=row.status.value,
            horario=row.criado_em,
        )
        for row in vendas
    ]

    itens_os = [
        AtividadeItem(
            tipo="os",
            referencia=row.numero_os,
            cliente_nome=row.cliente_nome,
            valor=row.valor_total,
            status=row.status.value,
            horario=row.data_criacao,
        )
        for row in ordens
    ]

    todos = itens_venda + itens_os
    todos.sort(key=lambda x: x.horario, reverse=True)
    return AtividadeHojeResponse(items=todos[:20])


_STATUS_LABELS = {
    "ABERTA": "Aberta",
    "EM_ANDAMENTO": "Em andamento",
    "AGUARDANDO_PECAS": "Aguard. peças",
    "AGUARDANDO_APROVACAO": "Aguard. aprovação",
    "AGUARDANDO_RETIRADA": "Aguard. retirada",
}


def get_ranking_funcionarios(db: Session, periodo: str, empresa_id: int) -> RankingFuncionariosResponse:
    inicio, fim, _, _ = _calcular_periodo(periodo)
    rows = dashboard_crud.get_ranking_funcionarios(db, inicio, fim, empresa_id)
    items = [
        RankingFuncionarioItem(
            posicao=i + 1,
            id=row.id,
            nome=row.nome,
            total_vendas_valor=row.total_vendas_valor,
            qtd_vendas=row.qtd_vendas,
            qtd_os_fechadas=row.qtd_os_fechadas,
        )
        for i, row in enumerate(rows)
    ]
    return RankingFuncionariosResponse(items=items)


def get_os_por_status(db: Session, empresa_id: int) -> OSPorStatusResponse:
    rows = dashboard_crud.get_os_por_status(db, empresa_id)
    items = [
        OSPorStatusItem(
            status=row.status.value,
            status_label=_STATUS_LABELS.get(row.status.value, row.status.value),
            count=row.count,
        )
        for row in rows
    ]
    return OSPorStatusResponse(items=items, total_ativas=sum(i.count for i in items))


def get_formas_pagamento(db: Session, periodo: str, empresa_id: int) -> FormasPagamentoResponse:
    inicio, fim, _, _ = _calcular_periodo(periodo)
    vendas_rows = dashboard_crud.get_formas_pagamento_vendas(db, inicio, fim, empresa_id)
    os_rows = dashboard_crud.get_formas_pagamento_os(db, inicio, fim, empresa_id)

    totais: dict[str, int] = {}
    for row in vendas_rows:
        totais[row.nome] = totais.get(row.nome, 0) + (row.total or 0)
    for row in os_rows:
        totais[row.nome] = totais.get(row.nome, 0) + (row.total or 0)

    items = [
        FormaPagamentoItem(nome=nome, valor_total=valor)
        for nome, valor in sorted(totais.items(), key=lambda x: x[1], reverse=True)
    ]
    return FormasPagamentoResponse(items=items, total=sum(i.valor_total for i in items))


def get_os_atrasadas_empresa(db: Session, empresa_id: int) -> OSAtrasadaEmpresaResponse:
    rows = dashboard_crud.get_os_atrasadas_empresa(db, empresa_id)
    hoje = date.today()
    items = [
        OSAtrasadaEmpresaItem(
            numero_os=row.numero_os,
            cliente_nome=row.cliente_nome,
            funcionario_nome=row.funcionario_nome,
            defeito_relatado=row.defeito_relatado,
            data_previsao=row.data_previsao,
            dias_atraso=(hoje - row.data_previsao.date()).days,
        )
        for row in rows
    ]
    return OSAtrasadaEmpresaResponse(items=items, total=len(items))


def get_ultimas_vendas(db: Session, empresa_id: int) -> UltimasVendasResponse:
    """Retorna as vendas mais recentes."""
    rows = dashboard_crud.get_ultimas_vendas(db, empresa_id)

    items = [
        UltimaVendaItem(
            id=row.id,
            cliente_nome=row.cliente_nome,
            total=row.total,
            status=row.status.value,
            criado_em=row.criado_em,
        )
        for row in rows
    ]

    return UltimasVendasResponse(items=items)
