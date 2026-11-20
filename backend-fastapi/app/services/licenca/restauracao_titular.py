# ---------------------------------------------------------------------------
# ARQUIVO: services/licenca/restauracao_titular.py
# DESCRICAO: O dono que acabou de entrar com a conta (re-login) recupera o
#            banco pelo backup da nuvem (LIC-03 §4.1, §6.1, D-07, D-36).
#
# O CASO: o dono perdeu o banco (HD queimou, Windows reinstalado), instalou o
# app e entrou com a conta. A licença voltou, mas o banco está vazio. Em vez de
# cair num setup vazio, ele restaura o último backup da nuvem.
#
# QUEM AUTORIZA: a senha da conta StartBig, pedida de novo e conferida na nuvem,
# e a regra de que a conta é dona da licença gravada aqui. Não há login local
# nesse momento (o banco está vazio), por isso a rota é pública, como /transferir.
# ---------------------------------------------------------------------------

import asyncio
import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.hwid import obter_hwid
from app.db.crud.configuracao import licenca as licenca_crud
from app.schemas.licenca.restauracao import (
    BackupEncontrado,
    RestaurarBackupPayload,
    RestaurarBackupResposta,
)
from app.services.backup import restore
from app.services.cloud._constants import API_BACKUP_STATUS_URL
from app.services.cloud.download import download_chain
from app.services.cloud.flow import CloudSyncError
from app.services.licenca import titular_nuvem
from app.services.licenca.transferencia import _entrar_na_conta, _erro

logger = logging.getLogger(__name__)

# Erros desta rota (LIC-03 §4.1). Ficam aqui para os textos não se repetirem.
_SEM_BACKUP = (status.HTTP_404_NOT_FOUND, "BACKUP_INEXISTENTE",
               "Não há backup na nuvem para esta licença.")
_JA_PENDENTE = (status.HTTP_409_CONFLICT, "RESTAURACAO_JA_PENDENTE",
                "Uma restauração já está pendente. Reinicie o sistema para aplicá-la.")


# ===========================================================================
# Qual ciclo restaurar (D-36)
# ===========================================================================

def _fulls_confirmados(status_nuvem: dict) -> list[dict]:
    """Os envios FULL confirmados do histórico do /erp/backup/status.

    A comparação ignora maiúsculas ("FULL" ou "full", "CONFIRMADO" ou
    "confirmado"), porque o formato exato do histórico não foi conferido contra
    a API nesta sessão (registrado na nota de revisão da spec).
    """
    return [
        evento
        for evento in status_nuvem.get("historicoEventos") or []   # os 30 envios mais recentes
        if str(evento.get("tipo", "")).upper() == "FULL"
        and str(evento.get("status", "")).upper() == "CONFIRMADO"
        and evento.get("ciclo")
    ]


def ciclo_mais_recente_com_full(status_nuvem: dict) -> str | None:
    """O ciclo mais recente que tem um FULL confirmado; None se não houver nenhum.

    Sem ciclo, a API usaria a SEMANA ATUAL, que pode estar vazia (segunda de
    manhã, ou um trial com um backup antigo). O registro local de ciclos some
    junto com o banco, então a fonte é o /status da nuvem.
    """
    ciclos = [evento["ciclo"] for evento in _fulls_confirmados(status_nuvem)]
    return max(ciclos) if ciclos else None   # o ciclo é uma data ISO: o maior é o mais recente


def _quando(evento: dict) -> str | None:
    """Data e hora de um envio. O nome do campo varia; tentamos os prováveis."""
    for campo in ("confirmadoEm", "criadoEm", "dataHora", "data"):
        if evento.get(campo):
            return str(evento[campo])
    return None


def resumo_do_backup(status_nuvem: dict) -> BackupEncontrado | None:
    """'Semana de ... · último envio em ...' para a tela do re-login (§6.2). None = sem backup."""
    ciclo = ciclo_mais_recente_com_full(status_nuvem)
    if ciclo is None:
        return None
    # Último envio confirmado DESSE ciclo (o full ou um fragmento depois dele)
    datas = [
        _quando(evento)
        for evento in status_nuvem.get("historicoEventos") or []
        if evento.get("ciclo") == ciclo and str(evento.get("status", "")).upper() == "CONFIRMADO"
    ]
    datas = [data for data in datas if data]
    return BackupEncontrado(ciclo=ciclo, ultimo_envio=max(datas) if datas else None)


# ===========================================================================
# Conversa com a nuvem
# ===========================================================================

def consultar_status_backup(db: Session) -> dict:
    """GET /erp/backup/status com o token da licença. Erros saem com o código certo."""
    resposta = titular_nuvem.pedir_a_nuvem(db, "GET", API_BACKUP_STATUS_URL)
    if resposta.status_code >= 400:
        raise titular_nuvem.erro_da_resposta(resposta)
    try:
        corpo = resposta.json()
    except ValueError as e:   # a nuvem respondeu algo que não é JSON (proxy, manutenção)
        raise _erro(status.HTTP_502_BAD_GATEWAY, "RESPOSTA_INVALIDA",
                    "A StartBig respondeu de um jeito inesperado. Tente de novo em instantes.") from e
    return corpo if isinstance(corpo, dict) else {}


def conferir_titular_da_licenca(db: Session, email: str, senha: str) -> None:
    """A senha confere na nuvem E a conta é dona da licença gravada aqui?"""
    # 1. Confere a senha na nuvem. Os erros saem com os mesmos códigos de
    #    transferencia.py (CREDENCIAIS_INVALIDAS, SEM_CONEXAO, NUVEM_INDISPONIVEL...).
    #    Um segundo login do mesmo computador é reconexão na nuvem: não conta
    #    como troca nem derruba caixa (conferido no plataformaADM).
    resposta = _entrar_na_conta(email, senha, obter_hwid())
    # 2. A conta tem que ser dona da licença que está gravada aqui. Sem esta
    #    regra, qualquer conta poderia trocar o banco desta loja pelo dela.
    local = licenca_crud.get_licenca(db)
    if local is None or local.licenca_id != resposta.licencaId:
        raise _erro(status.HTTP_403_FORBIDDEN, "LICENCA_DE_OUTRA_CONTA",
                    "Esta conta não é dona da licença deste computador.")


def _erro_do_download(e: CloudSyncError) -> HTTPException:
    """Traduz a falha do download da nuvem para os códigos da §4.1."""
    if e.http_status is None:
        return _erro(status.HTTP_503_SERVICE_UNAVAILABLE, "SEM_CONEXAO",
                     "Sem conexão com a StartBig. Verifique a internet.")
    if e.http_status == 404:
        return _erro(*_SEM_BACKUP)
    if e.http_status >= 500:
        return _erro(status.HTTP_503_SERVICE_UNAVAILABLE, "NUVEM_INDISPONIVEL",
                     "O servidor da StartBig não respondeu. Tente de novo em alguns minutos.")
    # 4xx com código da nuvem (ex.: BACKUP_MAQUINA_REVOGADA): repassa o código
    return _erro(e.http_status, e.code or "NUVEM_INDISPONIVEL",
                 "A StartBig recusou o download do backup.")


# ===========================================================================
# A restauração
# ===========================================================================

async def restaurar_backup_do_titular(db: Session, pedido: RestaurarBackupPayload) -> RestaurarBackupResposta:
    """Prepara a restauração do backup da nuvem para o próximo boot (§4.1).

    Ordem: conferir quem pede → ver se já há restauração pendente → descobrir o
    ciclo → baixar → preparar. Qualquer falha para antes de preparar, e o banco
    atual não muda.
    """
    # As funções de conta e de status usam chamadas síncronas (httpx.Client).
    # `asyncio.to_thread` as roda numa thread separada, para não travar o
    # servidor enquanto esperamos a nuvem.
    await asyncio.to_thread(conferir_titular_da_licenca, db, pedido.email, pedido.senha)

    # Só uma restauração por vez: a segunda apagaria o marcador da primeira.
    if restore.restauracao_pendente():
        raise _erro(*_JA_PENDENTE)

    ciclo = pedido.ciclo
    if ciclo is None:
        status_nuvem = await asyncio.to_thread(consultar_status_backup, db)
        ciclo = ciclo_mais_recente_com_full(status_nuvem)
        if ciclo is None:
            raise _erro(*_SEM_BACKUP)

    # Baixa a cadeia do ciclo e decifra (LIC-01). Chave errada → 422 BACKUP_CHAVE_INVALIDA,
    # que sobe como está (HTTPException).
    try:
        baixado = await download_chain(db, ciclo)
    except CloudSyncError as e:
        logger.warning("[licenca] Restauração do titular: download falhou (%s).", e)
        raise _erro_do_download(e) from e
    if baixado.status != "success":
        raise _erro(*_SEM_BACKUP)   # "no_files" ou "needs_explicit_cycle": nada para restaurar

    try:
        await asyncio.to_thread(restore.preparar_restauracao_do_titular, ciclo)
    except restore.BackupError as e:
        # Corrida rara: outro pedido gravou o marcador enquanto este baixava.
        if restore.restauracao_pendente():
            raise _erro(*_JA_PENDENTE) from e
        raise

    logger.info("[licenca] Restauração do titular preparada (ciclo %s).", ciclo)
    return RestaurarBackupResposta(
        status="pendente_reinicio",
        ciclo=ciclo,
        mensagem="Restauração preparada. Reinicie o sistema para aplicá-la.",
    )


# ===========================================================================
# O que a tela mostra logo depois do re-login (§6.2, §6.6)
# ===========================================================================

def dados_depois_do_relogin(db: Session) -> dict:
    """Backup na nuvem e dados do titular, para a tela "Sua licença foi encontrada".

    Vai na resposta do /auth/reconnect quando o banco ainda não tem empresa
    (decisão do usuário): só quem acabou de provar a senha recebe o documento
    e o endereço do titular.

    Uma falha aqui NUNCA derruba o re-login, que já deu certo: o campo volta
    `None`. Sem `backup`, a tela oferece o setup; sem `titular`, o setup abre
    vazio, como sempre abriu. O motivo fica no log.
    """
    backup = None
    try:
        backup = resumo_do_backup(consultar_status_backup(db))
    except HTTPException as e:
        logger.warning("[licenca] Re-login: situação do backup indisponível (%s).", e.detail)

    titular = None
    try:
        titular = titular_nuvem.buscar_titular(db)
    except HTTPException as e:
        logger.warning("[licenca] Re-login: dados do titular indisponíveis (%s).", e.detail)

    return {
        "backup": backup.model_dump() if backup else None,
        "titular": titular.model_dump() if titular else None,
    }
