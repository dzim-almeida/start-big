# ---------------------------------------------------------------------------
# ARQUIVO: schemas/compras/recebimentos.py
# DESCRICAO: Schemas de compras - escrita do recebimento.
# ---------------------------------------------------------------------------

from typing import Optional
from pydantic import BaseModel, Field, model_validator
from app.schemas.compras.pedidos import MAX_ITENS_POR_PEDIDO


# ---------------------------------------------------------------------------
# Fase 3 — recebimento
# ---------------------------------------------------------------------------


class RecebimentoItemEscrita(BaseModel):
    pedido_item_id: int = Field(..., ge=1)
    quantidade: int = Field(..., ge=0, le=1_000_000, description="Na unidade de compra; 0 = não chegou")
    # Custo REAL, por unidade de compra. Nulo = o do pedido. Ignorado para quem
    # não pode ver custo (o almoxarife confere quantidade, não preço — D14).
    custo_unitario: Optional[int] = Field(None, ge=0, le=100_000_000)


class RecebimentoEscrita(BaseModel):
    itens: list[RecebimentoItemEscrita] = Field(..., min_length=1, max_length=MAX_ITENS_POR_PEDIDO)
    numero_nota: Optional[str] = Field(None, max_length=20)
    observacao: Optional[str] = Field(None, max_length=2000)
    lancar_contas_pagar: bool = Field(True, description="Gera as contas a pagar proporcionais (D8), com o Financeiro")
    encerrar_saldo: bool = Field(False, description="O que não chegou agora não vem mais (D5)")

    @model_validator(mode="after")
    def _sem_item_repetido(self) -> "RecebimentoEscrita":
        ids = [i.pedido_item_id for i in self.itens]
        if len(ids) != len(set(ids)):
            raise ValueError("O mesmo item aparece duas vezes no recebimento.")
        return self
