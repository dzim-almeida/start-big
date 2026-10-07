# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/fiscal_eventos.py
# DESCRIÇÃO: Centro Fiscal — eventos: cancelamento, carta de correção, inutilização
# e ajustes de numeração.
#
# Saiu do fiscal.py na F5 (07/10/2026), sem mudar comportamento: o
# código foi movido, não reescrito. As URLs não mudaram: `fiscal.py` inclui
# este router sem prefixo, e a trava do módulo NFE vem de lá.
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Body, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from app.core.depends import get_current_active_user, get_db, requer_configuracao_fiscal, _handle_db_transaction
from app.schemas.documento_fiscal import DocumentoFiscalRead
from app.schemas.emissao_fiscal import CartaCorrecaoRead, CartaCorrecaoRequest, GapNumeracao, InutilizacaoRead, AjusteNumeracaoRequest, InutilizacaoRequest, CancelamentoRequest
from .fiscal_documentos import _cliente_fiscal

# Sem `dependencies`: a trava do módulo NFE é herdada do router de `fiscal.py`.
router = APIRouter()


# ===========================================================================
# CANCELAMENTO
# ===========================================================================

@router.post(
    "/documentos/{documento_id}/cancelar",
    response_model=DocumentoFiscalRead,
    summary="Cancelar Documento Fiscal",
    description="Solicita cancelamento de documento autorizado (justificativa mínima: 15 caracteres).",
)
def cancelar_documento(
    user_token: dict = Depends(get_current_active_user),
    *,
    db: Session = Depends(get_db),
    documento_id: int = Path(..., ge=1, description="ID do documento fiscal"),
    payload: CancelamentoRequest = Body(...),
):
    from app.services.fiscal.emissao import cancelar_documento as _cancelar

    empresa_id = user_token["empresa_id"]
    return _handle_db_transaction(
        db,
        _cancelar,
        documento_id,
        empresa_id,
        payload.justificativa,
    )


# ===========================================================================
# CARTA DE CORREÇÃO (CC-e) — evento anexo à NF-e, até 20 por nota
# ===========================================================================

@router.post(
    "/documentos/{documento_id}/carta-correcao",
    response_model=CartaCorrecaoRead,
    summary="Registrar Carta de Correção",
    description=(
        "Registra uma CC-e na NF-e autorizada (só modelo 55; 15 a 1000 caracteres). "
        "A última carta substitui as anteriores na SEFAZ."
    ),
)
def registrar_carta_correcao(
    user_token: dict = Depends(get_current_active_user),
    *,
    db: Session = Depends(get_db),
    documento_id: int = Path(..., ge=1, description="ID da NF-e"),
    payload: CartaCorrecaoRequest = Body(...),
):
    from app.services.fiscal.carta_correcao import emitir_carta_correcao

    carta = _handle_db_transaction(
        db,
        emitir_carta_correcao,
        documento_id,
        user_token["empresa_id"],
        payload.correcao,
        int(user_token["sub"]) if user_token.get("sub") else None,
    )
    return CartaCorrecaoRead.de_registro(carta)


@router.get(
    "/documentos/{documento_id}/cartas-correcao",
    response_model=list[CartaCorrecaoRead],
    summary="Cartas de Correção da Nota",
    description="Histórico de CC-e da NF-e, na ordem da SEFAZ (a última é a vigente).",
)
def listar_cartas_correcao(
    user_token: dict = Depends(get_current_active_user),
    *,
    db: Session = Depends(get_db),
    documento_id: int = Path(..., ge=1, description="ID da NF-e"),
):
    from app.services.fiscal.carta_correcao import listar_cartas_correcao as _listar

    return [
        CartaCorrecaoRead.de_registro(c)
        for c in _listar(db, documento_id, user_token["empresa_id"])
    ]


def _arquivo_da_carta(db: Session, user_token: dict, carta_id: int, extensao: str):
    """XML ou PDF da carta: disco primeiro; emissora como plano B, guardando."""
    from fastapi.responses import Response
    from app.services.fiscal.arquivos import guardar_pdf, guardar_xml, ler_pdf, ler_xml
    from app.services.fiscal.carta_correcao import obter_carta_correcao

    carta = obter_carta_correcao(db, carta_id, user_token["empresa_id"])
    e_pdf = extensao == "pdf"
    conteudo = (ler_pdf if e_pdf else ler_xml)(
        carta.caminho_pdf_local if e_pdf else carta.caminho_xml_local
    )

    url = carta.url_pdf if e_pdf else carta.url_xml
    if not conteudo and url:
        client = _cliente_fiscal(db, user_token["empresa_id"])
        conteudo = (client.baixar_pdf if e_pdf else client.baixar_xml)(url)
        chave = carta.documento.chave_acesso or f"doc-{carta.documento_id}"
        fallback = f"{chave}_cce_{carta.sequencia or 0:02d}"
        caminho = (guardar_pdf if e_pdf else guardar_xml)(conteudo, chave=None, fallback=fallback)
        if caminho:
            setattr(carta, "caminho_pdf_local" if e_pdf else "caminho_xml_local", caminho)
            db.commit()

    if not conteudo:
        raise HTTPException(
            status_code=404,
            detail=f"{extensao.upper()} da carta indisponível: não está nesta máquina e a emissora não respondeu.",
        )

    nome = f"{carta.documento.chave_acesso or f'documento-{carta.documento_id}'}_cce_{carta.sequencia or 0:02d}.{extensao}"
    return Response(
        content=conteudo,
        media_type="application/pdf" if e_pdf else "application/xml",
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )


@router.get(
    "/cartas-correcao/{carta_id}/pdf",
    summary="Baixar o PDF da Carta de Correção",
)
def baixar_pdf_carta_correcao(
    user_token: dict = Depends(get_current_active_user),
    carta_id: int = Path(..., ge=1),
    *,
    db: Session = Depends(get_db),
):
    return _arquivo_da_carta(db, user_token, carta_id, "pdf")


@router.get(
    "/cartas-correcao/{carta_id}/xml",
    summary="Baixar o XML da Carta de Correção",
)
def baixar_xml_carta_correcao(
    user_token: dict = Depends(get_current_active_user),
    carta_id: int = Path(..., ge=1),
    *,
    db: Session = Depends(get_db),
):
    return _arquivo_da_carta(db, user_token, carta_id, "xml")


# ===========================================================================
# INUTILIZAÇÃO DE NUMERAÇÃO
# ===========================================================================

@router.get(
    "/numeracao/gaps",
    response_model=list[GapNumeracao],
    summary="Buracos na Numeração",
    description=(
        "Lista faixas de numeração que foram reservadas mas nunca viraram nota "
        "autorizada. Esses números precisam ser inutilizados junto à SEFAZ."
    ),
)
def listar_gaps_numeracao(
    user_token: dict = Depends(get_current_active_user),
    *,
    db: Session = Depends(get_db),
):
    from app.services.fiscal.inutilizacao import listar_gaps_numeracao as _gaps

    return _gaps(db, user_token["empresa_id"])


@router.get(
    "/numeracao/inutilizacoes",
    response_model=list[InutilizacaoRead],
    summary="Inutilizações Solicitadas",
    description="Histórico de pedidos de inutilização de faixa de numeração.",
)
def listar_inutilizacoes(
    user_token: dict = Depends(get_current_active_user),
    *,
    db: Session = Depends(get_db),
):

    from app.services.fiscal.inutilizacao import listar_inutilizacoes as _listar

    return _listar(db, user_token["empresa_id"])


@router.post(
    "/numeracao/ajustar-duplicidade",
    summary="Ajustar numeração depois de uma Rejeição 539",
    description=(
        "A SEFAZ disse que o número já existe (emitido por outro sistema). Leva o "
        "contador da série da nota para o último número informado, nunca para trás."
    ),
)
def ajustar_numeracao_duplicidade(
    user_token: dict = Depends(requer_configuracao_fiscal),
    *,
    db: Session = Depends(get_db),
    payload: AjusteNumeracaoRequest = Body(...),
):
    from app.services.fiscal.numeracao import ajustar_numeracao_por_duplicidade

    return _handle_db_transaction(
        db, ajustar_numeracao_por_duplicidade,
        user_token["empresa_id"], payload.documento_id, payload.ultimo_numero,
    )


@router.post(
    "/numeracao/inutilizar",
    response_model=InutilizacaoRead,
    summary="Inutilizar Faixa de Numeração",
    description=(
        "Declara à SEFAZ que uma faixa de numeração não foi utilizada. "
        "A justificativa precisa de no mínimo 15 caracteres."
    ),
)
def inutilizar_numeracao(
    user_token: dict = Depends(get_current_active_user),
    *,
    db: Session = Depends(get_db),
    payload: InutilizacaoRequest = Body(...),
):
    from app.services.fiscal.inutilizacao import solicitar_inutilizacao

    return _handle_db_transaction(
        db,
        solicitar_inutilizacao,
        user_token["empresa_id"],
        payload.serie,
        payload.numero_inicial,
        payload.numero_final,
        payload.justificativa,
    )
