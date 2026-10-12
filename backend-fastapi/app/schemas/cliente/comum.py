# ---------------------------------------------------------------------------
# ARQUIVO: schemas/cliente/comum.py
# DESCRICAO: Clientes - campos comuns a PF e PJ (ClienteBase).
# ---------------------------------------------------------------------------

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


# ===========================================================================
# SCHEMA BASE (CAMPOS COMUNS)
# ===========================================================================

class ClienteBase(BaseModel):
    """Atributos compartilhados entre PF e PJ."""
    
    email: Optional[str] = Field(
        None,
        max_length=255,
        description="Endereço de e-mail principal para contato."
    )
    telefone: Optional[str] = Field(
        None,
        max_length=255,
        description="Telefone principal."
    )
    celular: Optional[str] = Field(
        None,
        max_length=255,
        description="Celular principal."
    )
    observacoes: Optional[str] = Field(
        None,
        max_length=500,
        description="Notas internas ou observações sobre o cliente."
    )
    model_config = ConfigDict(from_attributes=True)
