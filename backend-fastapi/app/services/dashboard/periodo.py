# ---------------------------------------------------------------------------
# ARQUIVO: services/dashboard/periodo.py
# DESCRICAO: Dashboard - helpers de periodo, variacao percentual, banda de
#            urgencia, ticket medio e montagem da serie por dia.
# ---------------------------------------------------------------------------

from datetime import datetime, date, timedelta
from calendar import monthrange


from app.core.tempo import agora_utc, fim_do_dia_utc, hoje_local, inicio_do_dia_utc
from app.db.crud import dashboard as dashboard_crud
from app.schemas.dashboard import (
    TendenciaDiaItem,
)


# ===========================================================================
# HELPERS
# ===========================================================================

def _calcular_periodo(periodo: str) -> tuple[datetime, datetime, datetime, datetime]:
    """
    Retorna (inicio_atual, fim_atual, inicio_anterior, fim_anterior) em UTC.

    As BORDAS sao o dia da loja; a SAIDA e em UTC, porque e assim que o banco
    grava (`func.now()` no SQLite e UTC).

    Antes isto usava `datetime.utcnow().date()` como "hoje", o que fazia o dia
    virar junto com o UTC: no Brasil (UTC-3), as 21h o dashboard ja trocava de
    dia e o faturamento da noite sumia da tela do lojista, reaparecendo no dia
    seguinte. O dia agora vira quando vira para quem esta na loja.
    """
    agora = agora_utc()
    hoje = hoje_local()

    if periodo == "hoje":
        inicio = inicio_do_dia_utc(hoje)
        fim = agora
        ontem = hoje - timedelta(days=1)
        inicio_ant = inicio_do_dia_utc(ontem)
        fim_ant = fim_do_dia_utc(ontem)

    elif periodo == "semana":
        primeiro_dia = hoje - timedelta(days=hoje.weekday())
        inicio = inicio_do_dia_utc(primeiro_dia)
        fim = agora
        inicio_ant = inicio_do_dia_utc(primeiro_dia - timedelta(days=7))
        fim_ant = fim_do_dia_utc(primeiro_dia - timedelta(days=1))

    else:  # mes
        inicio = inicio_do_dia_utc(hoje.replace(day=1))
        fim = agora
        if hoje.month == 1:
            mes_ant = 12
            ano_ant = hoje.year - 1
        else:
            mes_ant = hoje.month - 1
            ano_ant = hoje.year
        ultimo_dia_ant = monthrange(ano_ant, mes_ant)[1]
        inicio_ant = inicio_do_dia_utc(date(ano_ant, mes_ant, 1))
        fim_ant = fim_do_dia_utc(date(ano_ant, mes_ant, ultimo_dia_ant))

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
# SERIE POR DIA — base das tendencias (grafico do topo)
# ===========================================================================

def _montar_serie(
    inicio: datetime, fim: datetime, vendas_rows, os_rows
) -> list[TendenciaDiaItem]:
    """Monta a serie diaria continua (dias sem movimento viram zero) a partir das
    linhas agrupadas por dia de vendas e OS. Mantem o grafico sem buracos."""
    vendas_dia = {str(r.dia): (r.total or 0) for r in vendas_rows}
    os_dia = {str(r.dia): (r.total or 0) for r in os_rows}

    itens: list[TendenciaDiaItem] = []
    dia = inicio.date()
    fim_dia = fim.date()
    while dia <= fim_dia:
        chave = dia.isoformat()
        tv = vendas_dia.get(chave, 0)
        to = os_dia.get(chave, 0)
        itens.append(TendenciaDiaItem(dia=dia, total_vendas=tv, total_os=to, total_geral=tv + to))
        dia += timedelta(days=1)
    return itens
