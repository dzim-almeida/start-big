# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/fiscal_emissao.py
# DESCRIÇÃO: Centro Fiscal — emissão: prévia e emissão de NF-e/NFC-e, lote, teste,
# consulta, reemissão e devolução.
#
# Saiu do fiscal.py na F5 (07/10/2026), sem mudar comportamento: o
# código foi movido, não reescrito. As URLs não mudaram: `fiscal.py` inclui
# este router sem prefixo, e a trava do módulo NFE vem de lá.
# ---------------------------------------------------------------------------

from fastapi import APIRouter, BackgroundTasks, Body, Depends, Path
from sqlalchemy.orm import Session
from app.core.depends import get_current_active_user, get_db, requer_modulo_fiscal, _handle_db_transaction
from app.schemas.documento_fiscal import DocumentoFiscalRead
from app.schemas.emissao_fiscal import EmissaoBatchResponse, EmissaoDevolucaoRequest, EmissaoNFeBatchRequest, EmissaoNFCeRequest, EmissaoNFeRequest, EmissaoResponse
from app.services import documento_fiscal as documento_fiscal_service
from app.core.modulos import requer_modulo
from app.schemas.emissao_fiscal import EmissaoPreviewResponse

# Sem `dependencies`: a trava do módulo NFE é herdada do router de `fiscal.py`.
router = APIRouter()


# ===========================================================================
# REEMISSÃO (cria nova tentativa — linked list)
# ===========================================================================

@router.post(
    "/documentos/{documento_id}/reemitir",
    response_model=DocumentoFiscalRead,
    summary="Reemitir Documento Fiscal",
    description=(
        "Emite de novo a origem (venda ou OS) de um documento REJEITADO e devolve o "
        "documento novo já com o desfecho da SEFAZ. O original mantém seu status; o "
        "novo aponta para ele por tentativa_anterior_id e recebe número novo."
    ),
)
def reemitir_documento(
    background_tasks: BackgroundTasks,
    user_token: dict = Depends(requer_modulo_fiscal),
    *,
    db: Session = Depends(get_db),
    documento_id: int = Path(..., ge=1, description="ID do documento fiscal"),
):
    from app.services.fiscal.emissao import poll_nfe_status_async
    from app.services.fiscal.reemissao import reemitir_documento as _reemitir

    doc = _handle_db_transaction(db, _reemitir, documento_id, user_token["empresa_id"])

    # Mesmo acompanhamento do /emitir/nfe: a NF-e é assíncrona na SEFAZ.
    if doc.status == "PROCESSANDO":
        background_tasks.add_task(poll_nfe_status_async, doc.id, user_token["empresa_id"])

    return doc


@router.post(
    "/preview/nfe",
    response_model=EmissaoPreviewResponse,
    summary="Pré-visualizar NF-e",
    description="Gera um resumo da NF-e para visualização e verificação antes da emissão.",
)
def preview_nfe(
    user_token: dict = Depends(requer_modulo_fiscal),
    *,
    db: Session = Depends(get_db),
    payload: EmissaoNFeRequest = Body(...),
):
    from app.services.fiscal.emissao import preview_nfe_os, preview_nfe_venda

    empresa_id = user_token["empresa_id"]
    if payload.venda_id:
        return preview_nfe_venda(db, payload.venda_id, empresa_id)
    return preview_nfe_os(db, payload.numero_os, empresa_id)


@router.post(
    "/emitir/nfe",
    response_model=EmissaoResponse,
    summary="Emitir NF-e",
    description="Emite NF-e a partir de uma venda ou OS (apenas itens de produto).",
)
def emitir_nfe(
    background_tasks: BackgroundTasks,
    user_token: dict = Depends(requer_modulo_fiscal),
    *,
    db: Session = Depends(get_db),
    payload: EmissaoNFeRequest = Body(...),
):
    from app.services.fiscal.emissao import (
        emitir_nfe_os, emitir_nfe_venda, poll_nfe_status_async,
    )

    empresa_id = user_token["empresa_id"]

    # A NF-e de uma OS cobre os itens de PRODUTO. A mao de obra e servico e
    # pede NFS-e municipal, que este sistema ainda nao emite.
    if payload.venda_id:
        doc = _handle_db_transaction(
            db, emitir_nfe_venda, payload.venda_id, empresa_id,
        )
    else:
        doc = _handle_db_transaction(
            db, emitir_nfe_os, payload.numero_os, empresa_id,
        )

    if doc.status == "PROCESSANDO":
        background_tasks.add_task(poll_nfe_status_async, doc.id, empresa_id)

    return EmissaoResponse(
        documento_id=doc.id,
        ref_api=doc.ref_api,
        status=doc.status,
        mensagem=doc.mensagem_sefaz or f"NF-e {doc.status.lower()}.",
        ambiente=doc.ambiente_emissao or 2,
    )


@router.post(
    "/preview/nfce",
    # NFC-e exige o modulo NFCE, SEPARADO do NFE: a plataforma tem familia,
    # cota e modulo proprios para o modelo 65 (/erp/fiscal/nfce/...). Uma loja
    # pode ter NF-e e nao ter cupom. Sem esta trava o lojista so descobriria no
    # 403 da plataforma, com a venda ja fechada.
    dependencies=[Depends(requer_modulo("NFCE"))],
    response_model=EmissaoPreviewResponse,
    summary="Pré-visualizar NFC-e",
    description="Gera um resumo da NFC-e para conferência antes da emissão.",
)
def preview_nfce(
    user_token: dict = Depends(requer_modulo_fiscal),
    *,
    db: Session = Depends(get_db),
    payload: EmissaoNFCeRequest = Body(...),
):
    from app.services.fiscal.emissao import preview_nfce_venda

    return preview_nfce_venda(db, payload.venda_id, user_token["empresa_id"])


@router.post(
    "/emitir/nfce",
    # NFC-e exige o modulo NFCE, SEPARADO do NFE: a plataforma tem familia,
    # cota e modulo proprios para o modelo 65 (/erp/fiscal/nfce/...). Uma loja
    # pode ter NF-e e nao ter cupom. Sem esta trava o lojista so descobriria no
    # 403 da plataforma, com a venda ja fechada.
    dependencies=[Depends(requer_modulo("NFCE"))],
    response_model=EmissaoResponse,
    summary="Emitir NFC-e",
    description=(
        "Emite NFC-e (modelo 65) a partir de uma venda do PDV. "
        "A autorização é síncrona: o resultado volta nesta resposta."
    ),
)
def emitir_nfce(
    user_token: dict = Depends(requer_modulo_fiscal),
    *,
    db: Session = Depends(get_db),
    payload: EmissaoNFCeRequest = Body(...),
):
    # Sem BackgroundTasks de propósito: a NFC-e é síncrona. Agendar polling
    # aqui atrasaria o cupom que o operador está esperando para entregar.
    from app.services.fiscal.emissao import emitir_nfce_venda

    doc = _handle_db_transaction(
        db, emitir_nfce_venda, payload.venda_id, user_token["empresa_id"],
    )
    return EmissaoResponse.de_documento(doc, "NFC-e")


@router.post(
    "/emitir/nfe/batch",
    response_model=EmissaoBatchResponse,
    summary="Emitir NF-e em Lote",
    description="Emite NF-e para múltiplas vendas sequencialmente. Máximo 20 vendas por lote.",
)
def emitir_nfe_batch(
    background_tasks: BackgroundTasks,
    user_token: dict = Depends(requer_modulo_fiscal),
    *,
    db: Session = Depends(get_db),
    payload: EmissaoNFeBatchRequest = Body(...),
):
    from app.services.fiscal.emissao import emitir_nfe_batch as _emitir_batch, poll_nfe_status_async

    empresa_id = user_token["empresa_id"]
    resultados = _emitir_batch(db, payload.venda_ids, empresa_id)

    for r in resultados:
        if r["status"] == "PROCESSANDO" and r["documento_id"]:
            background_tasks.add_task(poll_nfe_status_async, r["documento_id"], empresa_id)

    # Sucesso é a SEFAZ ter aceitado — não é "tudo que não deu pau".
    # A regra anterior (`not in ("ERRO", "REJEITADA")`) contava DENEGADA como
    # sucesso, e o contador que o lojista lê na tela mentia sobre o resultado.
    sucesso = sum(1 for r in resultados if r["status"] in ("AUTORIZADA", "PROCESSANDO"))
    return EmissaoBatchResponse(
        resultados=resultados,
        total=len(resultados),
        sucesso=sucesso,
        falha=len(resultados) - sucesso,
    )



@router.post(
    "/emitir/teste/nfe",
    response_model=EmissaoResponse,
    summary="Emitir NF-e de Teste",
    description=(
        "Emite NF-e com dados fictícios no ambiente de homologação. "
        "Apenas disponível quando ambiente_emissao = 2 (Homologação)."
    ),
)
def emitir_teste_nfe(
    background_tasks: BackgroundTasks,
    user_token: dict = Depends(requer_modulo_fiscal),
    *,
    db: Session = Depends(get_db),
):
    from app.services.fiscal.emissao import emitir_teste_nfe as _emitir_teste, poll_nfe_status_async

    empresa_id = user_token["empresa_id"]
    doc = _handle_db_transaction(db, _emitir_teste, empresa_id)

    if doc.status == "PROCESSANDO":
        background_tasks.add_task(poll_nfe_status_async, doc.id, empresa_id)

    return EmissaoResponse(
        documento_id=doc.id,
        ref_api=doc.ref_api,
        status=doc.status,
        mensagem=doc.mensagem_sefaz or f"NF-e de teste {doc.status.lower()}.",
        ambiente=2,
    )


# ===========================================================================
# CONSULTA (polling de status na API)
# ===========================================================================

@router.get(
    "/documentos/{documento_id}/consultar",
    response_model=DocumentoFiscalRead,
    summary="Consultar Status do Documento",
    description="Consulta o status atualizado do documento na API de emissão.",
)
def consultar_documento(
    user_token: dict = Depends(get_current_active_user),
    *,
    db: Session = Depends(get_db),
    documento_id: int = Path(..., ge=1, description="ID do documento fiscal"),
):
    from app.services.fiscal.emissao import consultar_documento as _consultar

    empresa_id = user_token["empresa_id"]
    return _handle_db_transaction(
        db, _consultar, documento_id, empresa_id,
    )


# ===========================================================================
# DEVOLUÇÃO — NF-e de entrada (finalidade 4) referenciando a nota original
# ===========================================================================

@router.post(
    "/documentos/{documento_id}/devolucao",
    response_model=DocumentoFiscalRead,
    summary="Emitir NF-e de Devolução",
    description=(
        "Emite uma NF-e de devolução (modelo 55, entrada, finalidade 4) total ou "
        "parcial a partir de uma NF-e/NFC-e autorizada. Consome número da NF-e. "
        "Com `devolver_estoque`, os itens voltam ao estoque quando a SEFAZ autorizar."
    ),
)
def emitir_devolucao(
    background_tasks: BackgroundTasks,
    user_token: dict = Depends(requer_modulo_fiscal),
    *,
    db: Session = Depends(get_db),
    documento_id: int = Path(..., ge=1, description="ID da nota de origem (autorizada)"),
    payload: EmissaoDevolucaoRequest = Body(...),
):
    from app.services.fiscal.devolucao import emitir_devolucao as _emitir
    from app.services.fiscal.emissao import poll_nfe_status_async

    doc = _handle_db_transaction(
        db,
        _emitir,
        documento_id,
        user_token["empresa_id"],
        payload,
        int(user_token["sub"]) if user_token.get("sub") else None,
    )

    # Mesmo acompanhamento do /emitir/nfe: se a SEFAZ ficou de responder, o
    # polling é o que traz a autorização -- e com ela o saldo e o estoque.
    if doc.status == "PROCESSANDO":
        background_tasks.add_task(poll_nfe_status_async, doc.id, user_token["empresa_id"])

    return documento_fiscal_service.obter_documento(db, doc.id)
