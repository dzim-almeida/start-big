# ---------------------------------------------------------------------------
# ARQUIVO: services/licenca/sincronizacao.py
# DESCRICAO: Licenca - heartbeat dos terminais e renovacao do token em segundo plano.
# ---------------------------------------------------------------------------

import asyncio
import logging
from datetime import datetime, timezone
import httpx
from sqlalchemy.orm import Session
from datetime import timedelta
from app.schemas.licenca import (
    HeartbeatPayload,
    ValidarPayload,
    ValidarResponse,
)
from app.db.models.terminal_conectado import TerminalConectado
from app.db.crud.configuracao import licenca as licenca_crud
from app.db.crud.terminal import conectados as terminal_crud
from app.core.hwid import obter_hwid
from app.services.licenca.constantes import API_HEARTBEAT_URL, API_VALIDAR_URL, HEARTBEAT_TIMEOUT
from app.services.licenca.cripto import decriptar_valor
from app.services.licenca.recusa import _limpar_bloqueio

logger = logging.getLogger(__name__)


# ===========================================================================
# Heartbeat (Etapa 3 — Sincronização de Estado)
# ===========================================================================

async def _enviar_heartbeat_terminal(
    client: httpx.AsyncClient,
    licenca_id: str,
    terminal: "TerminalConectado",
) -> tuple["TerminalConectado", int | None]:
    """
    Envia heartbeat para um terminal específico.

    Returns:
        Tupla (terminal, status_code). status_code é None em caso de erro de rede.
    """
    payload = HeartbeatPayload(licencaId=licenca_id, hwid=terminal.hwid)
    try:
        response = await client.post(
            API_HEARTBEAT_URL,
            json=payload.model_dump(),
        )
        return terminal, response.status_code, response.text
    except httpx.RequestError as error:
        print(f"[licenca] Heartbeat falhou para {terminal.hwid[:8]}... — {type(error).__name__}: {error}")
        return terminal, None, None


async def enviar_heartbeat(db: Session) -> None:
    """
    Envia heartbeat para CADA terminal conectado em paralelo.

    Se não há terminais registrados, não envia nada (sem heartbeat).
    Reage à resposta da API por terminal:
    - 201: OK, atualiza ultima_sinc do terminal.
    - 400: Terminal bloqueado, remove da tabela.
    - Erro de rede: Registra em log e ignora.

    Ao final, se todos os terminais foram bloqueados, marca a licença
    como bloqueada. Se pelo menos um está OK, desbloqueia.
    """
    licenca = licenca_crud.get_licenca(db)
    if not licenca:
        return

    terminais = terminal_crud.get_todos_terminais(db)
    if not terminais:
        print("[licenca] Nenhum terminal conectado — heartbeat ignorado.")
        return

    # Enviar heartbeats em paralelo
    async with httpx.AsyncClient(timeout=HEARTBEAT_TIMEOUT) as client:
        resultados = await asyncio.gather(
            *[
                _enviar_heartbeat_terminal(client, licenca.licenca_id, terminal)
                for terminal in terminais
            ],
            return_exceptions=True,
        )

    tem_ok = False
    todos_bloqueados = True

    for resultado in resultados:
        if isinstance(resultado, Exception):
            logger.warning("[licenca] Heartbeat erro inesperado: %s", resultado)
            todos_bloqueados = False
            continue

        terminal, status_code, response_text = resultado

        if status_code == 201:
            terminal_crud.update_ultima_sinc(db, terminal)
            print(f"[licenca] Heartbeat OK para terminal {terminal.hwid[:8]}...")
            tem_ok = True
            todos_bloqueados = False

        elif status_code == 400:
            terminal_crud.delete_terminal_by_hwid(db, terminal.hwid)
            print(f"[terminal] Terminal {terminal.hwid[:8]}... bloqueado (400), REMOVIDO pelo heartbeat. Body: {response_text}")

        elif status_code is not None:
            print(f"[licenca] Heartbeat {terminal.hwid[:8]}...: status inesperado {status_code}")
            todos_bloqueados = False

        else:
            # Erro de rede — não conta como bloqueio
            todos_bloqueados = False

    # Atualizar flag de bloqueio da licença
    if tem_ok and licenca.bloqueada:
        licenca.bloqueada = False
        licenca_crud.update_licenca(db, licenca)
        print("[licenca] Licença desbloqueada (terminal ativo detectado).")
    elif todos_bloqueados and terminais and not licenca.bloqueada:
        licenca.bloqueada = True
        licenca_crud.update_licenca(db, licenca)
        print("[licenca] Licença BLOQUEADA (todos terminais rejeitados).")

    db.commit()


# ===========================================================================
# Renovação Ativa de Token (Etapa 4)
# ===========================================================================

LIMIAR_RENOVACAO = timedelta(hours=24)


async def renovar_licenca_background(db: Session) -> None:
    """
    Verifica se o token está próximo de expirar e solicita renovação à API central.

    Executa em segundo plano a cada hora. Só faz requisição HTTP se a data atual
    estiver a menos de 24 horas de proximaValidacaoEm ou já a tiver ultrapassado.

    Idempotente: seguro para correr múltiplas vezes. Falhas de rede são ignoradas
    silenciosamente para não interromper o loop.
    """
    licenca = licenca_crud.get_licenca(db)
    if not licenca:
        return

    # Verificar se é necessário renovar
    agora = datetime.now(timezone.utc)
    proxima_validacao = licenca.proxima_validacao
    if proxima_validacao.tzinfo is None:
        proxima_validacao = proxima_validacao.replace(tzinfo=timezone.utc)

    tempo_restante = proxima_validacao - agora
    if tempo_restante > LIMIAR_RENOVACAO:
        return

    # Preparar payload
    hwid = obter_hwid()
    chave_ativacao = decriptar_valor(licenca.chave_ativacao, hwid)
    payload = ValidarPayload(
        chave=chave_ativacao,
        hwid=hwid,
    )

    try:
        async with httpx.AsyncClient(timeout=HEARTBEAT_TIMEOUT) as client:
            response = await client.post(
                API_VALIDAR_URL,
                json=payload.model_dump(),
            )

        if response.status_code == 201:
            dados = response.json()

            if not dados.get("valida", False):
                motivo = dados.get("motivo", "Desconhecido")
                status_licenca = dados.get("status", "DESCONHECIDO")
                logger.warning(
                    "[licenca] Renovação recusada — status=%s, motivo=%s",
                    status_licenca, motivo,
                )
                return

            resposta = ValidarResponse(**dados)

            # Atualizar campos atomicamente
            licenca.token = resposta.token
            licenca.proxima_validacao = resposta.proximaValidacaoEm
            licenca.ultima_sinc = resposta.ultimaSincronizacao
            licenca.data_vencimento = resposta.dataVencimento
            licenca.grace_period = resposta.gracePeriodDias
            _limpar_bloqueio(licenca)

            licenca_crud.update_licenca(db, licenca)
            db.commit()

            logger.info("[licenca] Token renovado com sucesso. Próxima validação: %s", resposta.proximaValidacaoEm)
            return

        logger.warning(
            "[licenca] Renovação: servidor retornou status %d — %s",
            response.status_code, response.text,
        )

    except httpx.RequestError as error:
        logger.warning(
            "[licenca] Renovação falhou — %s: %s",
            type(error).__name__, error,
        )
