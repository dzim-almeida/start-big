# ---------------------------------------------------------------------------
# ARQUIVO: schemas/ordem_servico/foto.py
# DESCRICAO: Schemas da OS - fotos de diagnostico.
# ---------------------------------------------------------------------------

from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ===========================================================================
# FOTOS DA OS
# ===========================================================================

class OSFotoRead(BaseModel):
    """Resposta de uma foto de diagnóstico de OS."""
    id: int = Field(..., description="ID único da foto")
    ordem_servico_id: int = Field(..., description="ID da OS associada")
    nome_arquivo: str = Field(..., description="Nome original do arquivo enviado")
    url: str = Field(..., description="Caminho/URL do arquivo no servidor")
    data_criacao: datetime = Field(..., description="Data de upload")

    model_config = ConfigDict(from_attributes=True)
