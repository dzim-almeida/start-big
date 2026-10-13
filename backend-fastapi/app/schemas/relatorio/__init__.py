# ---------------------------------------------------------------------------
# ARQUIVO: schemas/relatorio/__init__.py
# DESCRICAO: Schemas de resposta do modulo de Relatorios.
#            Todos os valores monetarios sao INTEIROS EM CENTAVOS.
#
# Era um arquivo so (relatorio.py) ate 13/10/2026; virou pacote:
#   faturamento.py, equipe.py, estoque.py, regras_preco.py, contador.py,
#   os_performance.py (os mesmos assuntos do services/relatorio/).
#
# Este __init__ reexporta tudo: `from app.schemas.relatorio import ...` continua
# valendo como antes.
# ---------------------------------------------------------------------------

from app.schemas.relatorio.faturamento import (
    FaturamentoDiaItem,
    FormaPagamentoResumo,
    RelatorioFaturamento,
)

from app.schemas.relatorio.equipe import (
    RankingFuncionarioItem,
    RelatorioRanking,
    ComissaoFuncionarioItem,
    RelatorioComissao,
    ExtratoServicoItem,
    ExtratoVendaItem,
    RelatorioExtratoFuncionario,
)

from app.schemas.relatorio.estoque import (
    EstoqueAbcItem,
    EstoqueReposicaoItem,
    EstoqueParadoItem,
    RelatorioEstoque,
)

from app.schemas.relatorio.regras_preco import (
    RegraPrecoResumo,
    RegraPrecoProdutoItem,
    RelatorioRegrasPreco,
)

from app.schemas.relatorio.contador import (
    ReceitaGrupoItem,
    ProdutoSemClassificacaoItem,
    RelatorioContador,
)

from app.schemas.relatorio.os_performance import (
    OSReparoResumo,
    OSStatusItem,
    OSTecnicoItem,
    RelatorioOSPerformance,
)

__all__ = [
    "FaturamentoDiaItem",
    "FormaPagamentoResumo",
    "RelatorioFaturamento",
    "RankingFuncionarioItem",
    "RelatorioRanking",
    "ComissaoFuncionarioItem",
    "RelatorioComissao",
    "ExtratoServicoItem",
    "ExtratoVendaItem",
    "RelatorioExtratoFuncionario",
    "EstoqueAbcItem",
    "EstoqueReposicaoItem",
    "EstoqueParadoItem",
    "RelatorioEstoque",
    "RegraPrecoResumo",
    "RegraPrecoProdutoItem",
    "RelatorioRegrasPreco",
    "ReceitaGrupoItem",
    "ProdutoSemClassificacaoItem",
    "RelatorioContador",
    "OSReparoResumo",
    "OSStatusItem",
    "OSTecnicoItem",
    "RelatorioOSPerformance",
]
