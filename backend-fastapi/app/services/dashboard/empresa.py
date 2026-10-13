# ---------------------------------------------------------------------------
# ARQUIVO: services/dashboard/empresa.py
# DESCRICAO: Dashboard - visao da empresa (dono/master): stats, tendencia,
#            OS vencendo/atrasadas, estoque baixo, ranking, OS por status,
#            formas de pagamento e ultimas vendas.
# ---------------------------------------------------------------------------

from datetime import date

from sqlalchemy.orm import Session

from app.core import segmentos as reg                      # registry (dado dos segmentos)
from app.db.crud import dashboard as dashboard_crud
from app.db.crud import relatorio as relatorio_crud
from app.schemas.dashboard.paineis import (
    DashboardStats,
    TendenciaResponse,
    OSVencendoItem,
    OSVencendoResponse,
    EstoqueBaixoItem,
    EstoqueBaixoResponse,
    UltimaVendaItem,
    UltimasVendasResponse,
    RankingFuncionarioItem,
    RankingFuncionariosResponse,
    OSPorStatusItem,
    OSPorStatusResponse,
    FormaPagamentoItem,
    FormasPagamentoResponse,
    OSAtrasadaEmpresaItem,
    OSAtrasadaEmpresaResponse,
)
from app.services.sistema import segmentos as segmentos_service    # descobre o segmento da empresa
from app.services.dashboard.periodo import _calcular_periodo, _calcular_ticket_medio, _calcular_urgencia, _calcular_variacao, _montar_serie


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

    # Faturamento total = vendas + OS finalizadas (os_soma ja e o faturamento de OS).
    fat_atual = atual.vendas_total + atual.os_soma
    fat_ant = anterior.vendas_total + anterior.os_soma

    return DashboardStats(
        faturamento_total=fat_atual,
        faturamento_total_variacao=_calcular_variacao(fat_atual, fat_ant),
        vendas_total=atual.vendas_total,
        vendas_total_variacao=_calcular_variacao(atual.vendas_total, anterior.vendas_total),
        vendas_count=atual.vendas_count,
        vendas_count_variacao=_calcular_variacao(atual.vendas_count, anterior.vendas_count),
        os_total=atual.os_soma,
        os_total_variacao=_calcular_variacao(atual.os_soma, anterior.os_soma),
        # OS FINALIZADAS, não criadas. Este painel é de resultados: ao lado
        # aparecem as vendas finalizadas e o faturamento de serviços do período.
        # Contando as criadas, uma OS aberta na semana passada e fechada hoje
        # deixava a tela dizendo "0 OS" logo acima de "Serviços R$ 51,10".
        os_count=atual.os_finalizadas_count,
        os_count_variacao=_calcular_variacao(atual.os_finalizadas_count, anterior.os_finalizadas_count),
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
# TENDENCIA — serie de faturamento por dia (grafico do topo)
# ===========================================================================

def get_tendencia(db: Session, periodo: str, empresa_id: int) -> TendenciaResponse:
    """Serie de faturamento (vendas + OS) por dia da LOJA no periodo. Reusa o crud
    por-dia do modulo de relatorios para nao duplicar as agregacoes."""
    inicio, fim, _, _ = _calcular_periodo(periodo)
    vendas_rows = relatorio_crud.get_faturamento_vendas_por_dia(db, inicio, fim, empresa_id)
    os_rows = relatorio_crud.get_faturamento_os_por_dia(db, inicio, fim, empresa_id)
    return TendenciaResponse(items=_montar_serie(inicio, fim, vendas_rows, os_rows))


# ===========================================================================
# MASTER — ranking, OS por status, formas de pagamento, OS atrasadas
# ===========================================================================

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

    items: list[RankingFuncionarioItem] = []
    posicao = 0
    for row in rows:
        total_geral = row.total_vendas_valor + row.total_os_valor
        # Esconde quem esta 100% zerado no periodo (sem venda e sem OS) — tira o ruido.
        if total_geral == 0 and row.qtd_vendas == 0 and row.qtd_os_fechadas == 0:
            continue
        posicao += 1
        items.append(
            RankingFuncionarioItem(
                posicao=posicao,
                id=row.id,
                nome=row.nome,
                total_vendas_valor=row.total_vendas_valor,
                total_os_valor=row.total_os_valor,
                total_geral=total_geral,
                qtd_vendas=row.qtd_vendas,
                qtd_os_fechadas=row.qtd_os_fechadas,
            )
        )
    return RankingFuncionariosResponse(items=items)


def get_os_por_status(db: Session, empresa_id: int) -> OSPorStatusResponse:
    rows = dashboard_crud.get_os_por_status(db, empresa_id)    # contagem por status (sem mudanca)
    segmento = segmentos_service.get_segmento_atual(db)        # uma consulta, fora do laco
    items = [
        OSPorStatusItem(
            status=row.status.value,                           # sempre o codigo do enum
            # 1o: o texto curto que o segmento declarou (Spec 01A);
            # 2o: a tabela padrao de hoje (_STATUS_LABELS, igual para os outros segmentos);
            # 3o: o proprio codigo, como ja era antes da Spec 01A.
            status_label=(
                reg.rotulo_status(segmento, row.status.value, curto=True)
                or _STATUS_LABELS.get(row.status.value, row.status.value)
            ),
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


# ===========================================================================
# ULTIMAS VENDAS
# ===========================================================================

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
