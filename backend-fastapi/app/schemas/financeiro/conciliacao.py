# ---------------------------------------------------------------------------
# ARQUIVO: schemas/financeiro/conciliacao.py
# DESCRICAO: Financeiro - schemas da conciliacao.
# ---------------------------------------------------------------------------

from datetime import date
from typing import List
from pydantic import BaseModel, Field


# ===========================================================================
# CONCILIAÇÃO (Onda 4)
# ===========================================================================

class ConciliacaoItem(BaseModel):
    """Uma cobrança que compõe o repasse do dia."""

    conta_id: int
    descricao: str
    valor: int = Field(..., description="Previsto LÍQUIDO (centavos)")
    cliente_nome: str | None = None
    forma_origem: str | None = Field(
        None, description="Forma que originou (Cartão de Crédito, PIX...); None se lançada à mão"
    )


class ConciliacaoDia(BaseModel):
    """Tudo que a loja espera receber num dia — o candidato a um depósito.

    O agrupamento é por DIA de vencimento porque é assim que o dinheiro chega:
    a operadora não deposita venda a venda, deposita o lote do dia. Conferir
    item a item contra o extrato é o trabalho que esta tela existe para evitar.
    """

    data: date
    quantidade: int
    total_previsto: int
    itens: List[ConciliacaoItem] = Field(default_factory=list)


class Conciliacao(BaseModel):
    inicio: date
    fim: date
    total_previsto: int
    dias: List[ConciliacaoDia] = Field(default_factory=list)


class ConciliacaoBaixaLote(BaseModel):
    """O depósito que caiu: um valor só, cobrindo o lote inteiro do dia."""

    data: date = Field(..., description="Dia do vencimento cujo lote está sendo conferido")
    valor_recebido: int = Field(
        ..., gt=0, description="O que caiu de fato na conta, em centavos"
    )
    conta_bancaria_id: int | None = Field(None, description="Onde o depósito caiu")
    forma_pagamento_id: int | None = None


class ConciliacaoResultado(BaseModel):
    """O que a baixa em lote fez, para a tela poder mostrar sem recarregar."""

    data: date
    quantidade: int
    total_previsto: int
    total_recebido: int
    diferenca: int = Field(
        ...,
        description=(
            "total_recebido - total_previsto (centavos). Negativo é o comum: é a "
            "taxa que a operadora reteve"
        ),
    )
