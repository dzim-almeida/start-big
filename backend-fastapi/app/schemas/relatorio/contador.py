# ---------------------------------------------------------------------------
# ARQUIVO: schemas/relatorio/contador.py
# DESCRICAO: Schemas de relatorio - receita para o contador (PGDAS-D).
# ---------------------------------------------------------------------------

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


# ===========================================================================
# RECEITA PARA O CONTADOR (segregação do PGDAS-D)
# ===========================================================================

class ReceitaGrupoItem(BaseModel):
    """Receita de mercadoria de um grupo do PGDAS-D."""
    icms_st: bool = Field(..., description="ICMS já pago por substituição tributária (CSOSN 500 / CST 60)")
    monofasico: bool = Field(..., description="PIS/COFINS monofásico (CST 04)")
    valor: int = Field(..., description="Centavos")


class ProdutoSemClassificacaoItem(BaseModel):
    """Produto vendido no período cujo cadastro não diz se o ICMS é ST."""
    produto_id: Optional[int] = None
    nome: str
    valor: int = Field(..., description="Receita do período (centavos)")
    motivo: str


class RelatorioContador(BaseModel):
    """Receita do período separada como o contador declara no PGDAS-D."""
    inicio: date
    fim: date
    crt: Optional[int] = Field(None, description="Regime da empresa: 1 Simples, 2 excesso de sublimite, 3 normal, 4 MEI")
    receita_total: int = Field(0, description="Bate com o faturamento bruto (vendas + OS)")
    mercadoria: list[ReceitaGrupoItem] = Field(default_factory=list)
    mercadoria_sem_classificacao: int = 0
    servicos: int = Field(0, description="Itens de serviço das OS")
    frete_e_juros: int = Field(0, description="Frete/taxa de entrega e juros de cartão cobrados do cliente")
    faturamento_vendas: int = 0
    faturamento_os: int = 0
    produtos_sem_classificacao: list[ProdutoSemClassificacaoItem] = Field(default_factory=list)
