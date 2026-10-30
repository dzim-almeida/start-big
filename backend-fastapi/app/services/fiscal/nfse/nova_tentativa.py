# ---------------------------------------------------------------------------
# ARQUIVO: services/fiscal/nfse/nova_tentativa.py
# DESCRIÇÃO: "Tentar de novo" na NFS-e recusada, pela gaveta de detalhe.
# ---------------------------------------------------------------------------
"""
Pedido do Alan em 30/10/2026: a NF-e recusada tem "Reemitir" no detalhe; a
NFS-e não tinha nada, e o lojista precisava voltar à OS para emitir de novo.

Não há "reemissão" própria: a nova tentativa É a emissão da OS (ou da
instalação), que relê a OS e o cadastro — então o que o lojista corrigiu
depois da recusa vai junto. A NFS-e não reserva número (a Focus numera a DPS),
então tentar de novo não queima nada.

Só a ÚLTIMA tentativa recusada de uma OS pode tentar de novo: uma mais antiga
já foi substituída, e a trava de nota viva da emissão continua valendo.
A avulsa não tem de onde reler os dados: emite-se uma nova pela tela da avulsa.
"""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.crud import fiscal as crud
from app.db.models.documento_fiscal import DocumentoFiscal
from app.services.fiscal.nfse.marcenaria import PAPEL_INSTALACAO

STATUS_RECUSADA = ("REJEITADA", "NAO_TRANSMITIDA", "ERRO")


def tentativa_mais_nova(db: Session, doc: DocumentoFiscal) -> Optional[DocumentoFiscal]:
    """Outra NFS-e da mesma OS e do mesmo papel, posterior a esta."""
    if not doc.origem_numero_os:
        return None
    return (
        db.query(DocumentoFiscal)
        .filter(
            DocumentoFiscal.tipo_documento == "NFSE",
            DocumentoFiscal.origem_numero_os == doc.origem_numero_os,
            DocumentoFiscal.papel == doc.papel,
            DocumentoFiscal.id > doc.id,
        )
        .order_by(DocumentoFiscal.id.desc())
        .first()
    )


def pode_tentar_de_novo(db: Session, doc: DocumentoFiscal) -> bool:
    return (
        doc.status in STATUS_RECUSADA
        and bool(doc.origem_numero_os)
        and tentativa_mais_nova(db, doc) is None
    )


def tentar_nfse_de_novo(
    db: Session, documento_id: int, empresa_id: int, confirmar_duplicidade: bool = False,
) -> DocumentoFiscal:
    from app.services.fiscal.nfse.emissao_os import emitir_nfse_os
    from app.services.fiscal.nfse.marcenaria import emitir_nfse_instalacao

    doc = crud.get_documento_fiscal(db, documento_id)
    if not doc or doc.tipo_documento != "NFSE":
        raise HTTPException(status_code=404, detail="NFS-e não encontrada.")

    if doc.status not in STATUS_RECUSADA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "codigo": "NFSE_NAO_RECUSADA",
                "mensagem": "Só a NFS-e que não saiu pode ser enviada de novo.",
            },
        )
    if not doc.origem_numero_os:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "codigo": "NFSE_AVULSA",
                "mensagem": "A NFS-e avulsa não guarda o formulário: emita uma nova em “Emitir NFS-e avulsa”.",
            },
        )
    nova = tentativa_mais_nova(db, doc)
    if nova:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "codigo": "NFSE_JA_TEM_TENTATIVA_NOVA",
                "mensagem": "Esta OS já tem uma tentativa mais nova desta nota.",
                "documento_id": nova.id,
            },
        )

    if doc.papel == PAPEL_INSTALACAO:
        return emitir_nfse_instalacao(db, doc.origem_numero_os, empresa_id, confirmar_duplicidade)

    # O papel guarda o código nacional (NFSE:<codigo>). Com um só código na OS a
    # emissão ignora a escolha; se o lojista trocou o código do serviço para
    # corrigir a recusa, o código antigo não existe mais e vale o único que há.
    codigo = (doc.papel or "").split(":", 1)[1] if (doc.papel or "").startswith("NFSE:") else None
    try:
        return emitir_nfse_os(
            db, doc.origem_numero_os, empresa_id,
            tentativa_anterior_id=doc.id, confirmar_duplicidade=confirmar_duplicidade, codigo_nacional=codigo,
        )
    except HTTPException as exc:
        detalhe = exc.detail if isinstance(exc.detail, dict) else {}
        if codigo and detalhe.get("codigo") == "NFSE_ESCOLHA_O_CODIGO" and len(detalhe.get("codigos") or []) == 1:
            return emitir_nfse_os(
                db, doc.origem_numero_os, empresa_id,
                tentativa_anterior_id=doc.id, confirmar_duplicidade=confirmar_duplicidade, codigo_nacional=None,
            )
        raise
