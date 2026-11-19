import asyncio
import logging
import os
import tempfile

from app.schemas.backup.operacoes import BackupInfo, SyncResponse

from ._constants import API_BACKUP_STATUS_URL
from ._http import _request, _safe_json
from . import journal
from .cifra_backup import cifrar_para_nuvem
from .flow import CloudSyncError, flow
from .upload import confirm_upload, get_url_upload, send_zip_to_cloud

logger = logging.getLogger(__name__)


async def sync(db) -> SyncResponse:
    # Imports locais evitam importações circulares entre services e core
    from app.core.hwid import obter_hwid
    from app.services import backup as backup_service

    # 1. STATUS + DECISÃO
    response = await _request(db, "GET", API_BACKUP_STATUS_URL)
    if response.status_code >= 400:
        body = _safe_json(response)
        raise CloudSyncError(
            f"get status falhou ({response.status_code}): {body.get('codigo')}",
            code=body.get("codigo"), http_status=response.status_code,
        )
    status = response.json()

    last_backup = await asyncio.to_thread(backup_service.get_last_backup)
    manifest = None
    if last_backup:
        manifest = await asyncio.to_thread(backup_service.load_manifest, last_backup.arquivo)

    decision = flow(status, manifest, last_backup)

    # Ações de PARADA (tudo que não é "upload"): encerra o ciclo.
    if decision.action in ("blocked", "in_progress", "up_to_date", "no_local_backup"):
        logger.info("[SYNC] Ciclo encerrado sem envio: %s", decision)
        return SyncResponse(status=decision.action, details=str(decision.action))

    # 2. RECONCILIAÇÃO: gerar full local se o servidor exige
    if decision.force_full_local:
        logger.info("[SYNC] Servidor exige full; gerando full local forçado.")
        new = await asyncio.to_thread(backup_service.create_backup, True)
        last_backup = BackupInfo(
            arquivo=new.arquivo, criado_em=new.criado_em,
            tamanho_bytes=new.tamanho_bytes, completo=True,
        )
        manifest = await asyncio.to_thread(backup_service.load_manifest, last_backup.arquivo)

    file = last_backup.arquivo
    zip_path = os.path.join(backup_service.LOCAL_BACKUP, file)
    content_code = journal.code_content(manifest)  # do MANIFEST, nunca do zip
    hwid = obter_hwid()

    # 2b. CÓPIA CIFRADA (LIC-01 §6.7): o que sai do computador é o ZIP cifrado
    #     com a chave de ativação. O backup local não muda. A cópia é montada
    #     ANTES do pedido de URL, porque o tamanhoBytes enviado à API é o dela.
    try:
        chave = _chave_para_cifrar(db, hwid)
    except _ChaveIndisponivel as e:
        # Sem a chave não há como cifrar, e em claro o backup não sai mais.
        logger.warning("[SYNC] Envio adiado: %s", e)
        return SyncResponse(status="error", details=str(e), code=e.codigo)
    # Ler e cifrar o ZIP é trabalho pesado de disco: roda numa thread para
    # não travar o resto do backend enquanto isso.
    cifrado_path = await asyncio.to_thread(_gravar_copia_cifrada, zip_path, chave)

    try:
        return await _enviar(db, decision, file, cifrado_path, content_code, hwid)
    finally:
        # A cópia cifrada é temporária: apagada sempre, deu certo ou não.
        try:
            os.remove(cifrado_path)
        except OSError:
            logger.warning("[SYNC] Não foi possível apagar a cópia temporária %s", cifrado_path)


class _ChaveIndisponivel(Exception):
    """A chave de ativação não abriu: o backup não pode ser cifrado."""

    def __init__(self, mensagem: str, codigo: str):
        super().__init__(mensagem)
        self.codigo = codigo


def _chave_para_cifrar(db, hwid: str) -> str:
    """Chave de ativação aberta do cofre, ou _ChaveIndisponivel com o motivo."""
    # Imports locais evitam importação circular entre cloud e licenca
    from app.db.crud.configuracao import licenca as licenca_crud
    from app.services.licenca import cofre, segredos_licenca

    licenca = licenca_crud.get_licenca(db)
    if not licenca:
        raise _ChaveIndisponivel("Nenhuma licença neste computador.", "LICENCA_NAO_ENCONTRADA")
    try:
        chave = segredos_licenca.ler_chave_ativacao(licenca.chave_ativacao, hwid)
    except cofre.CofreIndisponivel as e:
        raise _ChaveIndisponivel("O cofre do Windows recusou abrir a chave.", "COFRE_INDISPONIVEL") from e
    except Exception as e:  # noqa: BLE001 - chave de outro computador
        raise _ChaveIndisponivel(
            "A chave de ativação não abre neste computador.", "LICENCA_DE_OUTRA_MAQUINA"
        ) from e
    return chave


def _gravar_copia_cifrada(zip_path: str, chave: str) -> str:
    """Cifra o ZIP local num arquivo temporário e devolve o caminho dele.

    O arquivo temporário fica na pasta temporária do sistema, e não na pasta de
    backups, para a limpeza e o incremental nunca o confundirem com um backup.
    """
    with open(zip_path, "rb") as f:
        cifrado = cifrar_para_nuvem(f.read(), chave)
    # mkstemp cria o arquivo e devolve (descritor, caminho); usamos o descritor
    # para escrever e fechamos logo em seguida.
    descritor, caminho = tempfile.mkstemp(prefix="startbig-nuvem-", suffix=".sbkc")
    with os.fdopen(descritor, "wb") as destino:
        destino.write(cifrado)
    return caminho


async def _enviar(db, decision, file: str, zip_path: str, content_code: str, hwid: str) -> SyncResponse:
    """Passos 3 e 4 do ciclo: pede a URL, envia (PUT) e confirma.

    `zip_path` aqui é a CÓPIA CIFRADA; `file` continua sendo o nome do backup
    local, que é a chave do journal.
    """
    size = os.path.getsize(zip_path)   # tamanho da cópia cifrada (o que de fato sobe)

    # 3. URL-UPLOAD
    journal.update_journal_entry(file, status=journal.STATUS_PENDENTE,
                                 ciclo=decision.cycle, codigoConteudo=content_code)
    try:
        authorization = await get_url_upload(db, payload={
            "hwid": hwid,
            "tipo": decision.backup_type,
            "ciclo": decision.cycle,
            "tamanhoBytes": size,
            "codigoConteudo": content_code,
            "origem": "AUTOMATICO",
        })
    except CloudSyncError as e:
        # Recusa de negócio: registra e ENCERRA (sem retry).
        journal.update_journal_entry(file, status=journal.STATUS_FALHOU, codigoErro=e.code)
        return SyncResponse(status="error", details=str(e), code=e.code,
                            http_status=e.http_status)

    action_api = authorization.get("acao")
    if action_api == "PULAR":
        # Servidor já tem este conteúdo. NÃO chamar /confirmar (spec §2).
        journal.update_journal_entry(file, status=journal.STATUS_ENVIADO,
                                     observacao="PULAR: conteudo ja na nuvem")
        return SyncResponse(status="skipped", details="Conteúdo já presente na nuvem.")
    if action_api == "AGUARDANDO_OUTRO_TERMINAL":
        return SyncResponse(status="waiting", details="Outro terminal está enviando.")

    upload_id = authorization.get("uploadId")
    journal.update_journal_entry(file, status=journal.STATUS_ENVIANDO,
                                 uploadId=upload_id, expiraEm=authorization.get("expiraEm"))

    # 4. PUT + CONFIRMAR (sempre, nos dois desfechos)
    try:
        await send_zip_to_cloud(authorization["url"], authorization.get("headers", {}), zip_path)
    except CloudSyncError as e:
        # PUT falhou: confirmar ok:false devolve a cota e solta o lock.
        try:
            await confirm_upload(db, payload={
                "uploadId": upload_id, "hwid": hwid, "ok": False, "erro": str(e)[:500],
            })
        except CloudSyncError:
            logger.exception("[SYNC] confirmar(ok=false) também falhou")
        journal.update_journal_entry(file, status=journal.STATUS_FALHOU,
                                     codigoErro=e.code or "PUT_FALHOU")
        return SyncResponse(status="error", details=str(e), code=e.code,
                            http_status=e.http_status)

    confirm = await confirm_upload(db, payload={
        "uploadId": upload_id, "hwid": hwid, "ok": True, "tamanhoBytes": size,
    })
    if confirm.get("confirmado"):
        journal.update_journal_entry(file, status=journal.STATUS_ENVIADO,
                                     confirmadoEm=confirm.get("confirmado_em")
                                     or confirm.get("confirmadoEm"))
        logger.info("[SYNC] Backup %s enviado e confirmado.", file)
        return SyncResponse(status="success", details="Backup enviado e confirmado.")

    journal.update_journal_entry(file, status=journal.STATUS_FALHOU,
                                 codigoErro="CONFIRMAR_NEGADA")
    return SyncResponse(status="error", details="Confirmação negada.", code="CONFIRMAR_NEGADA")
