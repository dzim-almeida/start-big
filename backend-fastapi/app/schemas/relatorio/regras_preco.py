# ---------------------------------------------------------------------------
# ARQUIVO: schemas/relatorio/regras_preco.py
# DESCRICAO: Schemas de relatorio - vendas por regra de preco.
# ---------------------------------------------------------------------------

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


# ===========================================================================
# VENDAS POR REGRA DE PREÇO (plano de embalagens, fase 6)
# ===========================================================================

class RegraPrecoResumo(BaseModel):
    """Total de uma regra (R1, R2 ou R3) no período."""
    regra: str = Field(..., description="R1, R2 ou R3")
    qtd_vendas: int = Field(..., description="Vendas finalizadas com esta regra em alguma linha")
    unidades: float = Field(..., description="Unidades vendidas com a regra (na unidade base; fracionado em KG)")
    faturamento: int = Field(..., description="O que entrou nessas linhas (centavos)")
    abatimento: int = Field(..., description="O que a regra deixou de cobrar (centavos)")


class RegraPrecoProdutoItem(BaseModel):
    """Um produto vendido com uma regra no período."""
    regra: str
    produto_id: int
    nome: str
    sku: Optional[str] = None
    qtd_vendas: int
    unidades: float
    faturamento: int = Field(..., description="Centavos")
    abatimento: int = Field(..., description="Centavos")


class RelatorioRegrasPreco(BaseModel):
    """Vendas com regra de preço por quantidade: quanto venderam e quanto abateram."""
    inicio: date
    fim: date
    qtd_vendas: int = Field(0, description="Vendas com ao menos uma linha com regra (sem contar duas vezes)")
    faturamento: int = Field(0, description="Σ faturamento das linhas com regra (centavos)")
    abatimento: int = Field(0, description="Σ do que as regras deixaram de cobrar (centavos)")
    por_regra: list[RegraPrecoResumo] = Field(default_factory=list)
    por_produto: list[RegraPrecoProdutoItem] = Field(default_factory=list)
