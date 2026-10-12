# ---------------------------------------------------------------------------
# ARQUIVO: schemas/cliente/historico.py
# DESCRICAO: Clientes - historico de equipamentos.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional


# ===========================================================================
# EQUIPAMENTO HISTÓRICO (DTO leve para listagem)
# ===========================================================================

class EquipamentoHistoricoRead(BaseModel):
    """Equipamento resumido para seleção rápida no formulário de OS."""
    # String livre (agnóstico de segmento): TI manda "COMPUTADOR"/"CELULAR"...,
    # oficina manda "Veículo". Antes era o enum de TI e a oficina quebrava a leitura.
    equipamento: str = Field(
        ...,
        validation_alias="tipo_equipamento",
        description="Tipo do equipamento/objeto (livre por segmento)"
    )
    marca: str
    modelo: str
    numero_serie: str
    # Detalhes reaproveitados ao reutilizar o objeto numa nova OS (cor + campos
    # dinâmicos do segmento, ex.: oficina → chassi, ano).
    cor: Optional[str] = None
    dados_adicionais: Optional[dict] = None

    @field_validator("equipamento", mode="before")
    @classmethod
    def _normalizar_equipamento(cls, v):
        # tipo_equipamento vem como shim/enum/str — normaliza para string.
        return getattr(v, "value", v)

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
