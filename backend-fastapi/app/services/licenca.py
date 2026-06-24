# ---------------------------------------------------------------------------
# ARQUIVO: services/licenca.py
# MÓDULO: Regras de Negócio (Service Layer)
# DESCRIÇÃO: Serviço de licenciamento - auto-cadastro na API StartBig,
#            criptografia AES-256-GCM e persistência local.
# ---------------------------------------------------------------------------

import base64
import hashlib
import logging
import os

import httpx
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.licenca import (
    AutoCadastroPayload,
    AutoCadastroResponse,
    LicencaEnderecoPayload,
)
from app.db.models.configuracao_licenca import ConfiguracaoLicenca
from app.db.crud import configuracao_licenca as licenca_crud

logger = logging.getLogger(__name__)

API_URL = "https://api.startbig.com.br/erp/auto-cadastro"
TIMEOUT_SECONDS = 30
MAX_RETRIES = 3


# ===========================================================================
# Criptografia AES-256-GCM
# ===========================================================================

def _derivar_chave(hwid: str) -> bytes:
    """
    Deriva uma chave AES-256 (32 bytes) a partir do HWID usando SHA-256.
    Determinístico: mesmo HWID sempre gera a mesma chave.
    """
    return hashlib.sha256(hwid.encode("utf-8")).digest()


def encriptar_valor(valor: str, hwid: str) -> str:
    """
    Encripta um valor usando AES-256-GCM com chave derivada do HWID.
    Retorna: base64(nonce + ciphertext + tag)
    """
    chave = _derivar_chave(hwid)
    aesgcm = AESGCM(chave)
    nonce = os.urandom(12)  # 96-bit nonce para GCM
    ciphertext = aesgcm.encrypt(nonce, valor.encode("utf-8"), None)
    # nonce (12 bytes) + ciphertext (inclui tag de 16 bytes)
    return base64.b64encode(nonce + ciphertext).decode("utf-8")


def decriptar_valor(valor_encriptado: str, hwid: str) -> str:
    """
    Decripta um valor previamente encriptado com encriptar_valor.
    """
    chave = _derivar_chave(hwid)
    dados = base64.b64decode(valor_encriptado)
    nonce = dados[:12]
    ciphertext = dados[12:]
    aesgcm = AESGCM(chave)
    return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")


# ===========================================================================
# Chamada à API Externa com Retry
# ===========================================================================

def _chamar_api_auto_cadastro(payload: AutoCadastroPayload) -> AutoCadastroResponse:
    """
    Faz a requisição HTTP POST para a API de auto-cadastro com retry.

    Retry: apenas para erros 5xx, ConnectError e TimeoutException.
    Erros 4xx: propagados imediatamente (sem retry).

    Raises:
        HTTPException 422: Se a API retornar erro 4xx (validação, duplicidade).
        HTTPException 503: Se não conseguir conectar após todas as tentativas.
    """
    ultimo_erro = None

    for tentativa in range(1, MAX_RETRIES + 1):
        try:
            with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
                response = client.post(
                    API_URL,
                    json=payload.model_dump(exclude_none=True),
                )

            if 200 <= response.status_code < 300:
                return AutoCadastroResponse(**response.json())

            # Erros 4xx da API (ex: documento duplicado) — não faz retry
            if 400 <= response.status_code < 500:
                detail = response.text
                try:
                    body = response.json()
                    detail = body.get("msg", body.get("detail", response.text))
                except Exception:
                    pass
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Erro no auto-cadastro de licença: {detail}"
                )

            # Erros 5xx — faz retry
            ultimo_erro = f"API retornou status {response.status_code}"
            logger.warning(
                "[licenca] Tentativa %d/%d falhou: %s",
                tentativa, MAX_RETRIES, ultimo_erro,
            )

        except httpx.ConnectError as e:
            ultimo_erro = f"Falha de conexão: {e}"
            logger.warning(
                "[licenca] Tentativa %d/%d: %s", tentativa, MAX_RETRIES, ultimo_erro
            )
        except httpx.TimeoutException as e:
            ultimo_erro = f"Timeout: {e}"
            logger.warning(
                "[licenca] Tentativa %d/%d: %s", tentativa, MAX_RETRIES, ultimo_erro
            )
        except HTTPException:
            raise  # Re-raise erros 4xx sem retry
        except Exception as e:
            ultimo_erro = f"Erro inesperado: {e}"
            logger.error(
                "[licenca] Tentativa %d/%d: %s", tentativa, MAX_RETRIES, ultimo_erro
            )

    # Todas as tentativas falharam
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=(
            f"Não foi possível conectar ao servidor de licenças após {MAX_RETRIES} tentativas. "
            f"Verifique sua conexão com a internet. Último erro: {ultimo_erro}"
        ),
    )


# ===========================================================================
# Orquestração Principal
# ===========================================================================

def registrar_licenca(
    db: Session,
    hwid: str,
    documento: str,
    nome_ou_razao: str,
    email: str,
    endereco_data: dict,
) -> ConfiguracaoLicenca:
    """
    Orquestra o auto-cadastro de licença:
    1. Verifica se já existe licença para este HWID
    2. Chama a API externa
    3. Encripta campos sensíveis
    4. Persiste no banco (flush, não commit — commit fica com _handle_db_transaction)

    Args:
        db: Sessão do banco de dados.
        hwid: Hardware ID da máquina.
        documento: CPF ou CNPJ (apenas números).
        nome_ou_razao: Nome ou Razão Social.
        email: Email do responsável.
        endereco_data: Dict com campos de endereço (pode ser vazio).

    Returns:
        ConfiguracaoLicenca: O registro de licença criado.

    Raises:
        HTTPException 409: Se a máquina já possui licença.
        HTTPException 422: Se a API retornar erro de validação.
        HTTPException 503: Se não conseguir conectar ao servidor.
    """
    # 1. Verificar duplicidade de HWID
    existente = licenca_crud.get_licenca_by_hwid(db, hwid)
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta máquina já possui uma licença registrada.",
        )

    # 2. Montar payload e chamar API
    endereco_payload = None
    if endereco_data and endereco_data.get("cep"):
        endereco_payload = LicencaEnderecoPayload(**endereco_data)

    payload = AutoCadastroPayload(
        documento=documento,
        nomeOuRazao=nome_ou_razao,
        email=email,
        hwid=hwid,
        endereco=endereco_payload,
    )

    resposta = _chamar_api_auto_cadastro(payload)

    # 3. Encriptar campos sensíveis
    chave_ativacao_enc = encriptar_valor(resposta.chaveAtivacao, hwid)
    session_key_enc = encriptar_valor(resposta.sessionKey, hwid)

    # 4. Criar registro no banco
    licenca = ConfiguracaoLicenca(
        cliente_id=resposta.clienteId,
        hwid=hwid,
        licenca_id=resposta.licencaId,
        chave_ativacao=chave_ativacao_enc,
        session_key=session_key_enc,
        limite=resposta.limite,
        data_vencimento=resposta.dataVencimento,
        token=resposta.token,
        ultima_sinc=resposta.ultimaSincronizacao,
        grace_period=resposta.gracePeriodDias,
        proxima_validacao=resposta.proximaValidacaoEm,
    )

    return licenca_crud.create_licenca(db, licenca)
