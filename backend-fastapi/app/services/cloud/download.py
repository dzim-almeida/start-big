import asyncio
import logging
import os
from typing import Optional

import httpx
from cryptography.exceptions import InvalidTag
from fastapi import HTTPException, status

from app.schemas.backup.operacoes import CloudPlanResponse, DownloadChainResponse

from ._constants import API_BACKUP_DOWNLOAD, GET_TIMEOUT
from ._http import _client, _request, _safe_json
from .cifra_backup import decifrar_da_nuvem, esta_cifrado
from .flow import CloudSyncError

logger = logging.getLogger(__name__)


async def get_cloud_plan(db, cycle: str) -> CloudPlanResponse:
    # Import local — evita ciclo: download → core.hwid → (chain)
    from app.core.hwid import obter_hwid

    payload = {"hwid": obter_hwid()}
    if cycle:
        payload["ciclo"] = cycle

    response = await _request(db, "POST", API_BACKUP_DOWNLOAD, payload=payload)

    if response.status_code == 404:
        body = _safe_json(response)
        if body.get("codigo") == "BACKUP_INEXISTENTE" and not cycle:
            # §5b: nada NESTE ciclo, mas pode haver em ciclo anterior.
            return CloudPlanResponse(
                status="needs_explicit_cycle",
                code="BACKUP_INEXISTENTE",
                details="Ciclo corrente vazio; reconsultar com ciclo explícito.",
            )
        raise CloudSyncError(
            f"url-download 404: {body.get('codigo')}",
            code=body.get("codigo"), http_status=404,
        )
    if response.status_code >= 400:
        body = _safe_json(response)
        raise CloudSyncError(
            f"url-download falhou ({response.status_code}): {body.get('codigo')}",
            code=body.get("codigo"), http_status=response.status_code,
        )

    return CloudPlanResponse(status="ok", plan=response.json())


async def download_chain(db, cycle: Optional[str] = None) -> DownloadChainResponse:
    # Import local — evita ciclo: download ↔ backup
    from app.services import backup as backup_service

    planned = await get_cloud_plan(db, cycle)

    if planned.status == "needs_explicit_cycle":
        return DownloadChainResponse(status="needs_explicit_cycle", details=planned.details)

    plan = planned.plan
    files = plan.get("arquivos", [])
    resolved_cycle = plan.get("ciclo") or cycle

    if not files:
        return DownloadChainResponse(
            status="no_files",
            details="Nenhum backup disponível na nuvem para este ciclo.",
            ciclo=resolved_cycle,
        )

    # Primeiro baixa e decifra TODOS os arquivos da cadeia; só depois salva.
    # Assim, se um deles não abrir com a chave desta licença, nada é salvo
    # (LIC-01, CA-06), nem os que vieram antes dele.
    baixados: list[tuple[str, bytes]] = []
    chave_licenca: Optional[str] = None   # aberta do cofre só se algum arquivo for cifrado

    async with _client(GET_TIMEOUT) as client:
        for fileinfo in files:
            url = fileinfo.get("url")
            chave = fileinfo.get("chave", "")
            filename = os.path.basename(chave) or fileinfo.get("arquivo", "")

            try:
                download_response = await client.get(url)
            except httpx.RequestError as e:
                raise CloudSyncError(f"Falha de rede no GET para {url}: {e}") from e

            if download_response.status_code != 200:
                raise CloudSyncError(
                    f"Download de {filename} falhou ({download_response.status_code}).",
                    http_status=download_response.status_code,
                )

            conteudo = download_response.content
            if esta_cifrado(conteudo[:5]):
                if chave_licenca is None:
                    chave_licenca = _chave_desta_licenca(db)
                conteudo = await asyncio.to_thread(_decifrar_ou_422, conteudo, chave_licenca, filename)
            # Sem a marca SBKC1 é um backup antigo (ZIP comum, começa com "PK"):
            # segue como sempre seguiu.
            baixados.append((filename, conteudo))

    ordered_files: list[str] = []
    for filename, conteudo in baixados:
        await asyncio.to_thread(backup_service.save_backup, cycle, filename, conteudo)
        ordered_files.append(filename)

    await asyncio.to_thread(backup_service.restore_from_chain, cycle, ordered_files)
    return DownloadChainResponse(
        status="success",
        ciclo=resolved_cycle,
        ordered_files=ordered_files,
        restaura_ate=plan.get("restauraAte"),
        cadeia_completa=plan.get("cadeiaCompleta", False),
        indisponiveis=plan.get("indisponiveis", []),
        total_bytes=plan.get("totalBytes"),
    )


def _chave_desta_licenca(db) -> str:
    """Chave de ativação aberta do cofre, ou o erro de licença certo."""
    # Imports locais evitam importação circular entre cloud e licenca
    from app.core.hwid import obter_hwid
    from app.db.crud.configuracao import licenca as licenca_crud
    from app.services.licenca import segredos_licenca

    licenca = licenca_crud.get_licenca(db)
    if not licenca:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"codigo": "LICENCA_NAO_ENCONTRADA",
                    "mensagem": "Nenhuma licença ativada neste computador."},
        )
    # Levanta LICENCA_DE_OUTRA_MAQUINA ou COFRE_INDISPONIVEL quando não abre.
    return segredos_licenca.abrir_chave_ou_erro(licenca, obter_hwid())


def _decifrar_ou_422(conteudo: bytes, chave: str, filename: str) -> bytes:
    """Decifra um arquivo da nuvem; se a chave não confere, 422 BACKUP_CHAVE_INVALIDA."""
    try:
        return decifrar_da_nuvem(conteudo, chave)
    except InvalidTag as e:
        # InvalidTag = a "assinatura" da cifra não bateu: outra licença, ou o
        # arquivo foi alterado. Em nenhum dos dois casos dá para restaurar.
        logger.warning("[SYNC] Backup %s não abre com a chave desta licença.", filename)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"codigo": "BACKUP_CHAVE_INVALIDA",
                    "mensagem": "O backup da nuvem não abre com a chave desta licença."},
        ) from e
