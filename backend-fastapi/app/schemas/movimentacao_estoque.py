# ---------------------------------------------------------------------------
# ARQUIVO: schemas/movimentacao_estoque.py
# DESCRIÇÃO: Schemas Pydantic para movimentações de estoque.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

from app.core.enum import MovimentacaoTipo


class MovimentacaoCreate(BaseModel):
    """Dados de entrada para registrar uma movimentação de estoque."""
    tipo: MovimentacaoTipo = Field(..., description="Tipo: ENTRADA, SAIDA ou AJUSTE")
    quantidade: int = Field(..., ge=1, description="Quantidade movimentada (mínimo 1)")
    observacao: Optional[str] = Field(None, max_length=500, description="Motivo ou observação")

    model_config = ConfigDict(from_attributes=True)


class MovimentacaoRead(BaseModel):
    """Dados de saída de uma movimentação de estoque."""
    id: int
    produto_id: int
    produto_nome: str
    usuario_id: Optional[int]
    usuario_nome: str
    tipo: MovimentacaoTipo
    quantidade: int
    quantidade_anterior: int
    quantidade_posterior: int
    observacao: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
