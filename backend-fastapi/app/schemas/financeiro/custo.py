# ---------------------------------------------------------------------------
# ARQUIVO: schemas/financeiro/custo.py
# DESCRICAO: Financeiro - schemas do detalhe de custo.
# ---------------------------------------------------------------------------

from datetime import date, datetime
from pydantic import BaseModel, Field


# ===========================================================================
# DETALHE DO CUSTO — o que abre quando se clica em "Custo do que vendeu"
# ===========================================================================

class CustoDetalheLinha(BaseModel):
    """Uma origem de custo do período.

    Existe porque o card mostrava um total e nada mais. Em 05/09/2026 o dono
    passou uma tarde conferindo R$ 846 de CMV no papel, OS por OS, e o que
    faltava era um custo lançado num item avulso — invisível depois que a OS
    finaliza. Um número que não se consegue abrir não se consegue confiar.
    """

    data: datetime | None = Field(None, description="Data da venda ou da finalização da OS")
    origem: str = Field(..., description="VENDA ou OS")
    referencia: str = Field(..., description="Número da venda ou da OS")
    descricao: str = Field(..., description="Produto ou item que gerou o custo")
    quantidade: float
    custo: int = Field(
        ...,
        description=(
            "Custo desta linha (centavos). NEGATIVO quando é estorno — venda "
            "cancelada ou OS reaberta devolvem a peça e o custo sai da conta"
        ),
    )
    fonte: str = Field(
        ...,
        description=(
            "ESTOQUE (custo congelado no livro, na baixa), DECLARADO (o 'Custo "
            "para a loja' digitado à mão no item) ou ESTORNO (devolução)"
        ),
    )


class CustoDetalhe(BaseModel):
    """O detalhamento do CMV do período, linha a linha."""

    periodo_inicio: date
    periodo_fim: date
    total: int = Field(
        ...,
        description=(
            "Soma das linhas (centavos). TEM QUE BATER com `custo_mercadorias` "
            "do resumo — se divergir é bug, e um detalhe que não fecha com o "
            "total piora a desconfiança em vez de resolver"
        ),
    )
    linhas: list[CustoDetalheLinha] = Field(default_factory=list)
