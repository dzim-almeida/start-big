# ---------------------------------------------------------------------------
# ARQUIVO: schemas/relatorio/faturamento.py
# DESCRICAO: Schemas de relatorio - faturamento.
# ---------------------------------------------------------------------------

from datetime import date
from pydantic import BaseModel, Field


class FaturamentoDiaItem(BaseModel):
    """Faturamento consolidado de um dia (vendas + OS)."""
    dia: date
    total_vendas: int = Field(..., description="Faturamento de vendas no dia (centavos)")
    total_os: int = Field(..., description="Faturamento de OS no dia (centavos)")
    total_geral: int = Field(..., description="Soma vendas + OS no dia (centavos)")


class FormaPagamentoResumo(BaseModel):
    """Total recebido por forma de pagamento no periodo."""
    nome: str
    valor_total: int = Field(..., description="Total recebido nesta forma (centavos)")


class RelatorioFaturamento(BaseModel):
    """Resposta do relatorio de faturamento por periodo."""
    inicio: date
    fim: date
    faturamento_total: int = Field(..., description="Bruto: vendas + OS finalizadas no periodo (centavos)")
    faturamento_vendas: int = Field(..., description="Somente vendas (centavos)")
    faturamento_os: int = Field(..., description="Somente OS (centavos)")
    juros_repassado: int = Field(
        0,
        description="Juros cobrado do cliente. Já está dentro do faturamento_total, "
                    "mas fica com a operadora — por isso sai do líquido (centavos)",
    )
    juros_absorvido: int = Field(
        0,
        description="Juros que a loja bancou. NÃO está no faturamento_total (o cliente "
                    "não foi cobrado), e mesmo assim reduz o líquido (centavos)",
    )
    faturamento_liquido: int = Field(
        0,
        description="faturamento_total − juros_repassado − juros_absorvido. É o que "
                    "efetivamente sobra para a loja (centavos)",
    )
    cmv: int = Field(
        0,
        description="Custo da mercadoria vendida: Σ do custo congelado das pecas que "
                    "sairam por venda e OS no periodo, menos os estornos (centavos)",
    )
    lucro_bruto: int = Field(
        0,
        description="faturamento_liquido − cmv. E o que sobra depois do custo das pecas "
                    "e do juros de cartao. Nao desconta despesa fixa (centavos)",
    )
    margem_percentual: float = Field(
        0.0,
        description="lucro_bruto ÷ faturamento_total × 100. Zero quando nao houve faturamento",
    )
    saidas_sem_custo: int = Field(
        0,
        description="Movimentacoes do periodo sem custo apurado (anteriores ao registro de "
                    "custo). Enquanto for > 0 o lucro esta SUBESTIMADO e a tela avisa",
    )
    ticket_medio: int = Field(..., description="Faturamento / nº de transacoes finalizadas (centavos)")
    qtd_vendas: int = Field(..., description="Quantidade de vendas finalizadas")
    qtd_os: int = Field(..., description="Quantidade de OS finalizadas")
    por_dia: list[FaturamentoDiaItem] = Field(default_factory=list)
    formas_pagamento: list[FormaPagamentoResumo] = Field(default_factory=list)
