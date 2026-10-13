# ---------------------------------------------------------------------------
# ARQUIVO: schemas/orcamentos/resumo.py
# DESCRICAO: Schemas do orcamento - resumos financeiro e por status.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field, ConfigDict
from app.schemas.orcamentos.itens import OrcamentoProdutoRead


class OrcamentoFinanceSummary(BaseModel):
    subtotal: int = Field(0, ge=0, description="Subtotal atualizado do orcamento")
    descontos: int = Field(0, ge=0, description="Descontos atualizados do orcamento")
    entrega: int = Field(0, ge=0, description="Valor da entrega atualizado")
    total: int = Field(0, ge=0, description="Total atualizado do orcamento")


class OrcamentoProdutosAlterSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    produto_adicionado: OrcamentoProdutoRead
    financeiro_atualizado: OrcamentoFinanceSummary


class OrcamentoStatusSummary(BaseModel):
    orcamentos_ativos: int = Field(0, ge=0, description="Quantidade de orcamentos ativos")
    orcamentos_convertidos: int = Field(0, ge=0, description="Quantidade de orcamentos convertidos")
