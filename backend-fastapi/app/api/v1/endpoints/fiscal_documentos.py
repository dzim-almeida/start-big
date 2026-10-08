# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/fiscal_documentos.py
# DESCRIÇÃO: Centro Fiscal — documentos: resumo, pendências, lista, detalhe,
# histórico, XML/PDF e pacote do período.
#
# Saiu do fiscal.py na F5 (07/10/2026), sem mudar comportamento: o
# código foi movido, não reescrito. As URLs não mudaram: `fiscal.py` inclui
# este router sem prefixo, e a trava do módulo NFE vem de lá.
# ---------------------------------------------------------------------------

from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from app.core.depends import get_current_active_user, get_db, requer_modulo_fiscal, _handle_db_transaction
from app.db.crud import fiscal as fiscal_crud
from app.schemas.documento_fiscal import DocumentoFiscalHistorico, DocumentoFiscalListRead, DocumentoFiscalRead, DocumentoFiscalResumo, PendenciasGlobais
from app.services import documento_fiscal as documento_fiscal_service
from app.services import pendencias_globais as pendencias_globais_service

# Sem `dependencies`: a trava do módulo NFE é herdada do router de `fiscal.py`.
router = APIRouter()


# ===========================================================================
# RESUMO (contadores por status)
# ===========================================================================

@router.get(
    "/resumo",
    response_model=DocumentoFiscalResumo,
    summary="Resumo de Documentos Fiscais",
    description="Retorna contadores operacionais agrupados por status.",
)
def obter_resumo(
    user_token: dict = Depends(get_current_active_user),
    *,
    db: Session = Depends(get_db),
    tipo: Optional[str] = Query(
        None, description="Restringe os contadores a um tipo (NFE, NFCE, NFSE)",
    ),
):
    return documento_fiscal_service.obter_resumo(db, tipo=tipo)


# ===========================================================================
# PENDÊNCIAS GLOBAIS
# ===========================================================================

@router.get(
    "/pendencias",
    response_model=PendenciasGlobais,
    summary="Pendências Fiscais Globais",
    description=(
        "Retorna pendências cadastrais que impedem emissão fiscal: "
        "produtos sem NCM, serviços sem código LC 116, pagamentos sem código SEFAZ "
        "e dados do emitente incompletos."
    ),
)
def obter_pendencias(
    user_token: dict = Depends(get_current_active_user),
    *,
    db: Session = Depends(get_db),
):
    empresa_id = user_token["empresa_id"]
    return pendencias_globais_service.obter_pendencias_globais(db, empresa_id)


# ===========================================================================
# LISTAGEM DE DOCUMENTOS
# ===========================================================================

@router.get(
    "/documentos",
    response_model=DocumentoFiscalListRead,
    summary="Listar Documentos Fiscais",
    description="Retorna lista paginada de documentos fiscais com filtros.",
)
def listar_documentos(
    user_token: dict = Depends(get_current_active_user),
    *,
    db: Session = Depends(get_db),
    status_filtro: Optional[str] = Query(None, alias="status", description="Filtrar por status"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo (NFE, NFCE, NFSE)"),
    origem: Optional[str] = Query(None, description="Filtrar por origem (VENDA, ORDEM_SERVICO)"),
    busca: Optional[str] = Query(None, description="Busca por chave de acesso ou número OS"),
    data_inicio: Optional[date] = Query(None, description="Data início (YYYY-MM-DD)"),
    data_fim: Optional[date] = Query(None, description="Data fim (YYYY-MM-DD)"),
    pagina: int = Query(1, ge=1, description="Número da página"),
    por_pagina: int = Query(20, ge=1, le=100, description="Itens por página"),
):
    return documento_fiscal_service.listar_documentos(
        db,
        status_filtro=status_filtro,
        tipo=tipo,
        origem=origem,
        busca=busca,
        data_inicio=data_inicio,
        data_fim=data_fim,
        pagina=pagina,
        por_pagina=por_pagina,
    )


# ===========================================================================
# DETALHE DO DOCUMENTO
# ===========================================================================

# Declarado ANTES de /documentos/{documento_id}: o path param captura
# qualquer segmento, e 'exportar-xml' viraria um 422 de 'nao e inteiro'.
@router.get(
    "/documentos/exportar-xml",
    summary="XMLs do período (ZIP para o contador)",
    description=(
        "Baixa um ZIP com o XML de cada NF-e/NFC-e autorizada ou cancelada no "
        "período, as inutilizações homologadas e uma relação em CSV. O que a "
        "emissora não devolver vai listado em nao_baixados.txt, sem derrubar o pacote."
    ),
)
def exportar_xml_periodo(
    user_token: dict = Depends(requer_modulo_fiscal),
    *,
    db: Session = Depends(get_db),
    data_inicio: date = Query(..., description="Primeiro dia (YYYY-MM-DD, data local)"),
    data_fim: date = Query(..., description="Último dia (YYYY-MM-DD, data local)"),
    tipo: Optional[str] = Query(None, description="NFE ou NFCE; vazio = os dois"),
):
    from fastapi.responses import Response
    from app.services.fiscal.exportacao_xml import montar_pacote_xml

    if data_fim < data_inicio:
        raise HTTPException(status_code=422, detail="data_fim anterior a data_inicio.")
    if (data_fim - data_inicio).days > 366:
        raise HTTPException(status_code=422, detail="O período máximo é de um ano.")

    conteudo, resumo = montar_pacote_xml(
        db, user_token["empresa_id"], data_inicio, data_fim, tipo,
    )
    nome = f"xml-fiscal-{data_inicio:%Y-%m-%d}_{data_fim:%Y-%m-%d}.zip"
    return Response(
        content=conteudo,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{nome}"',
            "X-Fiscal-Documentos": str(resumo["documentos"]),
            "X-Fiscal-Baixados": str(resumo["baixados"]),
            "X-Fiscal-Nao-Baixados": str(resumo["nao_baixados"]),
        },
    )


@router.get(
    "/documentos/{documento_id}",
    response_model=DocumentoFiscalRead,
    summary="Detalhe do Documento Fiscal",
    description="Retorna os dados completos de um documento fiscal.",
)
def obter_documento(
    user_token: dict = Depends(get_current_active_user),
    *,
    db: Session = Depends(get_db),
    documento_id: int = Path(..., ge=1, description="ID do documento fiscal"),
):
    return documento_fiscal_service.obter_documento(db, documento_id)


# ===========================================================================
# HISTÓRICO DE TENTATIVAS
# ===========================================================================

@router.get(
    "/documentos/{documento_id}/historico",
    response_model=DocumentoFiscalHistorico,
    summary="Histórico de Tentativas",
    description="Retorna a cadeia completa de tentativas de emissão (do mais recente ao mais antigo).",
)
def obter_historico(
    user_token: dict = Depends(get_current_active_user),
    *,
    db: Session = Depends(get_db),
    documento_id: int = Path(..., ge=1, description="ID do documento fiscal"),
):

    return documento_fiscal_service.obter_historico_tentativas(db, documento_id)


def _cliente_fiscal(db: Session, empresa_id: int):
    """
    O client da emissora, montado como a emissão monta.

    Vive aqui porque os endpoints de arquivo precisam dele para o plano B
    (buscar na emissora o que não está no disco) — e a assinatura pede
    ambiente e token, não a sessão.
    """
    from app.db.crud import fiscal as crud
    from app.services.fiscal.http.client_factory import get_fiscal_client

    settings_fiscais = crud.get_fiscal_settings(db, empresa_id)
    ambiente = settings_fiscais.ambiente_emissao if settings_fiscais else 2
    return get_fiscal_client(ambiente, crud.get_licenca_token(db))


# ===========================================================================
# ARQUIVOS DA NOTA (XML guardado no computador da loja)
# ===========================================================================


@router.get(
    "/documentos/{documento_id}/xml",
    summary="Baixar o XML da Nota",
    description=(
        "Entrega o XML autorizado. Lê do disco da loja quando existe — e aí "
        "funciona sem internet; cai na emissora só para documentos anteriores "
        "ao arquivamento local, guardando o que baixar."
    ),
)
def baixar_xml_documento(
    user_token: dict = Depends(get_current_active_user),
    documento_id: int = Path(..., ge=1),
    *,
    db: Session = Depends(get_db),
):
    from fastapi.responses import Response
    from app.services.fiscal.arquivos import obter_xml

    doc = fiscal_crud.get_documento_fiscal(db, documento_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Documento não encontrado.")

    conteudo = obter_xml(db, _cliente_fiscal(db, user_token["empresa_id"]), doc)
    if not conteudo:
        raise HTTPException(
            status_code=404,
            detail=(
                "XML indisponível: não está guardado nesta máquina e a emissora "
                "não respondeu."
            ),
        )
    db.commit()  # o `obter_xml` pode ter gravado o caminho recém-arquivado

    nome = f"{doc.chave_acesso or f'documento-{doc.id}'}.xml"
    return Response(
        content=conteudo,
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )


@router.get(
    "/documentos/{documento_id}/pdf",
    summary="Baixar o DANFE da Nota",
    description=(
        "Entrega o DANFE em PDF. Lê do disco da loja quando existe — e aí "
        "reimprime sem internet; cai na emissora como plano B."
    ),
)
def baixar_pdf_documento(
    user_token: dict = Depends(get_current_active_user),
    documento_id: int = Path(..., ge=1),
    *,
    db: Session = Depends(get_db),
):
    from fastapi.responses import Response
    from app.services.fiscal.arquivos import guardar_pdf, ler_pdf

    doc = fiscal_crud.get_documento_fiscal(db, documento_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Documento não encontrado.")

    conteudo = ler_pdf(doc.caminho_pdf_local)
    if not conteudo and doc.url_pdf:
        conteudo = _cliente_fiscal(db, user_token["empresa_id"]).baixar_pdf(doc.url_pdf)
        caminho = guardar_pdf(
            conteudo, chave=doc.chave_acesso,
            fallback=f"doc-{doc.id}", quando=doc.data_autorizacao,
        )
        if caminho:
            doc.caminho_pdf_local = caminho
            db.commit()

    if not conteudo:
        raise HTTPException(
            status_code=404,
            detail="DANFE indisponível: não está nesta máquina e a emissora não respondeu.",
        )

    nome = f"{doc.chave_acesso or f'documento-{doc.id}'}.pdf"
    return Response(
        content=conteudo,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )


@router.post(
    "/documentos/arquivos/sincronizar",
    summary="Guardar os XMLs que faltam",
    description=(
        "Baixa da emissora o XML das notas autorizadas que ainda não têm "
        "arquivo nesta máquina. É o caminho das notas emitidas antes do "
        "arquivamento local existir. Processa em lotes — rode de novo enquanto "
        "sobrar."
    ),
)
def sincronizar_arquivos_fiscais(
    user_token: dict = Depends(requer_modulo_fiscal),
    *,
    limite: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
):
    from app.services.fiscal.arquivos import sincronizar_pendentes

    def _sincronizar(db_: Session):
        cliente = _cliente_fiscal(db_, user_token["empresa_id"])
        return sincronizar_pendentes(db_, cliente, limite=limite)

    return _handle_db_transaction(db, _sincronizar)
