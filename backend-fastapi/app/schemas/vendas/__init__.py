# ---------------------------------------------------------------------------
# ARQUIVO: schemas/vendas/__init__.py
# DESCRICAO: Schemas da venda.
#
# Era um arquivo so (vendas.py) ate 13/10/2026; virou pacote:
#   itens.py           - itens da venda
#   pagamento.py       - pagamentos
#   cadastro.py        - a venda (criar, editar, ler)
#   resumo.py          - resumos financeiro e por status
#   acoes.py           - finalizar, cancelar, reabrir
#   consulta.py        - filtros e listagem
#   nota_fiscal.py     - dados fiscais (era schemas/venda_nota_fiscal.py)
#   correcao_fiscal.py - correcao fiscal (era schemas/venda_correcao_fiscal.py)
#
# Este __init__ reexporta tudo: `from app.schemas.vendas import ...` continua
# valendo como antes.
# ---------------------------------------------------------------------------

from app.schemas.vendas.itens import (
    ProdutoVendaCreate,
    ProdutoVendaUpdate,
    ProdutoVendaRead,
)

from app.schemas.vendas.pagamento import (
    PagamentoVendaCreate,
    PagamentoVendaRead,
)

from app.schemas.vendas.cadastro import (
    VendaCreate,
    VendaUpdate,
    FuncionarioVendaRead,
    VendaSimpleRead,
    VendaRead,
)

from app.schemas.vendas.resumo import (
    VendaFinanceSummary,
    VendaStatusSummary,
    ProdutosAlterSummary,
)

from app.schemas.vendas.acoes import (
    FinalizarVendaPayload,
    CancelarVendaPayload,
    ReabrirVendaPayload,
)

from app.schemas.vendas.consulta import (
    VendaSearchFilters,
    VendaListRead,
)

from app.schemas.vendas.nota_fiscal import (
    VendaNotaFiscalUpdate,
    VendaNotaFiscalRead,
)

from app.schemas.vendas.correcao_fiscal import (
    VendaCorrecaoFiscalPayload,
    VendaCorrecaoFiscalRead,
)

__all__ = [
    "ProdutoVendaCreate",
    "ProdutoVendaUpdate",
    "ProdutoVendaRead",
    "PagamentoVendaCreate",
    "PagamentoVendaRead",
    "VendaCreate",
    "VendaUpdate",
    "FuncionarioVendaRead",
    "VendaSimpleRead",
    "VendaRead",
    "VendaFinanceSummary",
    "VendaStatusSummary",
    "ProdutosAlterSummary",
    "FinalizarVendaPayload",
    "CancelarVendaPayload",
    "ReabrirVendaPayload",
    "VendaSearchFilters",
    "VendaListRead",
    "VendaNotaFiscalUpdate",
    "VendaNotaFiscalRead",
    "VendaCorrecaoFiscalPayload",
    "VendaCorrecaoFiscalRead",
]
