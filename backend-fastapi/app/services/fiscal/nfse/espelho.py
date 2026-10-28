# ---------------------------------------------------------------------------
# ARQUIVO: services/fiscal/nfse/espelho.py
# DESCRIÇÃO: Espelha a NFS-e da OS nos campos `*_nfse` da nota da OS
#            (`ordem_servico_nota_fiscal`), que existem desde d4e5f6a7b8c9 e
#            nunca tinham sido preenchidos. docs/nfse-plano.md, F3.
# ---------------------------------------------------------------------------
"""
O livro fiscal continua sendo `documento_fiscal`; isto é a conveniência da tela
da OS — como `espelho_nota.py` faz para a venda. O código de verificação só
existe aqui: `documento_fiscal` não tem coluna para ele, e é com ele que o
tomador confere a nota no portal da NFS-e.

Nunca levanta: espelho não pode derrubar a emissão nem a consulta.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.db.models.documento_fiscal import DocumentoFiscal
from app.db.models.ordem_servico_nota_fiscal import OrdemServicoNotaFiscal

logger = logging.getLogger(__name__)


def espelhar_nfse_na_os(db: Session, doc: DocumentoFiscal, resultado: Optional[dict] = None) -> None:
    if doc.tipo_documento != "NFSE" or doc.origem_tipo != "OS" or doc.origem_id is None:
        return
    try:
        nota = db.query(OrdemServicoNotaFiscal).filter(OrdemServicoNotaFiscal.os_id == doc.origem_id).first()
        if nota is None:
            nota = OrdemServicoNotaFiscal(os_id=doc.origem_id)
            db.add(nota)

        nota.status_nfse = doc.status
        nota.numero_nfse = str(doc.numero_documento) if doc.numero_documento else nota.numero_nfse
        if resultado and resultado.get("codigo_verificacao"):
            nota.codigo_verificacao_nfse = str(resultado["codigo_verificacao"])[:50]
        if doc.status == "AUTORIZADA" and not nota.data_emissao_nfse:
            nota.data_emissao_nfse = datetime.now(timezone.utc)
        # O link público (consulta no portal) vale mais que o PDF da emissora:
        # é o que o tomador abre sem login e não expira.
        nota.url_nfse = doc.url_consulta or doc.url_pdf or nota.url_nfse
        nota.mensagem_nfse = (doc.mensagem_sefaz or "")[:500] or None
        db.flush()
    except Exception:
        logger.exception("[NFS-e] Falha ao espelhar o documento %s na OS", doc.id)
