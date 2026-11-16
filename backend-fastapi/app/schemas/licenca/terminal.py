# ---------------------------------------------------------------------------
# ARQUIVO: schemas/licenca/terminal.py
# DESCRICAO: Schemas da licenca - conectar, heartbeat e desconectar terminal.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field


# ===========================================================================
# Validação de Sessão (Etapa 2)
# ===========================================================================

class ConectarPayload(BaseModel):
    """Payload enviado à API StartBig para validação de sessão."""
    chave: str = Field(..., description="Chave de ativação (descriptografada)")
    hwid: str = Field(..., description="Hardware ID da máquina")


class HeartbeatPayload(BaseModel):
    """Payload enviado à API StartBig para heartbeat de licença."""
    licencaId: str = Field(..., description="ID da licença")
    hwid: str = Field(..., description="Hardware ID da máquina")


# ===========================================================================
# Desconexão de Sessão (Etapa 5)
# ===========================================================================

class DesconectarPayload(BaseModel):
    """Payload enviado à API StartBig para desconectar a sessão da licença."""
    chave: str = Field(..., description="Chave de ativação (descriptografada)")
    hwid: str = Field(..., description="Hardware ID da máquina")
