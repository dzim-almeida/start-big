# ---------------------------------------------------------------------------
# ARQUIVO: services/fiscal/os_notas.py
# DESCRIÇÃO: "Notas desta OS": quanto vai em cada nota (peças → NF-e, serviço
#            → NFS-e), a situação de cada uma e se a loja emite aquele tipo.
#            M5 de docs/nfse-melhorias-plano.md.
# ---------------------------------------------------------------------------
"""
Só leitura. Decisões do Alan (29/10/2026) que este arquivo segue:

- nota só sai quando o cliente pede: "não emitida" é estado normal, não
  pendência — nada aqui conta ou cobra;
- peça e serviço são notas diferentes (o 14.01 da LC 116 exclui as peças,
  que vão com ICMS) — cada lado tem o seu valor e a sua nota;
- o desconto da OS se divide na proporção, com a mesma regra da NFS-e
  (`desconto_dos_servicos`); a parte das peças é o resto.
"""

from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.enum import OrdemServicoStatus
from app.core.modulos import requer_modulo
from app.db.crud import fiscal as crud
from app.db.models.documento_fiscal import DocumentoFiscal
from app.services.fiscal.emissoes.adaptador_os import itens_de_produto
from app.services.fiscal.nfse.payload import desconto_dos_servicos, servicos_da_os


def _tem_modulo(db: Session, identificador: str) -> bool:
    try:
        requer_modulo(identificador)(db=db)
        return True
    except HTTPException:
        return False


def _resumo_doc(doc: Optional[DocumentoFiscal]) -> Optional[dict]:
    if doc is None:
        return None
    return {
        "id": doc.id,
        "status": doc.status,
        "numero": doc.numero_documento,
        "motivo": doc.mensagem_sefaz or doc.motivo_rejeicao,
        "url_pdf": doc.url_pdf,
        "valor": doc.valor_total,
        "papel": doc.papel,
    }


def notas_da_os(db: Session, numero_os: str) -> Optional[dict]:
    os_obj = crud.get_os_completa(db, numero_os)
    if not os_obj:
        return None

    produtos = itens_de_produto(os_obj)
    servicos = servicos_da_os(os_obj)
    base_produtos = sum(i.valor_total or 0 for i in produtos)
    base_servicos = sum(i.valor_total or 0 for i in servicos)
    desconto_servicos = desconto_dos_servicos(os_obj, base_servicos) if servicos else 0
    desconto_produtos = max(0, (os_obj.desconto or 0) - desconto_servicos) if produtos else 0

    docs = (
        db.query(DocumentoFiscal)
        .filter(DocumentoFiscal.origem_numero_os == numero_os)
        .order_by(DocumentoFiscal.id.desc())
        .all()
    )
    # A última tentativa de cada nota é a que vale (as anteriores ficam na gaveta).
    nfe = next((d for d in docs if d.tipo_documento in ("NFE", "NFCE")), None)
    nfse_por_papel: dict = {}
    for d in docs:
        if d.tipo_documento == "NFSE" and d.papel not in nfse_por_papel:
            nfse_por_papel[d.papel] = d

    return {
        "numero_os": numero_os,
        "finalizada": os_obj.status == OrdemServicoStatus.FINALIZADA,
        "total_os": os_obj.valor_total,
        "pecas": {
            "tem": bool(produtos),
            "valor": max(0, base_produtos - desconto_produtos),
            "modulo": _tem_modulo(db, "NFE"),
            "documento": _resumo_doc(nfe),
        },
        "servico": {
            "tem": bool(servicos),
            "valor": max(0, base_servicos - desconto_servicos),
            "modulo": _tem_modulo(db, "NFSE"),
            "documentos": [_resumo_doc(d) for d in nfse_por_papel.values()],
        },
    }
