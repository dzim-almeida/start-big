# ---------------------------------------------------------------------------
# ARQUIVO: schemas/relatorio/estoque.py
# DESCRICAO: Schemas de relatorio - estoque e curva ABC.
# ---------------------------------------------------------------------------

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


# ===========================================================================
# RELATORIO DE ESTOQUE / CURVA ABC (Fase 4a)
# ===========================================================================

class EstoqueAbcItem(BaseModel):
    """Produto na Curva ABC (classificado por faturamento no período)."""
    produto_id: int
    nome: str
    sku: Optional[str] = Field(None, description="Codigo do produto (SKU)")
    categoria: Optional[str] = None
    faturamento: int = Field(..., description="Receita líquida gerada no período (centavos)")
    # float: venda fracionada (3,5 kg) — `int` derrubava a curva ABC.
    quantidade: float = Field(..., description="Unidades vendidas no período")
    participacao_pct: float = Field(..., description="% do faturamento total do período")
    acumulado_pct: float = Field(..., description="% acumulado (base da classificação ABC)")
    classe: str = Field(..., description="Classe ABC: 'A' | 'B' | 'C'")


class EstoqueReposicaoItem(BaseModel):
    """Produto abaixo do mínimo — alerta de reposição."""
    produto_id: int
    nome: str
    sku: Optional[str] = None
    # float: o estoque é fracionado desde f97d3c1 (kg quebrado). Como int, um
    # produto com 1,5 kg derrubava esta resposta com erro 500.
    quantidade: float = Field(..., description="Quantidade atual em estoque")
    quantidade_minima: Optional[float] = Field(None, description="Mínimo configurado")
    quantidade_ideal: Optional[float] = Field(None, description="Quantidade ideal configurada")


class EstoqueParadoItem(BaseModel):
    """Produto ativo com estoque e SEM vendas no período (encalhado)."""
    produto_id: int
    nome: str
    sku: Optional[str] = None
    # float: o estoque é fracionado desde f97d3c1 (kg quebrado). Como int, um
    # produto com 1,5 kg derrubava esta resposta com erro 500.
    quantidade: float = Field(..., description="Quantidade parada em estoque")
    valor_custo: int = Field(..., description="Capital imobilizado a custo (quantidade × custo, centavos)")


class RelatorioEstoque(BaseModel):
    """Relatorio de estoque: KPIs + Curva ABC + reposição + parados."""
    inicio: date
    fim: date
    # KPIs de valor imobilizado (posição atual — não depende do período)
    valor_custo_total: int = Field(..., description="Σ quantidade × custo de todos os produtos ativos (centavos)")
    valor_venda_total: int = Field(..., description="Σ quantidade × preço de varejo (centavos)")
    skus_ativos: int = Field(..., description="Produtos ativos cadastrados")
    itens_abaixo_minimo: int = Field(..., description="Quantos produtos estão abaixo do mínimo")
    itens_parados: int = Field(..., description="Quantos produtos ativos não venderam no período")
    curva_abc: list[EstoqueAbcItem] = Field(default_factory=list)
    abaixo_minimo: list[EstoqueReposicaoItem] = Field(default_factory=list)
    parados: list[EstoqueParadoItem] = Field(default_factory=list)
