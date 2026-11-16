# ---------------------------------------------------------------------------
# ARQUIVO: services/relatorio/__init__.py
# DESCRICAO: Regras do modulo de Relatorios. Monta o relatorio de faturamento
#            reusando as agregacoes do dashboard e a serie por dia do crud proprio.
#
# REGRA DO DONO (ver endpoints/relatorios.py e test/api/v1/test_relatorio.py):
# relatorio completo da loja e so do Master; o funcionario recebe so o que ele
# fez (get_faturamento_pessoal). O gate e o is_master, nunca o nome do cargo.
#
# Era um arquivo so (relatorio.py) ate 13/10/2026; virou pacote:
#   faturamento.py    - faturamento da loja e o pessoal do funcionario
#   equipe.py         - ranking, comissao e extrato do funcionario
#   estoque.py        - curva ABC, reposicao e parados
#   regras_preco.py   - vendas por regra de preco (R1/R2/R3)
#   contador.py       - receita segregada para o PGDAS-D
#   os_performance.py - desempenho de OS
#   acesso_comissoes.py - cargos que o Master liberou para ver as comissoes
#                       (fica no submodulo, sem reexport)
#
# Este __init__ reexporta tudo: `from app.services import relatorio` continua
# valendo como antes.
# ---------------------------------------------------------------------------

from app.services.relatorio.faturamento import (
    _serie_por_dia,
    get_faturamento_pessoal,
    get_faturamento,
)

from app.services.relatorio.equipe import (
    get_ranking,
    get_comissao,
    get_extrato_funcionario,
    _data_local,
)

from app.services.relatorio.estoque import (
    _ABC_CORTE_A,
    _ABC_CORTE_B,
    _classe_abc,
    get_estoque,
)

from app.services.relatorio.regras_preco import (
    get_regras_preco,
)

from app.services.relatorio.contador import (
    _GRUPOS,
    get_contador,
)

from app.services.relatorio.os_performance import (
    _duracao_horas,
    get_os_performance,
)

__all__ = [
    "_serie_por_dia",
    "get_faturamento_pessoal",
    "get_faturamento",
    "get_ranking",
    "get_comissao",
    "get_extrato_funcionario",
    "_data_local",
    "_ABC_CORTE_A",
    "_ABC_CORTE_B",
    "_classe_abc",
    "get_estoque",
    "get_regras_preco",
    "_GRUPOS",
    "get_contador",
    "_duracao_horas",
    "get_os_performance",
]
