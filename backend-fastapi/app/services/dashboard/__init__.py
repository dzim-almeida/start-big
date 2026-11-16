# ---------------------------------------------------------------------------
# ARQUIVO: services/dashboard/__init__.py
# DESCRICAO: Logica de negocio para o Dashboard.
#            Calcula periodos, variacoes percentuais e bandas de urgencia.
#
# Era um arquivo so (dashboard.py) ate 12/10/2026; virou pacote por assunto:
#   periodo.py     - helpers: periodo, variacao, urgencia, ticket medio, serie
#   empresa.py     - visao da empresa (dono/master)
#   meu_painel.py  - visao do funcionario logado
#
# Este __init__ reexporta tudo: quem faz `from app.services import dashboard`
# continua chamando `dashboard_service.<funcao>` como antes.
# ---------------------------------------------------------------------------

from app.services.dashboard.periodo import (
    _calcular_periodo,
    _calcular_variacao,
    _calcular_urgencia,
    _calcular_ticket_medio,
    _montar_serie,
)

from app.services.dashboard.empresa import (
    get_dashboard_stats,
    get_os_vencendo,
    get_estoque_baixo,
    get_tendencia,
    _STATUS_LABELS,
    get_ranking_funcionarios,
    get_os_por_status,
    get_formas_pagamento,
    get_os_atrasadas_empresa,
    get_ultimas_vendas,
)

from app.services.dashboard.meu_painel import (
    get_meu_resumo,
    get_minha_tendencia,
    get_minhas_os_vencendo,
    get_minhas_ultimas_vendas,
    get_minha_fila,
    get_minhas_os_atrasadas,
    get_os_aguardando_retirada,
    get_minha_atividade_hoje,
)

__all__ = [
    "_calcular_periodo",
    "_calcular_variacao",
    "_calcular_urgencia",
    "_calcular_ticket_medio",
    "_montar_serie",
    "get_dashboard_stats",
    "get_os_vencendo",
    "get_estoque_baixo",
    "get_tendencia",
    "_STATUS_LABELS",
    "get_ranking_funcionarios",
    "get_os_por_status",
    "get_formas_pagamento",
    "get_os_atrasadas_empresa",
    "get_ultimas_vendas",
    "get_meu_resumo",
    "get_minha_tendencia",
    "get_minhas_os_vencendo",
    "get_minhas_ultimas_vendas",
    "get_minha_fila",
    "get_minhas_os_atrasadas",
    "get_os_aguardando_retirada",
    "get_minha_atividade_hoje",
]
