# ---------------------------------------------------------------------------
# ARQUIVO: schemas/financeiro/__init__.py
# DESCRICAO: Schemas Pydantic da gestao financeira.
#
# Ate 12/10/2026 eram cinco arquivos soltos em schemas/ (financeiro.py,
# conta_pagar.py, conta_receber.py, conta_bancaria.py e plano_conta.py).
# Viraram este pacote; este __init__ reexporta tudo: importe de
# `app.schemas.financeiro`.
# ---------------------------------------------------------------------------

from app.schemas.financeiro.resumo import (
    DespesaPorCategoria,
    AlertaFinanceiro,
    ResumoFinanceiro,
)

from app.schemas.financeiro.fluxo_caixa import (
    FluxoLancamento,
    FluxoDia,
    FluxoCaixa,
)

from app.schemas.financeiro.conciliacao import (
    ConciliacaoItem,
    ConciliacaoDia,
    Conciliacao,
    ConciliacaoBaixaLote,
    ConciliacaoResultado,
)

from app.schemas.financeiro.extrato import (
    ExtratoLinha,
    Extrato,
)

from app.schemas.financeiro.analise import (
    SerieOrigem,
    SerieMes,
    Serie,
    ProjecaoMes,
    Projecao,
)

from app.schemas.financeiro.custo import (
    CustoDetalheLinha,
    CustoDetalhe,
)

from app.schemas.financeiro.conta_pagar import (
    ContaPagarCreate,
    ContaPagarUpdate,
    ContaPagarBaixa,
    ContaPagarEstorno,
    ContaPagarRead,
    ContaPagarListagem,
    HistoricoFinanceiroRead,
)

from app.schemas.financeiro.conta_receber import (
    ContaReceberCreate,
    ContaReceberUpdate,
    ContaReceberBaixa,
    ContaReceberEstorno,
    ContaReceberRead,
    ContaReceberListagem,
)

from app.schemas.financeiro.conta_bancaria import (
    ContaBancariaCreate,
    ContaBancariaUpdate,
    ContaBancariaRead,
)

from app.schemas.financeiro.plano_conta import (
    PlanoContaCreate,
    PlanoContaUpdate,
    PlanoContaRead,
)

__all__ = [
    "DespesaPorCategoria",
    "AlertaFinanceiro",
    "ResumoFinanceiro",
    "FluxoLancamento",
    "FluxoDia",
    "FluxoCaixa",
    "ConciliacaoItem",
    "ConciliacaoDia",
    "Conciliacao",
    "ConciliacaoBaixaLote",
    "ConciliacaoResultado",
    "ExtratoLinha",
    "Extrato",
    "SerieOrigem",
    "SerieMes",
    "Serie",
    "ProjecaoMes",
    "Projecao",
    "CustoDetalheLinha",
    "CustoDetalhe",
    "ContaPagarCreate",
    "ContaPagarUpdate",
    "ContaPagarBaixa",
    "ContaPagarEstorno",
    "ContaPagarRead",
    "ContaPagarListagem",
    "HistoricoFinanceiroRead",
    "ContaReceberCreate",
    "ContaReceberUpdate",
    "ContaReceberBaixa",
    "ContaReceberEstorno",
    "ContaReceberRead",
    "ContaReceberListagem",
    "ContaBancariaCreate",
    "ContaBancariaUpdate",
    "ContaBancariaRead",
    "PlanoContaCreate",
    "PlanoContaUpdate",
    "PlanoContaRead",
]
