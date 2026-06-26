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
from datetime import datetime, timezone

import httpx
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import HTTPException, status
from jose import jwt, JWTError, JOSEError
from sqlalchemy.orm import Session

from app.schemas.licenca import (
    AutoCadastroPayload,
    AutoCadastroResponse,
    ConectarPayload,
    LicencaEnderecoPayload,
)
from app.db.models.configuracao_licenca import ConfiguracaoLicenca
from app.db.crud import configuracao_licenca as licenca_crud
from app.core.hwid import obter_hwid

logger = logging.getLogger(__name__)

API_AUTO_CADASTRO_URL = "https://api.startbig.com.br/erp/auto-cadastro"
API_CONECTAR_URL = "https://api.startbig.com.br/licenca/conectar"
TIMEOUT_SECONDS = 30
CONECTAR_TIMEOUT_SECONDS = 3
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
                    API_AUTO_CADASTRO_URL,
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
    documento: str,
    nome_ou_razao: str,
    email: str,
    endereco_data: dict,
) -> ConfiguracaoLicenca:
    """
    Orquestra o auto-cadastro de licença:
    1. Obtém o HWID da máquina localmente
    2. Verifica se já existe licença para este HWID
    3. Chama a API externa
    4. Encripta campos sensíveis
    5. Persiste no banco (flush, não commit — commit fica com _handle_db_transaction)

    Args:
        db: Sessão do banco de dados.
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
    # 1. Obter HWID da máquina
    hwid = obter_hwid()

    # 2. Verificar duplicidade de HWID
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


# ===========================================================================
# Validação de Sessão (Etapa 2 — Boot Check)
# ===========================================================================

def _erro_licenca(codigo: str, mensagem: str) -> HTTPException:
    """
    Cria uma HTTPException 403 padronizada para erros de licença inválida.
    E um HTTPException 404 para licença não encontrada.
    """
    
    if codigo == "LICENCA_NAO_ENCONTRADA":
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"codigo": codigo, "mensagem": mensagem},
        )

    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"codigo": codigo, "mensagem": mensagem},
    )


def _tentar_conexao_remota(
    db: Session,
    licenca: ConfiguracaoLicenca,
    chave_ativacao: str,
    hwid: str,
) -> dict:
    """
    Tenta validar a licença online via POST /licenca/conectar.

    Raises:
        httpx.ConnectError / httpx.TimeoutException: Se offline (fallback).
        HTTPException 403: Se o servidor recusar a licença.
    """
    payload = ConectarPayload(chave=chave_ativacao, hwid=hwid)

    with httpx.Client(timeout=CONECTAR_TIMEOUT_SECONDS) as client:
        response = client.post(
            API_CONECTAR_URL,
            json=payload.model_dump(),
        )

    if 200 <= response.status_code < 300:
        resposta = AutoCadastroResponse(**response.json())

        # Atualizar dados da licença atomicamente
        licenca.ultima_sinc = resposta.ultimaSincronizacao
        licenca.proxima_validacao = resposta.proximaValidacaoEm
        licenca.token = resposta.token
        licenca.data_vencimento = resposta.dataVencimento
        licenca.limite = resposta.limite
        licenca.grace_period = resposta.gracePeriodDias

        # Re-encriptar session_key e chave_ativacao caso tenham mudado
        licenca.session_key = encriptar_valor(resposta.sessionKey, hwid)

        licenca_crud.update_licenca(db, licenca)
        db.commit()

        logger.info("[licenca] Validação online bem-sucedida.")
        return {"status": "online_valid"}

    # Erro 4xx do servidor (licença inválida/suspensa)
    if 400 <= response.status_code < 500:
        detail = response.text
        try:
            body = response.json()
            detail = body.get("msg", body.get("message", response.text))
        except Exception:
            pass
        raise _erro_licenca("LICENCA_RECUSADA", f"Servidor recusou a licença: {detail}")

    # Erro 5xx — tratar como offline (fallback)
    raise httpx.ConnectError(f"Servidor retornou status {response.status_code}")


def _validar_offline(
    licenca: ConfiguracaoLicenca,
    session_key: str,
) -> dict:
    """
    Validação offline usando JWT RS256 e regras de grace period.

    Args:
        licenca: Registro da licença no banco.
        session_key: Session key descriptografada (chave pública RS256).

    Returns:
        dict com status e dias_restantes.

    Raises:
        HTTPException 403: Se a validação offline falhar.
    """
    agora = datetime.now(timezone.utc)

    # 1. Validar JWT com a session_key (shared secret HS256)
    try:
        jwt.decode(
            licenca.token,
            session_key,
            algorithms=["HS256"],
            options={"verify_exp": True, "verify_aud": False},
        )
    except (JWTError, JOSEError) as e:
        logger.warning("[licenca] Falha na validação JWT offline: %s", e)
        raise _erro_licenca(
            "REQUISITA_CONEXAO_INTERNET",
            "Token de licença inválido ou expirado. Conecte-se à internet para revalidar.",
        )

    # 2. Verificar data de vencimento do plano
    data_vencimento = licenca.data_vencimento
    if data_vencimento.tzinfo is None:
        data_vencimento = data_vencimento.replace(tzinfo=timezone.utc)

    if agora >= data_vencimento:
        raise _erro_licenca(
            "LICENCA_EXPIRADA",
            "Sua licença expirou. Entre em contato com o suporte para renovação.",
        )

    # 3. Verificar grace period (dias desde última sincronização)
    ultima_sinc = licenca.ultima_sinc
    if ultima_sinc.tzinfo is None:
        ultima_sinc = ultima_sinc.replace(tzinfo=timezone.utc)

    dias_offline = (agora - ultima_sinc).days
    if dias_offline > licenca.grace_period:
        raise _erro_licenca(
            "REQUISITA_CONEXAO_INTERNET",
            f"Limite de {licenca.grace_period} dias offline excedido ({dias_offline} dias). "
            "Conecte-se à internet para revalidar a licença.",
        )

    # 4. Verificar próxima validação obrigatória
    proxima_validacao = licenca.proxima_validacao
    if proxima_validacao.tzinfo is None:
        proxima_validacao = proxima_validacao.replace(tzinfo=timezone.utc)

    if agora >= proxima_validacao:
        raise _erro_licenca(
            "REQUISITA_CONEXAO_INTERNET",
            "Data de validação obrigatória atingida. Conecte-se à internet para revalidar.",
        )

    # 5. Calcular dias restantes
    dias_ate_vencimento = (data_vencimento - agora).days
    dias_ate_grace = licenca.grace_period - dias_offline
    dias_ate_validacao = (proxima_validacao - agora).days
    dias_restantes = min(dias_ate_vencimento, dias_ate_grace, dias_ate_validacao)

    logger.info(
        "[licenca] Validação offline aceita. Dias restantes: %d", dias_restantes
    )
    return {"status": "offline_valid", "dias_restantes": dias_restantes}


def verificar_licenca_ativa(db: Session) -> dict:
    """
    Verifica se a licença da máquina está ativa.

    Fluxo:
    1. Obtém HWID local.
    2. Busca licença no banco.
    3. Testa descriptografia (anti-clonagem).
    4. Tenta validação online (prioridade).
    5. Fallback offline se a nuvem estiver inacessível.

    Returns:
        dict: {"status": "online_valid"} ou {"status": "offline_valid", "dias_restantes": N}

    Raises:
        HTTPException 403: Com código estruturado em caso de falha.
    """
    # 1. Obter HWID
    try:
        hwid = obter_hwid()
    except RuntimeError as e:
        logger.error("[licenca] Falha ao obter HWID: %s", e)
        raise _erro_licenca(
            "CLONAGEM_DETECTADA",
            "Não foi possível identificar a máquina. Verifique a instalação.",
        )

    # 2. Buscar licença no banco
    licenca = licenca_crud.get_licenca(db)
    if not licenca:
        raise _erro_licenca(
            "LICENCA_NAO_ENCONTRADA",
            "Nenhuma licença encontrada. Execute o setup inicial do sistema.",
        )

    # 3. Descriptografar campos sensíveis (teste anti-clonagem)
    try:
        chave_ativacao = decriptar_valor(licenca.chave_ativacao, hwid)
        session_key = decriptar_valor(licenca.session_key, hwid)
    except Exception as e:
        logger.warning("[licenca] Falha na descriptografia — possível clonagem: %s", e)
        raise _erro_licenca(
            "CLONAGEM_DETECTADA",
            "Falha na verificação de integridade. "
            "O banco de dados pode ter sido copiado de outra máquina.",
        )

    # 4. Tentar validação online (prioridade)
    try:
        return _tentar_conexao_remota(db, licenca, chave_ativacao, hwid)
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        logger.info("[licenca] Nuvem inacessível (%s), iniciando fallback offline.", e)
    except HTTPException:
        raise  # Erros 403 da API são repassados

    # 5. Fallback offline
    return _validar_offline(licenca, session_key)
