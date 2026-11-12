# ---------------------------------------------------------------------------
# ARQUIVO: app/schemas/lava_rapido/lavador.py
# DESCRICAO: Lavadores (executores) da OS -- Spec 10A do lava-rapido.
# ---------------------------------------------------------------------------

from typing import List

from pydantic import BaseModel, Field


class LavadorRead(BaseModel):
    funcionario_id: int
    nome: str


class LavadoresUpdate(BaseModel):
    """A lista INTEIRA. Vazia = sem lavador (comissao para o responsavel)."""
    funcionario_ids: List[int] = Field(default_factory=list)
