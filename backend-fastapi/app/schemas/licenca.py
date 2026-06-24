# ---------------------------------------------------------------------------
# ARQUIVO: app/schemas/licenca.py
# DESCRIÇÃO: Schemas Pydantic para dados de licenciamento.
# ---------------------------------------------------------------------------

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class LicencaEnderecoPayload(BaseModel):
    """Sub-schema para o endereço no payload de auto-cadastro."""
    cep: str = Field(..., max_length=10)
    logradouro: str = Field(..., max_length=255)
    numero: str = Field(..., max_length=20)
    bairro: str = Field(..., max_length=100)
    cidade: str = Field(..., max_length=100)
    estado: str = Field(..., max_length=2)


class AutoCadastroPayload(BaseModel):
    """Payload enviado à API StartBig para auto-cadastro de licença."""
    documento: str = Field(..., description="CPF ou CNPJ")
    nomeOuRazao: str = Field(..., description="Nome ou Razão Social")
    email: str = Field(..., description="Email do responsável")
    hwid: str = Field(..., description="Hardware ID da máquina")
    endereco: Optional[LicencaEnderecoPayload] = Field(
        None, description="Endereço (opcional)"
    )


class AutoCadastroResponse(BaseModel):
    """Resposta da API StartBig após auto-cadastro."""
    msg: str
    clienteId: str
    licencaId: str
    chaveAtivacao: str
    sessionKey: str
    limite: int
    dataVencimento: datetime
    token: str
    ultimaSincronizacao: datetime
    gracePeriodDias: int
    proximaValidacaoEm: datetime


class LicencaRead(BaseModel):
    """Schema de leitura da licença armazenada localmente."""
    id: int
    cliente_id: str
    hwid: str
    licenca_id: str
    limite: int
    data_vencimento: datetime
    proxima_validacao: datetime
    grace_period: int
