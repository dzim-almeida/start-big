# ---------------------------------------------------------------------------
# ARQUIVO: services/licenca/sincronizacao.py
# DESCRICAO: Licenca - heartbeat dos terminais e renovacao do token em segundo plano.
# ---------------------------------------------------------------------------

import asyncio
import json
import logging
from datetime import datetime, timezone
import httpx
from sqlalchemy.orm import Session
from datetime import timedelta
from app.schemas.licenca import (
    ConectarPayload,
    HeartbeatPayload,
    ValidarPayload,
    ValidarResponse,
)
from app.db.models.terminal_conectado import TerminalConectado
from app.db.crud.configuracao import licenca as licenca_crud
from app.db.crud.terminal import conectados as terminal_crud
from app.core.hwid import obter_hwid
from app.services.licenca.constantes import API_CONECTAR_URL, API_HEARTBEAT_URL, API_VALIDAR_URL, HEARTBEAT_TIMEOUT
from app.services.licenca import segredos_licenca  # unico dono do token e da chave (LIC-01)
from app.services.licenca.recusa import _limpar_bloqueio

logger = logging.getLogger(__name__)


# ===========================================================================
# Heartbeat (Etapa 3 — Sincronização de Estado)
# ===========================================================================

async def _enviar_heartbeat_terminal(
    client: httpx.AsyncClient,
    licenca_id: str,
    terminal: "TerminalConectado",
    headers: dict | None = None,
) -> tuple["TerminalConectado", int | None]:
    """
    Envia heartbeat para um terminal específico.

    `headers` leva o token da licença (`Authorization: Bearer ...`, LIC-02 §6.8):
    é ele que prova à API que o pedido vem do servidor da loja (D-37).

    Returns:
        Tupla (terminal, status_code). status_code é None em caso de erro de rede.
    """
    payload = HeartbeatPayload(licencaId=licenca_id, hwid=terminal.hwid)
    try:
        response = await client.post(
            API_HEARTBEAT_URL,
            json=payload.model_dump(),
            headers=headers or {},
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

    # O token da licença vai no cabeçalho (D-37). Se ele não abrir, o
    # heartbeat segue sem o cabeçalho, como antes: a API, na transição,
    # ainda renova sessão existente sem token (ADR-004).
    headers = _cabecalho_com_token(licenca)

    # Enviar heartbeats em paralelo
    async with httpx.AsyncClient(timeout=HEARTBEAT_TIMEOUT) as client:
        resultados = await asyncio.gather(
            *[
                _enviar_heartbeat_terminal(client, licenca.licenca_id, terminal, headers)
                for terminal in terminais
            ],
            return_exceptions=True,
        )

    # Caixas cuja sessão a API não conhece (404 SESSAO_INEXISTENTE).
    para_reconectar: list[str] = []

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

        elif status_code == 404 and _codigo_da_resposta(response_text) == "SESSAO_INEXISTENTE":
            # A API (LIC-09) não tem sessão para este caixa: reconecta com a
            # chave de ativação. NÃO remove o caixa nem conta como bloqueio.
            para_reconectar.append(terminal.hwid)
            todos_bloqueados = False

        elif status_code in (401, 403):
            # 401 LICENCA_HWID_REVOGADO: a validação da licença trata a revogação.
            # 403 HEARTBEAT_LICENCA_DIVERGENTE: não deveria acontecer (o token é
            # da própria licença). Nos dois casos: só o log.
            logger.warning(
                "[licenca] Heartbeat %s...: %d %s",
                terminal.hwid[:8], status_code, _codigo_da_resposta(response_text) or "",
            )
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

    if para_reconectar:
        await _reconectar_caixas(licenca, para_reconectar)

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


def _cabecalho_com_token(licenca) -> dict:
    """Cabeçalho `Authorization: Bearer <token>` do heartbeat, ou {} sem token legível."""
    try:
        token = segredos_licenca.ler_token(licenca.token)   # LIC-01: abre o token do cofre
    except Exception as e:  # noqa: BLE001 - cofre fora do ar ou banco de outra máquina
        logger.warning("[licenca] Heartbeat sem token: o token não abre (%s).", type(e).__name__)
        return {}
    return {"Authorization": f"Bearer {token}"} if token else {}


def _codigo_da_resposta(texto: str | None) -> str | None:
    """`codigo` do corpo JSON da resposta (texto), ou None se não houver."""
    try:
        corpo = json.loads(texto or "")
    except ValueError:
        return None
    return corpo.get("codigo") if isinstance(corpo, dict) else None


async def _reconectar_caixas(licenca, hwids: list[str]) -> None:
    """Abre de novo, na API, a sessão dos caixas que ela não conhece (LIC-02 §6.8).

    Faz o mesmo POST /licenca/conectar do login do caixa (`conectar_terminal`),
    com a chave de ativação. O `conectar_terminal` em si não serve aqui: ele é
    idempotente e não chama a API para um caixa que já está na tabela local.
    Falhas só vão para o log: o próximo heartbeat tenta de novo.
    """
    try:
        chave = segredos_licenca.ler_chave_ativacao(licenca.chave_ativacao, obter_hwid())
    except Exception as e:  # noqa: BLE001 - cofre fora do ar ou banco de outra máquina
        logger.warning("[licenca] Reconexão adiada: a chave de ativação não abre (%s).", type(e).__name__)
        return

    async with httpx.AsyncClient(timeout=HEARTBEAT_TIMEOUT) as client:
        for hwid in hwids:
            try:
                resposta = await client.post(
                    API_CONECTAR_URL,
                    json=ConectarPayload(chave=chave, hwid=hwid).model_dump(),
                )
                logger.info("[licenca] Caixa %s... reconectado (status %d).", hwid[:8], resposta.status_code)
            except httpx.RequestError as e:
                logger.warning("[licenca] Reconexão do caixa %s... falhou: %s", hwid[:8], e)


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
    try:
        chave_ativacao = segredos_licenca.ler_chave_ativacao(licenca.chave_ativacao, hwid)
    except Exception as e:  # noqa: BLE001 - cofre fora do ar ou banco de outra maquina
        # Roda em segundo plano: nao ha tela para mostrar o erro. O boot e o
        # login mostram o motivo certo; aqui so registramos e tentamos depois.
        logger.warning("[licenca] Renovacao adiada: chave de ativacao nao abre (%s).", type(e).__name__)
        return
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
            # Token novo trancado no cofre; se o cofre falhar, fica o anterior.
            segredos_licenca.gravar_token_na_licenca(licenca, resposta.token)
            licenca.proxima_validacao = resposta.proximaValidacaoEm
            licenca.ultima_sinc = resposta.ultimaSincronizacao
            licenca.data_vencimento = resposta.dataVencimento
            licenca.grace_period = resposta.gracePeriodDias
            # Carência também aqui (F25), como no caminho online. As colunas
            # são só informação de tela: a decisão offline vem do token (D-13).
            licenca.em_carencia = resposta.emCarencia
            licenca.data_limite_carencia = resposta.dataLimiteCarencia
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
