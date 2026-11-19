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
from app.services.licenca.cripto import decriptar_valor  # so para a chave publica (que nao vai ao cofre)
from app.services.licenca import segredos_licenca  # unico dono do token e da chave de ativacao (LIC-01)
from app.services.licenca import relogio  # relogio que voltou no tempo (LIC-02)
from app.services.licenca.recusa import (
    CODIGOS_REPASSADOS_AO_FRONT,
    _carencia_vigente,
    _codigo_da_recusa,
    _detalhe_da_recusa,
    _erro_licenca,
    _limpar_bloqueio,
    _recusa_por_vencimento,
)

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
        # O token novo vai trancado para o cofre. Se o cofre falhar, o anterior
        # fica (ainda vale ate 7 dias), o log registra, e a licenca continua
        # valida: a gravacao e tentada de novo na proxima validacao (LIC-01 §6.4).
        segredos_licenca.gravar_token_na_licenca(licenca, resposta.token)
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

        # dias_restantes: o número que a API calculou (F26, LIC-02 §6.4). Ele
        # não depende do relógio deste computador, que pode estar errado. Só
        # quando a API ainda não manda o campo o número é calculado aqui, e a
        # resposta o marca como estimativa.
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

        estimativa = resposta.diasRestantes is None
        if not estimativa:
            dias_restantes = resposta.diasRestantes
        if em_carencia and resposta.diasRestantesCarencia is not None:
            dias_carencia = resposta.diasRestantesCarencia
            dias_restantes = dias_carencia   # em carência, o prazo que conta é o dela

        return {
            "status": "online_valid",
            "dias_restantes": dias_restantes,
            "em_carencia": em_carencia,
            "dias_restantes_carencia": dias_carencia,
            "estimativa": estimativa,
        }

    # Erro 4xx do servidor (licença inválida/suspensa/vencida)
    if 400 <= response.status_code < 500:
        detail, corpo = _detalhe_da_recusa(response)

        # Recusa com código que o front trata pelo nome (F27, LIC-02 §6.6):
        # o código da API chega à tela como veio. Hoje: LICENCA_TRANSFERIDA.
        codigo = _codigo_da_recusa(corpo)
        if codigo in CODIGOS_REPASSADOS_AO_FRONT:
            logger.info("[licenca] Nuvem recusou com o código %s: %s", codigo, detail)
            raise _erro_licenca(codigo, CODIGOS_REPASSADOS_AO_FRONT[codigo])

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

    return ler_modulos_liberados(_token_para_ler_modulos(licenca), _decifrar_public_key(licenca, hwid))


def _token_para_ler_modulos(licenca: ConfiguracaoLicenca) -> str | None:
    """Token aberto do cofre so para LER os modulos, ou None se nao abrir.

    Mesma filosofia de _decifrar_public_key: aqui o token so serve para ler a
    claim `modulos`, e None quer dizer "nao sei" (libera). Quem decide se a
    licenca vale e a validacao, que tem os proprios erros.
    """
    try:
        return segredos_licenca.ler_token(licenca.token)
    except Exception as e:  # noqa: BLE001 - cofre fora do ar ou token de outra maquina
        logger.warning("[licenca] Token ilegivel para leitura de modulos (%s).", type(e).__name__)
        return None


# ===========================================================================
# Claims do token assinado (LIC-02 §6.1 e §6.2, ACORDO D-13 e D-15)
# ===========================================================================
# "Claim" e cada informacao que vem DENTRO do token (licencaId, hwid,
# dataVencimento...). O token e assinado pela API com a chave privada dela, e
# o app confere essa assinatura com a chave publica: se alguem mudar uma
# virgula do token, a assinatura deixa de bater. As COLUNAS do banco, ao
# contrario, qualquer pessoa edita. Por isso, sem internet, os prazos saem do
# token, e nao das colunas.

def _claims_do_token(token: str, chave_publica: str) -> dict:
    """Confere a assinatura RS256 e devolve as claims do token.

    A validade ('exp') continua sendo conferida: token vencido tambem e
    recusado. Lanca JWTError/JOSEError se a assinatura nao bater.
    """
    return jwt.decode(
        token,
        chave_publica,
        algorithms=["RS256"],             # aceita so o algoritmo que a API usa
        options={"verify_aud": False},    # a API nao envia 'aud'
    )


def _data_da_claim(valor) -> datetime | None:
    """Converte a data de uma claim (texto ISO da API) em datetime com fuso.

    A API manda datas em ISO com "Z" no fim (UTC). Trocar o "Z" por "+00:00"
    deixa o fromisoformat entender em qualquer versao do Python.
    """
    if not valor:
        return None
    data = datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
    if data.tzinfo is None:
        data = data.replace(tzinfo=timezone.utc)   # sem fuso: a API fala em UTC
    return data


def _carencia_do_token(claims: dict, agora: datetime) -> bool:
    """A carencia so vale com a flag E a data limite no token, e a data nao passou.

    Flag sem data nao basta (mesma regra de recusa._carencia_vigente): um token
    com `emCarencia` e sem data daria uso ilimitado.
    """
    if not claims.get("emCarencia"):
        return False
    limite = _data_da_claim(claims.get("dataLimiteCarencia"))
    if limite is None:
        return False
    return agora < limite


def _conferir_identidade(claims: dict, licenca: ConfiguracaoLicenca, hwid: str) -> None:
    """O token precisa ser DESTA licenca e DESTA maquina (D-15).

    O `hwid` so e conferido quando o token tem o campo: a API emite
    `hwid: null` quando o conectar e feito sem maquina, e nesse caso a
    checagem da licenca basta.
    """
    if claims.get("licencaId") != licenca.licenca_id:
        raise _erro_licenca("TOKEN_DE_OUTRA_LICENCA", "O token não confere com esta instalação.")
    if claims.get("hwid") and claims.get("hwid") != hwid:
        raise _erro_licenca("TOKEN_DE_OUTRA_LICENCA", "O token não confere com esta máquina.")


def _validar_offline(
    licenca: ConfiguracaoLicenca,
    public_key: str,
    hwid: str | None = None,
) -> dict:
    """
    Validação offline: tudo o que decide vem do token ASSINADO (LIC-02).

    Args:
        licenca: Registro da licença no banco.
        public_key: Chave pública RSA PEM, já aberta.
        hwid: HWID desta máquina (quem chama já tem; se faltar, é lido aqui).

    Returns:
        dict com status, dias_restantes (estimados), carência e, se o relógio
        recuou, o aviso "relogio_recuou".

    Raises:
        HTTPException 403: Se a validação offline falhar.
    """
    agora_real = datetime.now(timezone.utc)

    # 0. Abrir o token guardado no cofre. Sem internet nao ha como pedir outro,
    #    entao um token que nao abre aqui vira TOKEN_ILEGIVEL (LIC-01 §6.4).
    token = segredos_licenca.abrir_token_ou_erro(licenca.token)

    # 1. Conferir a assinatura e a validade ('exp') do token e ler as claims.
    try:
        claims = _claims_do_token(token, public_key)
    except (JWTError, JOSEError) as e:
        logger.warning("[licenca] Falha na validação JWT offline: %s", e)
        raise _erro_licenca(
            "REQUISITA_CONEXAO_INTERNET",
            "Token de licença inválido ou expirado. Conecte-se à internet para revalidar.",
        )

    # 2. O token e desta licenca e desta maquina? (D-15)
    _conferir_identidade(claims, licenca, hwid if hwid is not None else obter_hwid())

    # 3. Relogio: se ele voltou no tempo, as contas usam o maior horario ja
    #    visto, e a resposta leva o aviso (D-05). Nunca bloqueia por isso.
    agora, relogio_recuou = relogio.verificar_relogio(licenca, agora_real)

    # 4. Vencimento do plano, pela claim (D-13). Token sem `dataVencimento` e
    #    licenca sem vencimento, como a API define.
    #    A carencia afrouxa ESTE limite e so ele. Os dois seguintes -- validade
    #    offline e proxima validacao obrigatoria -- continuam valendo iguais,
    #    senao a carencia viraria uma porta para rodar desconectado.
    data_vencimento = _data_da_claim(claims.get("dataVencimento"))
    em_carencia = _carencia_do_token(claims, agora)
    if data_vencimento is not None and agora >= data_vencimento and not em_carencia:
        raise _erro_licenca(
            "LICENCA_EXPIRADA",
            "Sua licença expirou. Entre em contato com o suporte para renovação.",
        )

    # 5. Validade offline (dias desde a ultima sincronizacao). O prazo vem da
    #    claim `gracePeriodDias`; a coluna so vale para token antigo sem ela.
    grace_period = claims.get("gracePeriodDias")
    if grace_period is None:
        grace_period = licenca.grace_period
    ultima_sinc = licenca.ultima_sinc
    if ultima_sinc.tzinfo is None:
        ultima_sinc = ultima_sinc.replace(tzinfo=timezone.utc)

    dias_offline = (agora - ultima_sinc).days
    if dias_offline > grace_period:
        raise _erro_licenca(
            "REQUISITA_CONEXAO_INTERNET",
            f"Limite de {grace_period} dias offline excedido ({dias_offline} dias). "
            "Conecte-se à internet para revalidar a licença.",
        )

    # 6. Proxima validacao obrigatoria: claim `proximaValidacaoEm` (coluna so
    #    para token antigo sem ela).
    proxima_validacao = _data_da_claim(claims.get("proximaValidacaoEm")) or licenca.proxima_validacao
    if proxima_validacao.tzinfo is None:
        proxima_validacao = proxima_validacao.replace(tzinfo=timezone.utc)

    if agora >= proxima_validacao:
        raise _erro_licenca(
            "REQUISITA_CONEXAO_INTERNET",
            "Data de validação obrigatória atingida. Conecte-se à internet para revalidar.",
        )

    # 7. Dias restantes: o MENOR dos tres prazos. Em carencia o vencimento ja
    #    passou, e quem conta e o prazo da carencia. Sem internet o numero e
    #    calculado aqui, entao a resposta o marca como ESTIMATIVA (F26).
    if em_carencia:
        dias_ate_vencimento = (_data_da_claim(claims.get("dataLimiteCarencia")) - agora).days
    elif data_vencimento is not None:
        dias_ate_vencimento = (data_vencimento - agora).days
    else:
        dias_ate_vencimento = None   # sem vencimento: so os prazos offline contam

    dias_ate_grace = grace_period - dias_offline
    dias_ate_validacao = (proxima_validacao - agora).days
    prazos = [d for d in (dias_ate_vencimento, dias_ate_grace, dias_ate_validacao) if d is not None]
    dias_restantes = min(prazos)

    logger.info(
        "[licenca] Validação offline aceita. Dias restantes (estimados): %d", dias_restantes
    )
    resultado = {
        "status": "offline_valid",
        "dias_restantes": dias_restantes,
        "em_carencia": em_carencia,
        "dias_restantes_carencia": dias_ate_vencimento if em_carencia else None,
        "estimativa": True,
    }
    if relogio_recuou:
        resultado["aviso"] = "relogio_recuou"
    return resultado


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

    # 2b. Guarda o maior horário já visto (LIC-02 §6.5). Só anda para frente:
    #     se o relógio recuou, o valor guardado fica e a validação offline
    #     percebe. O commit vem junto com o da validação (online ou offline).
    relogio.registrar_horario(licenca, datetime.now(timezone.utc))

    # 3. Abrir a chave de ativação: só abre na máquina que a ativou (cofre do
    #    Windows no formato novo, HWID no antigo). Banco copiado de outro
    #    computador -> LICENCA_DE_OUTRA_MAQUINA (tela de transferência).
    chave_ativacao = segredos_licenca.abrir_chave_ou_erro(licenca, hwid)

    # 4. Tentar validação online (prioridade). Erros 4xx da API (HTTPException)
    #    sobem direto; só a falta de rede cai no caminho offline.
    resultado = None
    try:
        resultado = _tentar_conexao_remota(db, licenca, chave_ativacao, hwid)
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        logger.info("[licenca] Nuvem inacessível (%s), iniciando fallback offline.", e)

    if resultado is not None:
        # O token acabou de ser trocado pelo que o servidor mandou: os módulos
        # saem DELE, na hora, e NUNCA com uma chave pública ilegível (D-14).
        chave_publica = _chave_publica_com_resgate(db, licenca, hwid)
        resultado["modulos"] = ler_modulos_liberados(_token_para_ler_modulos(licenca), chave_publica)
        return resultado

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
    resultado = _validar_offline(licenca, public_key, hwid)
    resultado["modulos"] = ler_modulos_liberados(_token_para_ler_modulos(licenca), public_key)
    # Grava o maior horário visto (passo 2b): no caminho online quem grava é
    # o commit de _tentar_conexao_remota.
    licenca_crud.update_licenca(db, licenca)
    db.commit()
    return resultado


def _chave_publica_com_resgate(db: Session, licenca: ConfiguracaoLicenca, hwid: str) -> str:
    """Chave pública para ler os módulos no caminho COM internet (LIC-02 §6.3, D-14).

    Se a guardada não abrir, busca de novo na API (a mesma função do caminho
    offline, que grava a chave boa no banco). Se nem assim, CHAVE_CORROMPIDA:
    ler os módulos com uma chave ilegível daria "não sei" e liberaria tudo.
    """
    chave_publica = _decifrar_public_key(licenca, hwid)   # None se a coluna não abrir
    if chave_publica:
        return chave_publica
    try:
        return resgatar_chave_publica_online(db, hwid, licenca.licenca_id)
    except Exception:  # noqa: BLE001 - rede ou resposta ruim: o resultado é o mesmo
        raise _erro_licenca(
            "CHAVE_CORROMPIDA",
            "Chave de segurança corrompida. Necessária ligação à internet para recuperação.",
        )
