# ---------------------------------------------------------------------------
# ARQUIVO: schemas/licenca/status.py
# DESCRICAO: Schemas da licenca - status, erro e validacao.
# ---------------------------------------------------------------------------

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class LicencaStatusResponse(BaseModel):
    """Resposta do GET /licenca/status para o frontend."""
    status: str = Field(..., description="online_valid | offline_valid")
    dias_restantes: Optional[int] = Field(
        None, description="Dias restantes até o vencimento (online) ou de validade offline"
    )
    trial: Optional[bool] = Field(
        None,
        description="True quando a licença é um trial. Reservado: depende de a "
        "API StartBig repassar essa informação; hoje não é preenchido.",
    )
    em_carencia: bool = Field(
        False,
        description=(
            "True quando o plano venceu mas o gateway ainda re-tenta o cartao. "
            "A tela usa isto para avisar sem travar."
        ),
    )
    dias_restantes_carencia: Optional[int] = Field(
        None, description="Dias que ainda faltam da carencia, quando estiver em carencia"
    )
    modulos: Optional[List[str]] = Field(
        None,
        description=(
            "Modulos liberados para esta licenca, lidos do JWT assinado. "
            "AUSENTE/None = token sem a claim (emitido antes dos modulos existirem). "
            "Lista VAZIA = a plataforma ainda nao cadastrou modulo nenhum. "
            "Os dois casos significam 'nao sei' e LIBERAM; so uma lista "
            "PREENCHIDA sem o identificador e que bloqueia."
        ),
    )


class LicencaErroResponse(BaseModel):
    """Corpo do erro HTTP 403 para problemas de licença."""
    codigo: str = Field(
        ...,
        description=(
            "LICENCA_DE_OUTRA_MAQUINA | MAQUINA_NAO_IDENTIFICADA | REQUISITA_CONEXAO_INTERNET | "
            "LICENCA_EXPIRADA | LICENCA_NAO_ENCONTRADA | CHAVE_CORROMPIDA"
        ),
    )
    mensagem: str = Field(..., description="Mensagem descritiva do erro")


# ===========================================================================
# Renovação Ativa de Token (Etapa 4)
# ===========================================================================

class ValidarPayload(BaseModel):
    """Payload enviado à API StartBig para renovação ativa do token."""
    chave: str = Field(..., description="UUID da licença")
    hwid: str = Field(..., description="Hardware ID da máquina")


class ValidarResponse(BaseModel):
    """Resposta de sucesso da API StartBig ao validar/renovar o token."""
    valida: bool = Field(..., description="True se a licença é válida")
    licencaId: str = Field(..., description="UUID da licença")
    status: str = Field(..., description="Status da licença (ex: ATIVA)")
    dataVencimento: datetime = Field(..., description="Data de vencimento da licença")
    token: str = Field(..., description="Novo token JWT renovado")
    ultimaSincronizacao: datetime = Field(..., description="Timestamp da sincronização")
    gracePeriodDias: int = Field(..., description="Dias de período de carência offline")
    proximaValidacaoEm: datetime = Field(..., description="Data da próxima validação obrigatória")

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


class ValidarErroResponse(BaseModel):
    """Resposta de erro da API StartBig ao validar/renovar o token."""
    valida: bool = Field(False, description="Sempre False para erros")
    motivo: str = Field(..., description="Motivo da recusa (ex: Licença vencida)")
    status: str = Field(..., description="Status da licença (VENCIDA, BLOQUEADA, SUSPENSA, REVOGADA)")
