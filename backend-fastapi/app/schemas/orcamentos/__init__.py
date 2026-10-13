# ---------------------------------------------------------------------------
# ARQUIVO: schemas/orcamentos/__init__.py
# DESCRICAO: Schemas do orcamento.
#
# Era um arquivo so (orcamentos.py) ate 13/10/2026; virou pacote:
#   itens.py    - itens do orcamento
#   cadastro.py - criar, editar e ler o orcamento
#   resumo.py   - resumos financeiro e por status
#   acoes.py    - converter em venda
#   consulta.py - filtros e listagem
#
# Este __init__ reexporta tudo: `from app.schemas.orcamentos import ...`
# continua valendo como antes.
# ---------------------------------------------------------------------------

from app.schemas.orcamentos.itens import (
    OrcamentoProdutoCreate,
    OrcamentoProdutoUpdate,
    OrcamentoProdutoRead,
)

from app.schemas.orcamentos.cadastro import (
    OrcamentoCreate,
    OrcamentoUpdate,
    FuncionarioOrcamentoRead,
    OrcamentoSimpleRead,
    OrcamentoRead,
)

from app.schemas.orcamentos.resumo import (
    OrcamentoFinanceSummary,
    OrcamentoProdutosAlterSummary,
    OrcamentoStatusSummary,
)

from app.schemas.orcamentos.acoes import (
    ConverterOrcamentoPayload,
)

from app.schemas.orcamentos.consulta import (
    OrcamentoSearchFilters,
    OrcamentoListRead,
)

__all__ = [
    "OrcamentoProdutoCreate",
    "OrcamentoProdutoUpdate",
    "OrcamentoProdutoRead",
    "OrcamentoCreate",
    "OrcamentoUpdate",
    "FuncionarioOrcamentoRead",
    "OrcamentoSimpleRead",
    "OrcamentoRead",
    "OrcamentoFinanceSummary",
    "OrcamentoProdutosAlterSummary",
    "OrcamentoStatusSummary",
    "ConverterOrcamentoPayload",
    "OrcamentoSearchFilters",
    "OrcamentoListRead",
]
