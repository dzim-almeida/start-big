# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/emissao_eventos.py
# DESCRIÇÃO: Eventos de um documento já transmitido: consulta, polling, cancelamento
# (com a janela legal) e histórico de tentativas.
#
# Saiu do emissao.py na F5 (07/10/2026), sem mudar comportamento: o código foi
# movido, não reescrito. Quem importa de `emissao` continua funcionando.
# ---------------------------------------------------------------------------

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.db.models.documento_fiscal import DocumentoFiscal
from app.db.crud import fiscal as crud
from .http import get_fiscal_client
from .espelho_nota import espelhar_na_nota_da_venda
from app.db.session import SessionLocal
from .emissao_nucleo import STATUS_CONSULTAVEIS, _aplicar_resultado, _obter_fiscal_settings

logger = logging.getLogger(__name__)


def consultar_documento(db: Session, documento_id: int, empresa_id: int) -> DocumentoFiscal:
    """Polling: consulta status do documento na API e atualiza."""
    doc = crud.get_documento_fiscal(db, documento_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento fiscal não encontrado.")

    if not doc.ref_api:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Documento não possui referência de API para consulta.",
        )

    # Documento não transmitido não tem o que consultar. Ver STATUS_CONSULTAVEIS.
    if doc.status not in STATUS_CONSULTAVEIS:
        return doc

    fiscal_settings = _obter_fiscal_settings(db, empresa_id)
    token = crud.get_licenca_token(db)
    client = get_fiscal_client(fiscal_settings.ambiente_emissao, token)

    status_antes = doc.status
    try:
        resultado = client.consultar_nfe(doc.ref_api, doc.tipo_documento)
        _aplicar_resultado(doc, resultado, client)
        espelhar_na_nota_da_venda(db, doc)
        # A devolução que ficou PROCESSANDO/INDETERMINADA na emissão só devolve
        # saldo e estoque quando a SEFAZ confirma -- e a confirmação chega aqui.
        if status_antes != "AUTORIZADA" and doc.status == "AUTORIZADA":
            from .devolucao import aplicar_efeitos_autorizacao
            aplicar_efeitos_autorizacao(db, doc)
    except NotImplementedError:
        pass
    except Exception as e:
        logger.error("[FISCAL] Erro ao consultar doc=%d: %s", documento_id, e)

    return doc


async def poll_nfe_status_async(documento_id: int, empresa_id: int):
    """
    Realiza o polling assíncrono para a API StartBig.
    Tempo máximo: ~3 minutos.
    """
    intervals = [3, 5, 8, 12, 15, 20, 20, 20, 25, 25, 30]
    for wait_time in intervals:
        await asyncio.sleep(wait_time)

        db = SessionLocal()
        try:
            doc = consultar_documento(db, documento_id, empresa_id)
            db.commit()
            if doc.status not in STATUS_CONSULTAVEIS:
                break
        except Exception as e:
            db.rollback()
            logger.error("[FISCAL] Erro no polling background: %s", e)
        finally:
            db.close()


# Prazo legal para cancelamento, contado da autorização. O prazo é do MODELO,
# não do sistema: a NFC-e é muito mais curta porque o cliente sai da loja com a
# mercadoria — passado o prazo, a via é a nota de devolução.
JANELA_CANCELAMENTO_NFE = timedelta(hours=24)   # modelo 55


JANELA_CANCELAMENTO_NFCE = timedelta(minutes=30)  # modelo 65


JANELA_CANCELAMENTO_POR_TIPO = {
    "NFE": JANELA_CANCELAMENTO_NFE,
    "NFCE": JANELA_CANCELAMENTO_NFCE,
}


def _descrever_janela(janela: timedelta) -> str:
    """'24 horas' / '30 minutos' — para a mensagem que o operador lê."""
    if janela >= timedelta(hours=1):
        return f"{int(janela.total_seconds() // 3600)} horas"
    return f"{int(janela.total_seconds() // 60)} minutos"


def _descrever_decorrido(decorrido: timedelta) -> str:
    minutos = int(decorrido.total_seconds() // 60)
    if minutos < 60:
        return f"{minutos} minutos"
    return f"{minutos // 60} horas"


def _assert_dentro_da_janela_de_cancelamento(doc: DocumentoFiscal) -> None:
    """
    Barra cancelamento fora do prazo da SEFAZ.

    Sem isso o operador tenta cancelar, a SEFAZ recusa — e ele já devolveu o
    dinheiro ao cliente. Melhor recusar aqui e orientar a emitir devolução.
    """
    if not doc.data_autorizacao:
        return

    autorizacao = doc.data_autorizacao
    if autorizacao.tzinfo is None:
        autorizacao = autorizacao.replace(tzinfo=timezone.utc)

    # Tipo desconhecido cai no prazo mais CURTO: recusar um cancelamento que
    # ainda daria tempo é um aborrecimento; liberar um fora do prazo faz a
    # SEFAZ recusar depois de o caixa já ter devolvido o dinheiro.
    janela = JANELA_CANCELAMENTO_POR_TIPO.get(
        doc.tipo_documento, JANELA_CANCELAMENTO_NFCE,
    )

    decorrido = datetime.now(timezone.utc) - autorizacao
    if decorrido <= janela:
        return

    documento = "NFC-e" if doc.tipo_documento == "NFCE" else "NF-e"
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "codigo": "PRAZO_CANCELAMENTO_EXPIRADO",
            "mensagem": (
                f"O prazo de {_descrever_janela(janela)} para cancelar esta "
                f"{documento} expirou (autorizada há "
                f"{_descrever_decorrido(decorrido)}). Emita uma NF-e de "
                f"devolução para reverter a operação."
            ),
            "documento_id": doc.id,
        },
    )


def cancelar_documento(
    db: Session, documento_id: int, empresa_id: int, justificativa: str
) -> DocumentoFiscal:
    """Cancela documento fiscal autorizado, dentro do prazo legal."""
    doc = crud.get_documento_fiscal(db, documento_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento fiscal não encontrado.")

    if doc.status != "AUTORIZADA":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Apenas documentos autorizados podem ser cancelados.",
        )

    _assert_dentro_da_janela_de_cancelamento(doc)

    if not doc.ref_api:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Documento não possui referência de API para cancelamento.",
        )

    fiscal_settings = _obter_fiscal_settings(db, empresa_id)
    token = crud.get_licenca_token(db)
    client = get_fiscal_client(fiscal_settings.ambiente_emissao, token)

    try:
        resultado = client.cancelar_nfe(
            doc.ref_api, justificativa, doc.tipo_documento
        )
        _aplicar_resultado(doc, resultado, client)
    except NotImplementedError as e:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(e),
        )
    except Exception as e:
        logger.error("[FISCAL] Erro ao cancelar doc=%d: %s", documento_id, e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erro de comunicação ao cancelar: {str(e)[:400]}",
        )

    espelhar_na_nota_da_venda(db, doc)
    return doc


def obter_historico_tentativas(db: Session, documento_id: int) -> list[DocumentoFiscal]:
    """
    Retorna a cadeia completa de tentativas (do mais recente ao mais antigo).
    Segue a linked list via tentativa_anterior_id.
    """
    tentativas = []
    doc = crud.get_documento_fiscal(db, documento_id)

    if not doc:
        raise HTTPException(status_code=404, detail="Documento fiscal não encontrado.")

    # Subir na cadeia: encontrar o documento mais recente que aponta para este
    doc_mais_recente = crud.get_documento_by_tentativa_anterior(db, documento_id)

    while doc_mais_recente:
        proximo = crud.get_documento_by_tentativa_anterior(db, doc_mais_recente.id)
        if proximo:
            doc_mais_recente = proximo
        else:
            break

    # Começar do mais recente (ou do documento pedido se não há mais recente)
    atual = doc_mais_recente or doc
    while atual:
        tentativas.append(atual)
        if atual.tentativa_anterior_id:
            atual = crud.get_documento_fiscal(db, atual.tentativa_anterior_id)
        else:
            break

    return tentativas
