from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ConfiguracaoOSBase(BaseModel):
    prazo_entrega_padrao: int = Field(7, ge=1, description="Prazo padrão de entrega em dias")
    garantia_padrao: str = Field("90 dias", max_length=20, description="Prazo de garantia padrão")
    prazo_abandono_dias: int = Field(90, ge=1, description="Dias para considerar equipamento abandonado")
    taxa_diagnostico_padrao: int = Field(0, ge=0, description="Taxa de diagnóstico padrão em centavos (0 = desativada)")


class ConfiguracaoOSRead(ConfiguracaoOSBase):
    id: int
    empresa_id: int
    data_atualizacao: datetime
    model_config = ConfigDict(from_attributes=True)


class ConfiguracaoOSUpdate(BaseModel):
    prazo_entrega_padrao: Optional[int] = Field(None, ge=1)
    garantia_padrao: Optional[str] = Field(None, max_length=20)
    prazo_abandono_dias: Optional[int] = Field(None, ge=1)
    taxa_diagnostico_padrao: Optional[int] = Field(None, ge=0)
    model_config = ConfigDict(from_attributes=True)
