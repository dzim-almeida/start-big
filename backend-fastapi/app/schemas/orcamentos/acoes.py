# ---------------------------------------------------------------------------
# ARQUIVO: schemas/orcamentos/acoes.py
# DESCRICAO: Schemas do orcamento - converter em venda.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field


class ConverterOrcamentoPayload(BaseModel):
    cliente_id: int = Field(..., description="ID do cliente para a venda")
