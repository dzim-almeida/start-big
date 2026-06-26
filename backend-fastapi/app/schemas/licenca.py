# ---------------------------------------------------------------------------
# ARQUIVO: app/schemas/licenca.py
# DESCRIÇÃO: Schemas Pydantic para dados de licenciamento.
# ---------------------------------------------------------------------------

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ===========================================================================
# Auto-Cadastro (Etapa 1)
# ===========================================================================

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
    hwid: str = Field(..., description="Hardware ID da máquina (obtido internamente)")
    endereco: Optional[LicencaEnderecoPayload] = Field(
        None, description="Endereço (opcional)"
    )


class AutoCadastroResponse(BaseModel):
    """Resposta da API StartBig após auto-cadastro e conexão."""
    msg: str = Field(..., description="Mensagem de sucesso ou erro")
    clienteId: Optional[str] = Field(None, description="ID do cliente (se sucesso)")
    licencaId: str = Field(..., description="ID da licença gerada")
    chaveAtivacao: Optional[str] = Field(None, description="Chave de ativação (se sucesso)")
    sessionKey: str = Field(..., description="Chave de sessão para validação futura")
    limite: int = Field(..., description="Limite de uso da licença")
    dataVencimento: datetime = Field(..., description="Data de vencimento da licença")
    token: str = Field(..., description="Token de autenticação para futuras requisições")
    ultimaSincronizacao: datetime = Field(..., description="Data da última sincronização com a API")
    gracePeriodDias: int = Field(..., description="Dias de período de carência após vencimento")
    proximaValidacaoEm: datetime = Field(..., description="Data da próxima validação obrigatória da licença")


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


# ===========================================================================
# Validação de Sessão (Etapa 2)
# ===========================================================================

class ConectarPayload(BaseModel):
    """Payload enviado à API StartBig para validação de sessão."""
    chave: str = Field(..., description="Chave de ativação (descriptografada)")
    hwid: str = Field(..., description="Hardware ID da máquina")


class LicencaStatusResponse(BaseModel):
    """Resposta do GET /licenca/status para o frontend."""
    status: str = Field(..., description="online_valid | offline_valid")
    dias_restantes: Optional[int] = Field(
        None, description="Dias restantes de validade offline"
    )


class LicencaErroResponse(BaseModel):
    """Corpo do erro HTTP 403 para problemas de licença."""
    codigo: str = Field(
        ...,
        description=(
            "CLONAGEM_DETECTADA | REQUISITA_CONEXAO_INTERNET | "
            "LICENCA_EXPIRADA | LICENCA_NAO_ENCONTRADA"
        ),
    )
    mensagem: str = Field(..., description="Mensagem descritiva do erro")
