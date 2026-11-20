# ---------------------------------------------------------------------------
# ARQUIVO: schemas/licenca/cadastro.py
# DESCRICAO: Schemas da licenca - auto-cadastro, chave publica e leitura.
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
    senha: str = Field(..., description="Senha para autenticação futura")
    hwid: str = Field(..., description="Hardware ID da máquina (obtido internamente)")
    endereco: Optional[LicencaEnderecoPayload] = Field(
        None, description="Endereço (opcional)"
    )
    # O app novo avisa que sabe tratar a confirmação de e-mail: a API responde
    # 202 sem criar licença (LIC-03 §6.5, D-34, ADR-004).
    fluxoConfirmacao: Optional[bool] = Field(
        None, description="True = o app entende o cadastro com confirmação de e-mail"
    )


class AutoCadastroResponse(BaseModel):
    """Resposta da API StartBig após auto-cadastro e conexão."""
    msg: str = Field(..., description="Mensagem de sucesso ou erro")
    clienteId: Optional[str] = Field(None, description="ID do cliente (se sucesso)")
    licencaId: str = Field(..., description="ID da licença gerada")
    chaveAtivacao: Optional[str] = Field(None, description="Chave de ativação (se sucesso)")
    sessionKey: Optional[str] = Field(None, description="Chave de sessão (deprecada, mantida por retrocompatibilidade)")
    limite: int = Field(..., description="Limite de uso da licença")
    dataVencimento: datetime = Field(..., description="Data de vencimento da licença")
    token: str = Field(..., description="Token de autenticação para futuras requisições")
    ultimaSincronizacao: datetime = Field(..., description="Data da última sincronização com a API")
    gracePeriodDias: int = Field(
        ...,
        description=(
            "Dias de validade OFFLINE. Apesar do nome, NAO e tolerancia de "
            "inadimplencia -- essa vem em `emCarencia`/`dataLimiteCarencia`."
        ),
    )
    proximaValidacaoEm: datetime = Field(..., description="Data da próxima validação obrigatória da licença")
    # LIC-02 (F26): a API calcula os dias e manda FORA do token, para o numero
    # nao ficar congelado por 7 dias. Opcional: sem ele, o app calcula e marca
    # como estimativa.
    diasRestantes: Optional[int] = Field(
        None, description="Dias até o vencimento, calculados pela API"
    )

    # --- Carencia de pagamento (opcionais) ---
    # Opcionais porque a API so passou a mandar depois; servidor que nao mandar
    # deixa a licenca sem carencia, que e o comportamento de sempre.
    emCarencia: Optional[bool] = Field(
        None, description="True enquanto o gateway ainda re-tenta a cobranca do cartao"
    )
    diasRestantesCarencia: Optional[int] = Field(
        None, description="Dias que ainda faltam da carencia"
    )
    dataLimiteCarencia: Optional[datetime] = Field(
        None, description="Ate quando a carencia vale"
    )


class ChavePublicaResponse(BaseModel):
    """Resposta do GET /licenca/chave-publica da API StartBig."""
    publicKey: str = Field(..., description="Chave pública RSA em formato PEM")


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
