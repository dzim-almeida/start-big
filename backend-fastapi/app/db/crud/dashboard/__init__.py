# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/dashboard/__init__.py
# DESCRICAO: Queries SQL via SQLAlchemy para o Dashboard.
#            Apenas leitura - sem efeito colateral no banco.
#
# Era um arquivo so (dashboard.py) ate 12/10/2026; virou pacote por assunto:
#   indicadores.py  - totais do periodo e formas de pagamento (tambem usados
#                     pelo financeiro e pelos relatorios)
#   empresa.py      - visao do dono: OS vencendo/atrasadas, estoque baixo,
#                     ranking, OS por status, ultimas vendas
#   meu_painel.py   - visao do funcionario logado
#
# Este __init__ reexporta tudo: quem faz `from app.db.crud import dashboard`
# continua chamando `dashboard_crud.<funcao>` como antes.
# ---------------------------------------------------------------------------

from app.db.crud.dashboard.indicadores import (
    StatsAgregados,
    get_stats_agregados,
    get_formas_pagamento_vendas,
    get_formas_pagamento_os,
)

from app.db.crud.dashboard.empresa import (
    get_os_vencendo,
    get_estoque_baixo,
    get_ranking_funcionarios,
    get_os_por_status,
    get_os_atrasadas_empresa,
    get_ultimas_vendas,
)

from app.db.crud.dashboard.meu_painel import (
    MeuResumoAgregado,
    get_meu_resumo_stats,
    get_minhas_vendas_por_dia,
    get_minhas_os_por_dia,
    get_minhas_os_vencendo,
    get_minha_fila,
    get_minhas_os_atrasadas,
    get_os_aguardando_retirada,
    get_minhas_vendas_hoje,
    get_minhas_os_hoje,
    get_minhas_ultimas_vendas,
)

__all__ = [
    "StatsAgregados",
    "get_stats_agregados",
    "get_formas_pagamento_vendas",
    "get_formas_pagamento_os",
    "get_os_vencendo",
    "get_estoque_baixo",
    "get_ranking_funcionarios",
    "get_os_por_status",
    "get_os_atrasadas_empresa",
    "get_ultimas_vendas",
    "MeuResumoAgregado",
    "get_meu_resumo_stats",
    "get_minhas_vendas_por_dia",
    "get_minhas_os_por_dia",
    "get_minhas_os_vencendo",
    "get_minha_fila",
    "get_minhas_os_atrasadas",
    "get_os_aguardando_retirada",
    "get_minhas_vendas_hoje",
    "get_minhas_os_hoje",
    "get_minhas_ultimas_vendas",
]
