# ---------------------------------------------------------------------------
# ARQUIVO: services/fiscal/nfse/substituicao.py
# DESCRIÇÃO: Substituir uma NFS-e autorizada (retificar), pela gaveta de
#            detalhe. O4 de docs/nfe-cfop-e-notas-da-os-plano.md.
# ---------------------------------------------------------------------------
"""
A NFS-e Nacional não tem carta de correção: nota errada se SUBSTITUI. Na
Focus não há rota própria — a substituta é uma emissão nova (`POST /v2/nfsen`)
com três campos da DPS (campos.focusnfe.com.br/nfse_nacional/EmissaoDPSXml):

  chave_nfse_substituida              chSubstda  chave da nota antiga
  codigo_justificativa_substituicao   cMotivo    01..05, 99 (MOTIVOS)
  motivo_substituicao                 xMotivo    15 a 255 caracteres

Como no "Tentar de novo", a substituta É a emissão da OS: relê a OS e o
cadastro, então o que o lojista corrigiu vai junto. Ela aponta a antiga por
`tentativa_anterior_id`.

A ANTIGA: no Sistema Nacional a substituição registra o cancelamento da nota
substituída. Aqui ela vira CANCELADA, com "Substituída pela NFS-e nº X", só
quando a substituta é AUTORIZADA (`concluir_substituicao`, chamado pelo
espelho da NFS-e, que roda na emissão e em toda consulta). Recusada a
substituta, a antiga continua valendo. ⚠️ A confirmar na 1ª homologação: que a
Focus devolve a antiga como "cancelado" numa consulta.

Fica de fora: rota municipal (a doc da Focus não tem substituição), avulsa
(não guarda o formulário) e a instalação da marcenaria.
"""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.crud import fiscal as crud
from app.db.models.documento_fiscal import DocumentoFiscal
from app.services.fiscal.nfse.marcenaria import PAPEL_INSTALACAO
from app.services.fiscal.nfse.nova_tentativa import STATUS_RECUSADA, tentativa_mais_nova

MOTIVOS = {
    "01": "Desenquadramento do Simples Nacional",
    "02": "Enquadramento no Simples Nacional",
    "03": "Inclusão retroativa de imunidade/isenção",
    "04": "Exclusão retroativa de imunidade/isenção",
    "05": "Rejeição da nota pelo tomador",
    "99": "Outros",
}
DESCRICAO_MIN = 15
DESCRICAO_MAX = 255


def _recusa(codigo: str, mensagem: str, http: int = status.HTTP_422_UNPROCESSABLE_ENTITY) -> HTTPException:
    return HTTPException(status_code=http, detail={"codigo": codigo, "mensagem": mensagem})


def motivo_para_nao_substituir(db: Session, doc: DocumentoFiscal, rota=None) -> Optional[HTTPException]:
    """None = pode substituir; senão, a recusa que a rota devolveria."""
    if doc.status != "AUTORIZADA":
        return _recusa("NFSE_NAO_AUTORIZADA", "Só a NFS-e autorizada pode ser substituída.")
    if not doc.origem_numero_os:
        return _recusa("NFSE_AVULSA", "A NFS-e avulsa não guarda o formulário: cancele e emita uma nova.")
    if doc.papel == PAPEL_INSTALACAO:
        return _recusa("NFSE_INSTALACAO", "A NFS-e da instalação ainda não tem substituição: cancele e emita de novo.")
    if rota is not None and rota.municipal:
        return _recusa("NFSE_MUNICIPAL", "A substituição existe só na NFS-e Nacional. Na da prefeitura, cancele e emita de novo.")
    if not doc.chave_acesso:
        return _recusa(
            "NFSE_SEM_CHAVE",
            "Esta NFS-e não tem a chave de acesso gravada. Use “Consultar” e tente de novo.",
        )
    # Uma substituta RECUSADA não conta: a antiga continua valendo e pode ser
    # substituída de novo (corrigido o que a prefeitura recusou).
    nova = tentativa_mais_nova(db, doc)
    if nova is not None and nova.status not in STATUS_RECUSADA:
        return _recusa(
            "NFSE_JA_TEM_TENTATIVA_NOVA", "Esta OS já tem uma NFS-e mais nova desta nota.",
            http=status.HTTP_409_CONFLICT,
        )
    return None


def pode_substituir(db: Session, doc: DocumentoFiscal) -> bool:
    """Para o botão da gaveta. A rota é conferida de novo na hora de substituir."""
    return motivo_para_nao_substituir(db, doc) is None


def campos_da_dps(antiga: DocumentoFiscal, motivo: str, descricao: str) -> dict:
    return {
        "chave_nfse_substituida": antiga.chave_acesso,
        "codigo_justificativa_substituicao": motivo,
        "motivo_substituicao": descricao,
    }


def substituir_nfse(
    db: Session, documento_id: int, empresa_id: int, motivo: str, descricao: str,
    confirmar_duplicidade: bool = False,
) -> DocumentoFiscal:
    from app.services.fiscal.nfse.emissao_os import emitir_nfse_os
    from app.services.fiscal.nfse.rota import rota_da_empresa

    antiga = crud.get_documento_fiscal(db, documento_id)
    if not antiga or antiga.tipo_documento != "NFSE":
        raise HTTPException(status_code=404, detail="NFS-e não encontrada.")
    if motivo not in MOTIVOS:
        raise _recusa("NFSE_MOTIVO_INVALIDO", f"Motivo da substituição inválido. Use um de: {', '.join(MOTIVOS)}.")
    descricao = (descricao or "").strip()
    if not DESCRICAO_MIN <= len(descricao) <= DESCRICAO_MAX:
        raise _recusa(
            "NFSE_DESCRICAO_INVALIDA",
            f"Explique a substituição em {DESCRICAO_MIN} a {DESCRICAO_MAX} caracteres.",
        )
    recusa = motivo_para_nao_substituir(db, antiga, rota_da_empresa(db, empresa_id))
    if recusa is not None:
        raise recusa

    codigo = (antiga.papel or "").split(":", 1)[1] if (antiga.papel or "").startswith("NFSE:") else None
    return emitir_nfse_os(
        db, antiga.origem_numero_os, empresa_id,
        tentativa_anterior_id=antiga.id, confirmar_duplicidade=confirmar_duplicidade,
        codigo_nacional=codigo, substituindo=antiga,
        campos_extra=campos_da_dps(antiga, motivo, descricao),
    )


def eh_substituicao(db: Session, doc: DocumentoFiscal) -> bool:
    """Esta NFS-e foi emitida para substituir outra (a anterior está AUTORIZADA)."""
    if doc.tipo_documento != "NFSE" or not doc.tentativa_anterior_id:
        return False
    anterior = db.get(DocumentoFiscal, doc.tentativa_anterior_id)
    return anterior is not None and anterior.tipo_documento == "NFSE" and anterior.status == "AUTORIZADA"


def concluir_substituicao(db: Session, doc: DocumentoFiscal) -> None:
    """
    Substituta autorizada: a antiga sai de cena como CANCELADA.

    Reconhece a substituição pelo par (esta AUTORIZADA, a anterior AUTORIZADA):
    no "Tentar de novo" a anterior é sempre uma recusada, então não confunde.
    Idempotente: na segunda consulta a anterior já está cancelada.
    """
    if doc.tipo_documento != "NFSE" or doc.status != "AUTORIZADA" or not doc.tentativa_anterior_id:
        return
    antiga = db.get(DocumentoFiscal, doc.tentativa_anterior_id)
    if antiga is None or antiga.tipo_documento != "NFSE" or antiga.status != "AUTORIZADA":
        return
    antiga.status = "CANCELADA"
    antiga.mensagem_sefaz = f"Substituída pela NFS-e nº {doc.numero_documento or '—'}."
