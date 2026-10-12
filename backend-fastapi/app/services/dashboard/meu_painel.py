# ---------------------------------------------------------------------------
# ARQUIVO: services/dashboard/meu_painel.py
# DESCRICAO: Dashboard - visao do funcionario logado ("meu" painel).
# ---------------------------------------------------------------------------

from datetime import date

from sqlalchemy.orm import Session

from app.db.crud import dashboard as dashboard_crud
from app.schemas.dashboard import (
    TendenciaResponse,
    OSVencendoItem,
    OSVencendoResponse,
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
)
from app.services.dashboard.periodo import _calcular_periodo, _calcular_urgencia, _montar_serie


# ===========================================================================
# MEU PAINEL — resumo, tendencia, OS e vendas do funcionario logado
# ===========================================================================

def get_meu_resumo(db: Session, periodo: str, funcionario_id: int) -> MeuResumoStats:
    """Stats pessoais do funcionario logado, filtradas pelo seu ID."""
    inicio, fim, _, _ = _calcular_periodo(periodo)
    dados = dashboard_crud.get_meu_resumo_stats(db, inicio, fim, funcionario_id)
    return MeuResumoStats(
        meu_faturamento=dados.minhas_vendas_valor + dados.minhas_os_valor,
        minhas_vendas_valor=dados.minhas_vendas_valor,
        minhas_vendas_count=dados.minhas_vendas_count,
        minhas_os_valor=dados.minhas_os_valor,
        minhas_os_abertas=dados.minhas_os_abertas,
        minhas_os_concluidas=dados.minhas_os_concluidas,
    )


def get_minha_tendencia(db: Session, periodo: str, funcionario_id: int) -> TendenciaResponse:
    """Serie de faturamento (minhas vendas + minhas OS) por dia do FUNCIONARIO."""
    inicio, fim, _, _ = _calcular_periodo(periodo)
    vendas_rows = dashboard_crud.get_minhas_vendas_por_dia(db, inicio, fim, funcionario_id)
    os_rows = dashboard_crud.get_minhas_os_por_dia(db, inicio, fim, funcionario_id)
    return TendenciaResponse(items=_montar_serie(inicio, fim, vendas_rows, os_rows))


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
    items = []
    for os_obj, cliente_nome in rows:
        obj = os_obj.objeto
        tipo_str = obj.tipo_equipamento.value if hasattr(obj.tipo_equipamento, 'value') else str(obj.tipo_equipamento)

        # Se for um veículo com placa cadastrada nos dados_adicionais, exibe na listagem
        if obj.dados_adicionais and "placa" in obj.dados_adicionais:
            tipo_str = f"Veículo ({obj.dados_adicionais['placa']})"

        items.append(OSAguardandoRetiradaItem(
            numero_os=os_obj.numero_os,
            cliente_nome=cliente_nome,
            equipamento=f"{tipo_str} {obj.marca} {obj.modelo}",
            data_finalizacao=os_obj.data_finalizacao,
        ))
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
