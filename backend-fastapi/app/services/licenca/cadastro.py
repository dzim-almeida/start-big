# ---------------------------------------------------------------------------
# ARQUIVO: services/licenca/cadastro.py
# DESCRICAO: Licenca - auto-cadastro na API, chave publica e reconexao.
# ---------------------------------------------------------------------------

import logging
import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.licenca import (
    AutoCadastroPayload,
    AutoCadastroResponse,
    ChavePublicaResponse,
    LicencaEnderecoPayload,
)
from app.db.models.configuracao_licenca import ConfiguracaoLicenca
from app.db.crud.configuracao import licenca as licenca_crud
from app.core.hwid import obter_hwid
from app.services.licenca.constantes import API_AUTO_CADASTRO_URL, API_CHAVE_PUBLICA_URL, CONECTAR_TIMEOUT_SECONDS, MAX_RETRIES, TIMEOUT_SECONDS
from app.services.licenca.cripto import encriptar_valor

logger = logging.getLogger(__name__)


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
                detail = response.json().get("message", response.text)
                try:
                    body = response.json()
                    detail = body.get("message", body.get("detail", response.text))
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
# Resgate de Chave Pública (Endpoint 7)
# ===========================================================================

def _buscar_chave_publica_online() -> str:
    """
    Faz GET ao endpoint público da StartBig para obter a chave pública RSA PEM.

    Returns:
        str: Chave pública RSA em formato PEM.

    Raises:
        httpx.ConnectError / httpx.TimeoutException: Se offline.
        HTTPException 503: Se o servidor retornar erro.
    """
    with httpx.Client(timeout=CONECTAR_TIMEOUT_SECONDS) as client:
        response = client.get(API_CHAVE_PUBLICA_URL)

    if 200 <= response.status_code < 300:
        dados = ChavePublicaResponse(**response.json())
        return dados.publicKey

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"Falha ao obter chave pública: servidor retornou status {response.status_code}",
    )


def resgatar_chave_publica_online(
    db: Session,
    hwid: str,
    licenca_id: str,
) -> str:
    """
    Resgata a chave pública RSA da nuvem, encripta-a com o HWID
    e persiste na coluna public_key com commit independente.

    Args:
        db: Sessão do banco de dados.
        hwid: Hardware ID da máquina.
        licenca_id: UUID da licença.

    Returns:
        str: Chave pública PEM em texto limpo (para uso imediato em memória).

    Raises:
        httpx.ConnectError / httpx.TimeoutException: Se offline.
        HTTPException: Se o servidor retornar erro.
    """
    public_key_pem = _buscar_chave_publica_online()

    # Encriptar e persistir com commit independente
    licenca = licenca_crud.get_licenca(db)
    if licenca:
        licenca.public_key = encriptar_valor(public_key_pem, hwid)
        licenca_crud.update_licenca(db, licenca)
        db.commit()
        logger.info("[licenca] Chave pública resgatada e persistida com sucesso.")

    return public_key_pem


# ===========================================================================
# Orquestração Principal
# ===========================================================================

def registrar_licenca(
    db: Session,
    documento: str,
    nome_ou_razao: str,
    email: str,
    senha: str,
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
        senha=senha,
        hwid=hwid,
        endereco=endereco_payload,
    )

    resposta = _chamar_api_auto_cadastro(payload)

    # 3. Buscar chave pública RSA da plataforma StartBig
    public_key_pem = _buscar_chave_publica_online()

    # 4. Encriptar campos sensíveis
    chave_ativacao_enc = encriptar_valor(resposta.chaveAtivacao, hwid)
    public_key_enc = encriptar_valor(public_key_pem, hwid)

    # 5. Criar registro no banco
    licenca = ConfiguracaoLicenca(
        cliente_id=resposta.clienteId,
        hwid=hwid,
        licenca_id=resposta.licencaId,
        chave_ativacao=chave_ativacao_enc,
        public_key=public_key_enc,
        limite=resposta.limite,
        data_vencimento=resposta.dataVencimento,
        token=resposta.token,
        ultima_sinc=resposta.ultimaSincronizacao,
        grace_period=resposta.gracePeriodDias,
        proxima_validacao=resposta.proximaValidacaoEm,
    )

    return licenca_crud.create_licenca(db, licenca)


# ===========================================================================
# Reconexão de Licença
# ===========================================================================

def reconnect_licenca(
    db: Session,
    email: str,
    senha: str,
) -> ConfiguracaoLicenca:
    """
    Reconecta uma licença existente na StartBig usando email e senha.
    """
    hwid = obter_hwid()

    # Verifica se já existe
    existente = licenca_crud.get_licenca_by_hwid(db, hwid)
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta máquina já possui uma licença registrada.",
        )

    payload = {
        "email": email,
        "senha": senha,
        "hwid": hwid
    }

    try:
        with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
            response = client.post(
                "https://api.startbig.com.br/erp/auth/login",
                json=payload,
            )
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Falha de conexão com a StartBig: {e}"
        )

    if 200 <= response.status_code < 300:
        resposta = AutoCadastroResponse(**response.json())
    else:
        detail = response.text
        try:
            body = response.json()
            detail = body.get("message", body.get("msg", detail))
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Credenciais inválidas: {detail}"
        )

    # 3. Buscar chave pública RSA da plataforma StartBig
    public_key_pem = _buscar_chave_publica_online()

    # 4. Encriptar campos sensíveis
    chave_ativacao_enc = encriptar_valor(resposta.chaveAtivacao, hwid)
    public_key_enc = encriptar_valor(public_key_pem, hwid)

    # 5. Troca de computador: o banco veio copiado do servidor antigo e trouxe
    # a licença DE LÁ, cifrada com o HWID de lá. Aqui ela não decifra (é o que
    # levanta CLONAGEM_DETECTADA no boot) e segura o `licenca_id` unique que a
    # linha nova vai usar. Sai só agora, com a nuvem já tendo aprovado o login:
    # quem decide se a conta pode rodar nesta máquina é ela, não o arquivo.
    removidas = licenca_crud.remover_licencas_de_outras_maquinas(db, hwid)
    if removidas:
        logger.info(
            "[licenca] Reconexão em máquina nova: %d licença(s) de outra máquina substituída(s).",
            removidas,
        )

    # 6. Criar registro no banco
    licenca = ConfiguracaoLicenca(
        cliente_id=resposta.clienteId or "000000000-0000000000-0000000000",
        hwid=hwid,
        licenca_id=resposta.licencaId,
        chave_ativacao=chave_ativacao_enc,
        public_key=public_key_enc,
        limite=resposta.limite,
        data_vencimento=resposta.dataVencimento,
        token=resposta.token,
        ultima_sinc=resposta.ultimaSincronizacao,
        grace_period=resposta.gracePeriodDias,
        proxima_validacao=resposta.proximaValidacaoEm,
    )

    return licenca_crud.create_licenca(db, licenca)
