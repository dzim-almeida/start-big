# ---------------------------------------------------------------------------
# ARQUIVO: schemas/vendas/pagamento.py
# DESCRICAO: Schemas da venda - pagamentos.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field, model_validator
from datetime import datetime, date
from typing import Optional
from app.core.enum import JurosResponsavel


        

class PagamentoVendaCreate(BaseModel):
    forma_pagamento_id: int = Field(..., description="ID da forma de pagamento, obrigatório")
    parcelado: bool = Field(False, description="Indica se o pagamento é parcelado")
    qtd_parcelas: Optional[int] = Field(1, gt=0, description="Quantidade de parcelas")
    valor: int = Field(..., ge=0, description="Valor pago pelo cliente neste método (centavos), obrigatório")
    juros_valor: int = Field(0, ge=0, description="Juros calculados neste pagamento (centavos)")
    juros_responsavel: JurosResponsavel = Field(
        JurosResponsavel.CLIENTE,
        description="CLIENTE: juros embutido em `valor`. LOJA: juros absorvido, fora de `valor`.",
    )
    bandeira_cartao: Optional[str] = Field(None, max_length=50, description="Bandeira do cartão (VISA, MASTERCARD, etc.)")
    vencimento: Optional[date] = Field(None, description="Data de vencimento do pagamento (ex: boletos)")
    detalhes: Optional[dict] = Field(None, description="Dados adicionais do pagamento em formato JSON (ex: banco/NSU)")

    @model_validator(mode='after')
    def check_pagamento_fields(self) -> 'PagamentoVendaCreate':
        if self.parcelado:
            if self.qtd_parcelas is None:
                raise ValueError("O campo 'qtd_parcelas' é obrigatório quando o pagamento é parcelado.")
        if not self.parcelado and self.qtd_parcelas:
            raise ValueError("O campo 'qtd_parcelas' deve ser nulo quando o pagamento não é parcelado.")
        return self


class PagamentoVendaRead(PagamentoVendaCreate):
    id: int = Field(..., description="ID do pagamento na venda")
    data_pagamento: datetime = Field(..., description="Data do pagamento no formato ISO 8601")
