from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ConfiguracaoVendasRead(BaseModel):
    id: int
    empresa_id: int

    permitir_desconto: bool
    desconto_maximo_percent: int
    exigir_cliente_identificado: bool
    acao_ao_finalizar: str

    data_atualizacao: datetime

    model_config = {"from_attributes": True}


class ConfiguracaoVendasUpdate(BaseModel):
    permitir_desconto: Optional[bool] = None
    desconto_maximo_percent: Optional[int] = Field(None, ge=0, le=100)
    exigir_cliente_identificado: Optional[bool] = None
    acao_ao_finalizar: Optional[str] = None
