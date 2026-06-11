from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, computed_field


class ConfiguracaoSegurancaRead(BaseModel):
    id: int
    empresa_id: int

    pin_gerente: Optional[str] = Field(None, exclude=True)

    @computed_field
    @property
    def tem_pin_configurado(self) -> bool:
        return bool(self.pin_gerente)

    requer_pin_acessar_config_sensivel: bool

    requer_pin_cancelar_venda: bool
    requer_pin_reabrir_venda: bool
    requer_pin_desconto_venda: bool
    requer_pin_alterar_preco_venda: bool

    requer_pin_cancelar_os: bool
    requer_pin_reabrir_os: bool
    requer_pin_desconto_os: bool

    data_atualizacao: datetime

    model_config = {"from_attributes": True}


class VerificarPinPayload(BaseModel):
    pin: str = Field(..., description="PIN do gerente a verificar")


class ConfiguracaoSegurancaUpdate(BaseModel):
    pin_gerente: Optional[str] = None

    requer_pin_acessar_config_sensivel: Optional[bool] = None

    requer_pin_cancelar_venda: Optional[bool] = None
    requer_pin_reabrir_venda: Optional[bool] = None
    requer_pin_desconto_venda: Optional[bool] = None
    requer_pin_alterar_preco_venda: Optional[bool] = None

    requer_pin_cancelar_os: Optional[bool] = None
    requer_pin_reabrir_os: Optional[bool] = None
    requer_pin_desconto_os: Optional[bool] = None
