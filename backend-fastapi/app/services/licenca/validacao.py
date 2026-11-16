# ---------------------------------------------------------------------------
# ARQUIVO: services/licenca/validacao.py
# DESCRICAO: Licenca - validacao online e offline, e os modulos liberados.
# ---------------------------------------------------------------------------

import logging
import os
from datetime import datetime, timezone
import httpx
from cryptography.exceptions import InvalidTag
from fastapi import HTTPException
from jose import jwt, JWTError, JOSEError
from sqlalchemy.orm import Session
from app.schemas.licenca import (
    AutoCadastroResponse,
    ConectarPayload,
)
from app.db.models.configuracao_licenca import ConfiguracaoLicenca
from app.db.crud.configuracao import licenca as licenca_crud
from app.core.hwid import obter_hwid
from app.services.licenca.cadastro import resgatar_chave_publica_online
from app.services.licenca.constantes import API_CONECTAR_URL, CONECTAR_TIMEOUT_SECONDS
from app.services.licenca.cripto import decriptar_valor
from app.services.licenca.recusa import _carencia_vigente, _detalhe_da_recusa, _erro_licenca, _limpar_bloqueio, _recusa_por_vencimento, erro_licenca_de_outra_maquina

logger = logging.getLogger(__name__)


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
        # Carencia: o servidor manda, a loja guarda. Guardar e o que permite
        # honrar os dias de folga tambem quando a internet cair no meio deles.
        licenca.em_carencia = resposta.emCarencia
        licenca.data_limite_carencia = resposta.dataLimiteCarencia
        _limpar_bloqueio(licenca)

        licenca_crud.update_licenca(db, licenca)
        db.commit()

        logger.info("[licenca] Validação online bem-sucedida.")

        # dias_restantes a partir do vencimento recém-sincronizado do servidor,
        # para o frontend (badge de licença) alertar sobre renovação também no
        # caminho online — antes só o fallback offline devolvia esse número.
        vencimento = licenca.data_vencimento
        if vencimento.tzinfo is None:
            vencimento = vencimento.replace(tzinfo=timezone.utc)
        agora_online = datetime.now(timezone.utc)
        em_carencia = _carencia_vigente(licenca, agora_online)

        # Em carencia o vencimento ja passou: o numero util para a tela e
        # quanto falta da folga, nao um negativo do plano.
        if em_carencia:
            limite = licenca.data_limite_carencia
            if limite.tzinfo is None:
                limite = limite.replace(tzinfo=timezone.utc)
            dias_carencia = (limite - agora_online).days
            dias_restantes = dias_carencia
        else:
            dias_carencia = None
            dias_restantes = (vencimento - agora_online).days

        return {
            "status": "online_valid",
            "dias_restantes": dias_restantes,
            "em_carencia": em_carencia,
            "dias_restantes_carencia": dias_carencia,
        }

    # Erro 4xx do servidor (licença inválida/suspensa/vencida)
    if 400 <= response.status_code < 500:
        detail, corpo = _detalhe_da_recusa(response)

        # Vencimento tem saída pelo próprio sistema: o frontend deixa entrar e
        # leva para a tela de cobrança. Qualquer outra recusa segue barrando
        # antes do login, como sempre.
        if _recusa_por_vencimento(response.status_code, detail, corpo, licenca):
            logger.info("[licenca] Nuvem recusou por vencimento: %s", detail)
            # A frase e nossa, nao a da nuvem ("Licenca vencida. Acesso
            # negado."): quem le isto e o dono da loja, numa tela que ao mesmo
            # tempo garante que os dados dele estao inteiros e oferece o
            # pagamento. "Acesso negado" soa a punicao e contradiz a tela.
            raise _erro_licenca(
                "LICENCA_EXPIRADA",
                "Sua assinatura venceu. Renove para voltar a usar o sistema.",
            )

        raise _erro_licenca("LICENCA_RECUSADA", f"Servidor recusou a licença: {detail}")

    # Erro 5xx — tratar como offline (fallback)
    raise httpx.ConnectError(f"Servidor retornou status {response.status_code}")


def _decifrar_public_key(licenca: ConfiguracaoLicenca, hwid: str) -> str | None:
    """Chave publica da licenca, ou None se nao der para le-la.

    Best-effort de proposito. Quem depende dela para AUTORIZAR -- a validacao
    offline -- tem o proprio caminho, com resgate online e erro CHAVE_CORROMPIDA.
    Aqui ela serve so para ler claims, e nesse uso uma chave ilegivel nao pode
    virar erro de licenca: o caminho online funciona hoje sem tocar nela, e
    passar a exigi-la derrubaria instalacao que esta rodando bem.
    """
    if not licenca.public_key:
        return None

    try:
        return decriptar_valor(licenca.public_key, hwid)
    except Exception as e:
        logger.warning("[licenca] public_key ilegivel para leitura de modulos: %s", e)
        return None


def ler_modulos_liberados(token: str | None, public_key: str | None) -> list[str] | None:
    """Modulos que o token carrega, ou None quando nao da para saber.

    None NAO e "nenhum modulo": e "nao sei", e quem consome trata como libera
    tudo. Token emitido antes desta versao nao tem a claim, e o contrato da
    plataforma manda tratar ausencia como acesso liberado -- o JWT vive 7 dias,
    entao no dia em que a claim estreia boa parte da base ainda esta com token
    antigo, e bloquear aqui esconderia o sistema de cliente pagante por uma
    semana, sem erro aparecendo em lugar nenhum.

    Lista presente e VAZIA e outra coisa e passa adiante como lista vazia:
    significa "nenhum modulo liberado".

    A assinatura E conferida. Sem isso a claim seria o unico elo forjavel entre
    a API e o ERP: o token mora no SQLite da propria maquina do cliente, e ler
    sem verificar deixaria qualquer um se conceder todos os modulos editando o
    banco. Sem chave publica para conferir devolvemos None -- libera, mas por
    nao saber, nunca por acreditar num payload nao verificado.
    """
    if not token or not public_key:
        return None

    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            # A validade ja foi decidida antes de chegar aqui: no caminho online
            # pelo servidor, no offline pelo proprio _validar_offline. Reprovar
            # por expiracao neste ponto so trocaria uma licenca valida por um
            # menu vazio.
            options={"verify_exp": False, "verify_aud": False},
        )
    except (JWTError, JOSEError) as e:
        logger.warning("[licenca] Nao foi possivel ler os modulos do token: %s", e)
        return None

    modulos = payload.get("modulos")
    if modulos is None:
        return None

    if not isinstance(modulos, list):
        logger.warning(
            "[licenca] Claim 'modulos' em formato inesperado (%s) -- ignorada.",
            type(modulos).__name__,
        )
        return None

    return [str(m) for m in modulos]


def modulos_da_licenca(db: Session) -> list[str] | None:
    """Modulos do token guardado, para quem precisa decidir acesso fora do /status.

    Mesma regra de sempre: None = nao sei = libera. Le do token corrente a cada
    chamada, e nao de um campo proprio, porque o token e a unica copia assinada
    -- guardar os modulos ao lado dele criaria uma segunda verdade, que
    envelhece e que o cliente pode editar.
    """
    licenca = licenca_crud.get_licenca(db)
    if not licenca:
        return None

    try:
        hwid = obter_hwid()
    except RuntimeError:
        return None

    return ler_modulos_liberados(licenca.token, _decifrar_public_key(licenca, hwid))


def _validar_offline(
    licenca: ConfiguracaoLicenca,
    public_key: str,
) -> dict:
    """
    Validação offline usando JWT RS256 e regras de grace period.

    Args:
        licenca: Registro da licença no banco.
        public_key: Chave pública RSA PEM descriptografada.

    Returns:
        dict com status e dias_restantes.

    Raises:
        HTTPException 403: Se a validação offline falhar.
    """
    agora = datetime.now(timezone.utc)

    # 1. Validar JWT com a chave pública RSA
    try:
        jwt.decode(
            licenca.token,
            public_key,
            algorithms=["RS256"],
            options={"verify_exp": True, "verify_aud": False}
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

    # A carencia afrouxa ESTE limite e so ele. Os dois seguintes -- validade
    # offline e proxima validacao obrigatoria -- continuam valendo iguais, senao
    # a carencia viraria uma porta para rodar desconectado o tempo que quisesse.
    if agora >= data_vencimento and not _carencia_vigente(licenca, agora):
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
    # Em carencia o vencimento ja passou, entao `dias_ate_vencimento` e
    # NEGATIVO -- e a tela mostraria "-3 dias restantes". Nesse estado quem
    # conta e o prazo da carencia, que e o que de fato resta.
    if _carencia_vigente(licenca, agora):
        limite_carencia = licenca.data_limite_carencia
        if limite_carencia.tzinfo is None:
            limite_carencia = limite_carencia.replace(tzinfo=timezone.utc)
        dias_ate_vencimento = (limite_carencia - agora).days
    else:
        dias_ate_vencimento = (data_vencimento - agora).days

    dias_ate_grace = licenca.grace_period - dias_offline
    dias_ate_validacao = (proxima_validacao - agora).days
    dias_restantes = min(dias_ate_vencimento, dias_ate_grace, dias_ate_validacao)

    logger.info(
        "[licenca] Validação offline aceita. Dias restantes: %d", dias_restantes
    )
    em_carencia = _carencia_vigente(licenca, agora)
    return {
        "status": "offline_valid",
        "dias_restantes": dias_restantes,
        "em_carencia": em_carencia,
        "dias_restantes_carencia": dias_ate_vencimento if em_carencia else None,
    }


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
    # 0. Simulacao de licenca vencida (DESENVOLVIMENTO)
    #
    # A tela de "somente renovacao" so aparece com a licenca vencida -- e uma
    # licenca de verdade nao vence na hora que se quer testar. Sem isto, aquela
    # tela estrearia em producao, na frente do cliente que menos pode receber
    # surpresa: o que acabou de perder o acesso.
    #
    # So por variavel de ambiente, nunca por configuracao de loja. Nao ha
    # caminho pelo qual uma instalacao real ligue isto sem alguem editar o
    # ambiente do servico a mao.
    if os.getenv("STARTBIG_LICENCA_EXPIRADA_SIMULADA", "").strip().lower() in {"1", "true", "sim"}:
        logger.warning("[licenca] SIMULACAO de licenca vencida ligada por variavel de ambiente.")
        raise _erro_licenca(
            "LICENCA_EXPIRADA",
            "Sua assinatura expirou (simulacao de desenvolvimento).",
        )

    # 1. Obter HWID
    try:
        hwid = obter_hwid()
    except RuntimeError as e:
        logger.error("[licenca] Falha ao obter HWID: %s", e)
        raise _erro_licenca(
            "MAQUINA_NAO_IDENTIFICADA",
            "Não foi possível identificar a máquina. Verifique a instalação.",
        )

    # 2. Buscar licença no banco
    licenca = licenca_crud.get_licenca(db)
    if not licenca:
        raise _erro_licenca(
            "LICENCA_NAO_ENCONTRADA",
            "Nenhuma licença encontrada. Execute o setup inicial do sistema.",
        )

    # 3. Descriptografar chave de ativação: só decifra na máquina que a ativou
    try:
        chave_ativacao = decriptar_valor(licenca.chave_ativacao, hwid)
    except Exception as e:
        logger.warning("[licenca] Licença ativada em outra máquina: %s", e)
        raise erro_licenca_de_outra_maquina()

    # 4. Tentar validação online (prioridade)
    try:
        resultado = _tentar_conexao_remota(db, licenca, chave_ativacao, hwid)
        # O token acabou de ser trocado pelo que o servidor mandou: os módulos
        # saem DELE, na hora. Quem manda é sempre o token corrente.
        resultado["modulos"] = ler_modulos_liberados(
            licenca.token, _decifrar_public_key(licenca, hwid)
        )
        return resultado
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        logger.info("[licenca] Nuvem inacessível (%s), iniciando fallback offline.", e)
    except HTTPException:
        raise  # Erros 403 da API são repassados

    # 5. Desencriptar chave pública com resiliência
    public_key = None
    try:
        if licenca.public_key:
            public_key = decriptar_valor(licenca.public_key, hwid)
    except (InvalidTag, Exception) as e:
        logger.warning("[licenca] public_key corrompida, tentando resgate online: %s", e)

    if not public_key:
        try:
            public_key = resgatar_chave_publica_online(db, hwid, licenca.licenca_id)
        except Exception:
            raise _erro_licenca(
                "CHAVE_CORROMPIDA",
                "Chave de segurança corrompida. Necessária ligação à internet para recuperação.",
            )

    # 6. Fallback offline
    resultado = _validar_offline(licenca, public_key)
    resultado["modulos"] = ler_modulos_liberados(licenca.token, public_key)
    return resultado
