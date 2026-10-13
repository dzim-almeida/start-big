# ---------------------------------------------------------------------------
# ARQUIVO: schemas/vendas/resumo.py
# DESCRICAO: Schemas da venda - resumos financeiro e por status.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field, ConfigDict
from app.schemas.vendas.itens import ProdutoVendaRead


class VendaFinanceSummary(BaseModel):
    subtotal: int = Field(0, ge=0, description="Subtotal atualizado da venda após alteração dos produtos")
    descontos: int = Field(0, ge=0, description="Desconto atualizado da venda após alteração dos produtos")
    descontos_regra: int = Field(0, ge=0, description="Descontos das regras de preço (R1/R3) após a alteração")
    entrega: int = Field(0, ge=0, description="Valor da entrega atualizado da venda após alteração dos produtos")
    total: int = Field(0, ge=0, description="Total atualizado da venda após alteração dos produtos")


class VendaStatusSummary(BaseModel):
    vendas_ativas: int = Field(0, ge=0, description="Quantidade de vendas ativas")
    vendas_na_fila: int = Field(0, ge=0, description="Vendas ativas já entregues ao caixa")
    vendas_finalizadas: int = Field(0, ge=0, description="Quantidade de vendas finalizadas")
    vendas_canceladas: int = Field(0, ge=0, description="Quantidade de vendas canceladas")
    ticket_medio: int = Field(0, ge=0, description="Valor médio dos tickets das vendas finalizadas")


class ProdutosAlterSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    produto_adicionado: ProdutoVendaRead
    financeiro_atualizado: VendaFinanceSummary
    # As OUTRAS linhas que a regra de preço mudou (§6.1): a tela troca essas
    # também, senão mostraria o preço velho até recarregar. Vazio sem regra.
    itens_alterados: list[ProdutoVendaRead] = Field(default_factory=list)
