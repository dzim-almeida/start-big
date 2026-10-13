# ---------------------------------------------------------------------------
# ARQUIVO: schemas/ordem_servico/pagamento.py
# DESCRICAO: Schemas da OS - pagamentos (criados ao finalizar).
# ---------------------------------------------------------------------------

from datetime import date
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from app.core.enum import (
    JurosResponsavel,
)
from app.schemas.forma_pagamento import FormaPagamentoRead


# ===========================================================================
# PAGAMENTOS DA OS
# ===========================================================================

class OSPagamentoCreate(BaseModel):
    """
    Payload para registrar um pagamento.
    Pagamentos são criados exclusivamente no ato de finalização da OS.
    Uma OS pode ter múltiplos pagamentos (ex: parte em Dinheiro + parte em PIX).
    A soma dos valores deve ser exatamente igual ao valor_total da OS.
    """
    forma_pagamento_id: int = Field(..., description="ID da forma de pagamento do catálogo")
    valor: int = Field(..., gt=0, description="Valor pago pelo cliente nesta forma de pagamento (centavos)")
    juros_valor: int = Field(0, ge=0, description="Juros calculados neste pagamento (centavos)")
    juros_responsavel: JurosResponsavel = Field(
        JurosResponsavel.CLIENTE,
        description="CLIENTE: juros embutido em `valor`. LOJA: juros absorvido, fora de `valor`.",
    )
    parcelas: int = Field(1, ge=1, description="Número de parcelas (mínimo 1)")
    bandeira_cartao: Optional[str] = Field(None, max_length=50, description="Bandeira do cartão (VISA, MASTERCARD, etc.)")
    vencimento: Optional[date] = Field(None, description="Data de vencimento do pagamento (ex: boletos)")
    detalhes: Optional[dict] = Field(None, description="Dados adicionais do pagamento em formato JSON")

    model_config = ConfigDict(from_attributes=True)


class OSPagamentoRead(BaseModel):
    """Resposta de um pagamento de OS. Inclui dados aninhados da forma de pagamento."""
    id: int = Field(..., description="ID único do pagamento")
    ordem_servico_id: int = Field(..., description="ID da OS associada")
    forma_pagamento: FormaPagamentoRead = Field(..., description="Forma de pagamento utilizada")
    valor: int = Field(..., description="Valor pago pelo cliente (centavos)")
    juros_valor: int = Field(0, description="Juros calculados neste pagamento (centavos)")
    juros_responsavel: JurosResponsavel = Field(
        JurosResponsavel.CLIENTE, description="Quem arca com o juros deste pagamento"
    )
    parcelas: int = Field(..., description="Número de parcelas")
    bandeira_cartao: Optional[str] = Field(None, description="Bandeira do cartão")
    vencimento: Optional[date] = Field(None, description="Data de vencimento do pagamento")
    detalhes: Optional[dict] = Field(None, description="Dados adicionais")

    model_config = ConfigDict(from_attributes=True)
