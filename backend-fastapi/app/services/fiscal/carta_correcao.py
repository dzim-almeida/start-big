# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/carta_correcao.py
# DESCRIÇÃO: Carta de Correção Eletrônica (CC-e) — evento anexo a uma NF-e.
#
# Corrige erro NÃO fiscal (texto, endereço, transporte, observação) sem
# cancelar nem reemitir. Não serve para valor, quantidade, imposto ou troca de
# destinatário: para isso a via é cancelar no prazo ou emitir devolução.
#
# Regras que a SEFAZ impõe e que este módulo replica ANTES de gastar uma
# chamada: só modelo 55, só nota autorizada, no máximo 20 cartas por nota. A
# última carta substitui as anteriores -- a tela pré-preenche com a anterior
# para o operador consolidar, e o serviço não interfere nisso.
# ---------------------------------------------------------------------------

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.crud import fiscal as crud
from app.db.models.carta_correcao_fiscal import CartaCorrecaoFiscal
from app.db.models.documento_fiscal import DocumentoFiscal
from app.services.fiscal.arquivos import guardar_pdf, guardar_xml
from app.services.fiscal.http import get_fiscal_client
from app.services.fiscal.http.client import (
    EmissaoResultado,
    RESULTADO_AUTORIZADO,
    RESULTADO_NAO_TRANSMITIDO,
)

logger = logging.getLogger(__name__)

LIMITE_CARTAS_POR_NOTA = 20


def _obter_nfe_autorizada(db: Session, documento_id: int) -> DocumentoFiscal:
    """A nota que pode receber carta -- ou a exceção que explica por que não."""
    doc = crud.get_documento_fiscal(db, documento_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento fiscal não encontrado.")

    if doc.tipo_documento != "NFE":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "codigo": "CCE_SOMENTE_NFE",
                "mensagem": (
                    "Carta de correção só existe para NF-e. Para um cupom NFC-e, "
                    "cancele no prazo ou emita uma NF-e de devolução."
                ),
            },
        )

    if doc.status != "AUTORIZADA":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Apenas NF-e autorizada recebe carta de correção.",
        )

    if not doc.ref_api:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Documento não possui referência de API para a carta de correção.",
        )
    return doc


def _assert_cabe_mais_uma_carta(db: Session, documento_id: int) -> None:
    """Limite da SEFAZ e exclusão mútua -- decididos aqui, sem gastar chamada."""
    autorizadas = (
        db.query(CartaCorrecaoFiscal)
        .filter_by(documento_id=documento_id, status="AUTORIZADA")
        .count()
    )
    if autorizadas >= LIMITE_CARTAS_POR_NOTA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "codigo": "CCE_LIMITE_ATINGIDO",
                "mensagem": (
                    f"Esta NF-e já tem {LIMITE_CARTAS_POR_NOTA} cartas de correção, "
                    "o máximo que a SEFAZ aceita."
                ),
            },
        )

    # Duas cartas ao mesmo tempo na mesma nota voltariam como 573/574 da SEFAZ.
    em_andamento = (
        db.query(CartaCorrecaoFiscal)
        .filter_by(documento_id=documento_id, status="PROCESSANDO")
        .count()
    )
    if em_andamento:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma carta de correção em processamento para esta NF-e.",
        )


def _aplicar_resultado_carta(carta: CartaCorrecaoFiscal, resultado: EmissaoResultado) -> None:
    """Resposta da emissora -> registro. Três desfechos, como na emissão."""
    carta.codigo_status_sefaz = resultado.get("codigo_sefaz")
    carta.mensagem_sefaz = resultado.get("mensagem_sefaz")

    status_api = resultado.get("status")
    if status_api == RESULTADO_AUTORIZADO:
        carta.status = "AUTORIZADA"
        carta.sequencia = resultado.get("numero_carta_correcao")
        carta.protocolo = resultado.get("protocolo")
        carta.url_xml = resultado.get("url_xml")
        carta.url_pdf = resultado.get("url_pdf")
        carta.data_evento = datetime.now(timezone.utc)
    elif status_api == RESULTADO_NAO_TRANSMITIDO:
        # A plataforma recusou antes de a SEFAZ ver. Não é rejeição.
        carta.status = "ERRO"
    else:
        # A SEFAZ respondeu "não" (573 duplicidade, 574 sequência, etc.).
        carta.status = "REJEITADA"


def _arquivar_carta(carta: CartaCorrecaoFiscal, doc: DocumentoFiscal, client) -> None:
    """Best-effort: o evento já está na SEFAZ; disco cheio não desfaz isso.

    O nome leva o sufixo `_cce_NN`: sem ele a carta cairia no mesmo caminho do
    XML da nota, e `guardar_xml` nunca sobrescreve -- a carta ficaria sem arquivo.
    """
    fallback = f"{doc.chave_acesso or f'doc-{doc.id}'}_cce_{carta.sequencia or 0:02d}"
    try:
        if carta.url_xml:
            carta.caminho_xml_local = guardar_xml(
                client.baixar_xml(carta.url_xml), chave=None, fallback=fallback,
            )
        if carta.url_pdf:
            carta.caminho_pdf_local = guardar_pdf(
                client.baixar_pdf(carta.url_pdf), chave=None, fallback=fallback,
            )
    except Exception as exc:
        logger.warning("[FISCAL] Carta %s: arquivos não vieram agora: %s", carta.id, exc)


def emitir_carta_correcao(
    db: Session,
    documento_id: int,
    empresa_id: int,
    correcao: str,
    usuario_id: Optional[int],
) -> CartaCorrecaoFiscal:
    """Registra uma CC-e na NF-e e transmite pela emissora.

    O registro nasce PROCESSANDO antes da chamada: é ele que sustenta a
    exclusão mútua enquanto a resposta não vem. Numa falha de comunicação o
    serviço levanta 502 e o `_handle_db_transaction` do endpoint desfaz o
    registro -- de propósito, para não deixar um PROCESSANDO preso trancando
    a nota. Se a carta chegou à SEFAZ mesmo assim, a retentativa volta como
    rejeição 573 (duplicidade), visível no histórico.
    """
    doc = _obter_nfe_autorizada(db, documento_id)
    _assert_cabe_mais_uma_carta(db, doc.id)

    fs = crud.get_fiscal_settings(db, empresa_id)
    carta = CartaCorrecaoFiscal(
        empresa_id=empresa_id,
        documento_id=doc.id,
        correcao=correcao,
        status="PROCESSANDO",
        ambiente_emissao=fs.ambiente_emissao if fs else None,
        usuario_id=usuario_id,
    )
    db.add(carta)
    db.flush()

    client = get_fiscal_client(
        fs.ambiente_emissao if fs else 2, crud.get_licenca_token(db),
    )
    resultado = _transmitir_carta(db, carta, doc, client, correcao)
    _aplicar_resultado_carta(carta, resultado)
    if carta.status == "AUTORIZADA":
        _arquivar_carta(carta, doc, client)

    # O status final precisa estar visível para a próxima contagem de
    # PROCESSANDO na mesma sessão; quem comita é o endpoint.
    db.flush()
    return carta


def _transmitir_carta(db: Session, carta: CartaCorrecaoFiscal, doc: DocumentoFiscal, client, correcao: str) -> EmissaoResultado:
    """Chama a emissora; falha de transporte vira 501/502 com o registro em ERRO."""
    try:
        return client.emitir_carta_correcao(doc.ref_api, correcao)
    except NotImplementedError as e:
        carta.status = "ERRO"
        carta.mensagem_sefaz = str(e)
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(e))
    except Exception as e:
        logger.error("[FISCAL] Erro ao registrar carta na doc=%d: %s", doc.id, e)
        carta.status = "ERRO"
        carta.mensagem_sefaz = f"Falha de comunicação: {str(e)[:300]}"
        db.flush()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erro de comunicação ao registrar a carta de correção: {str(e)[:400]}",
        )


def listar_cartas_correcao(
    db: Session, documento_id: int, empresa_id: int
) -> list[CartaCorrecaoFiscal]:
    """Histórico de cartas da nota, na ordem da SEFAZ (a última é a vigente)."""
    if not crud.get_documento_fiscal(db, documento_id):
        raise HTTPException(status_code=404, detail="Documento fiscal não encontrado.")
    return (
        db.query(CartaCorrecaoFiscal)
        .filter_by(documento_id=documento_id, empresa_id=empresa_id)
        .order_by(CartaCorrecaoFiscal.sequencia.nulls_last(), CartaCorrecaoFiscal.id)
        .all()
    )


def obter_carta_correcao(db: Session, carta_id: int, empresa_id: int) -> CartaCorrecaoFiscal:
    carta = db.get(CartaCorrecaoFiscal, carta_id)
    if not carta or carta.empresa_id != empresa_id:
        raise HTTPException(status_code=404, detail="Carta de correção não encontrada.")
    return carta
