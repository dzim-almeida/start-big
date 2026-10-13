# ---------------------------------------------------------------------------
# ARQUIVO: schemas/vendas/acoes.py
# DESCRICAO: Schemas da venda - payloads de finalizar, cancelar e reabrir.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.vendas.pagamento import PagamentoVendaCreate


class FinalizarVendaPayload(BaseModel):
    pagamentos: list[PagamentoVendaCreate] = Field(..., min_length=1, description="Lista de pagamentos para finalizar a venda")
    acrescimo: Optional[int] = Field(0, ge=0, description="Acréscimo total de juros/cartão a ser somado ao total da venda (centavos)")


class CancelarVendaPayload(BaseModel):
    motivo: str = Field(..., min_length=10, max_length=500, description="Motivo do cancelamento da venda (mínimo 10 caracteres)")
    codigo_gerente: Optional[str] = Field(None, description="PIN do gerente para aprovar cancelamento")


class ReabrirVendaPayload(BaseModel):
    codigo_gerente: Optional[str] = Field(None, description="PIN do gerente para aprovar reabertura")
