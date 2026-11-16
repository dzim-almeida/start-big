# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/relatorio/__init__.py
# DESCRICAO: Queries agregadas do modulo de Relatorios. Apenas leitura.
#            As metricas consolidadas (totais, ticket, formas de pagamento)
#            reusam crud/dashboard; aqui ficam as series temporais (por dia).
#
# Convencao de data: timestamps sao gravados em UTC (func.now()); os filtros
# de periodo usam limites UTC, iguais aos do dashboard, para bater com ele.
#
# Era um arquivo so (relatorio.py) ate 13/10/2026; virou pacote:
#   faturamento.py    - series por dia e juros por responsavel
#   equipe.py         - ranking, base de comissao, servicos e vendas do funcionario
#   estoque.py        - vendas por produto e produtos em estoque
#   os_performance.py - OS finalizadas, abertas e por status
#   regras_preco.py   - vendas com regra de preco
#   contador.py       - linhas fiscais de venda e OS para o PGDAS-D
#   custo.py          - CMV (era db/crud/relatorio_custo.py)
#
# Este __init__ reexporta o que era relatorio.py. O custo fica no submodulo:
# `from app.db.crud.relatorio import custo as custo_crud`.
# ---------------------------------------------------------------------------

from app.db.crud.relatorio.faturamento import (
    get_faturamento_vendas_por_dia,
    get_faturamento_os_por_dia,
    get_juros_vendas_por_responsavel,
    get_juros_os_por_responsavel,
)

from app.db.crud.relatorio.equipe import (
    get_ranking_faturamento,
    get_comissao_base,
    get_servicos_do_funcionario,
    get_vendas_do_funcionario,
)

from app.db.crud.relatorio.estoque import (
    get_vendas_por_produto,
    get_produtos_estoque,
)

from app.db.crud.relatorio.os_performance import (
    get_os_finalizadas_periodo,
    get_os_abertas_count_periodo,
    get_os_por_status,
)

from app.db.crud.relatorio.regras_preco import (
    get_vendas_por_regra_preco,
    get_vendas_com_regra_count,
    get_vendas_com_regra_por_regra,
)

from app.db.crud.relatorio.contador import (
    get_linhas_venda_fiscal,
    get_extras_vendas,
    get_itens_os_fiscal,
    get_os_finalizadas_sem_itens_total,
)

__all__ = [
    "get_faturamento_vendas_por_dia",
    "get_faturamento_os_por_dia",
    "get_juros_vendas_por_responsavel",
    "get_juros_os_por_responsavel",
    "get_ranking_faturamento",
    "get_comissao_base",
    "get_servicos_do_funcionario",
    "get_vendas_do_funcionario",
    "get_vendas_por_produto",
    "get_produtos_estoque",
    "get_os_finalizadas_periodo",
    "get_os_abertas_count_periodo",
    "get_os_por_status",
    "get_vendas_por_regra_preco",
    "get_vendas_com_regra_count",
    "get_vendas_com_regra_por_regra",
    "get_linhas_venda_fiscal",
    "get_extras_vendas",
    "get_itens_os_fiscal",
    "get_os_finalizadas_sem_itens_total",
]
