# ---------------------------------------------------------------------------
# ARQUIVO: services/venda/guarda_fiscal.py
# DESCRICAO: Venda - trava fiscal: venda com documento fiscal ativo (autorizado,
#            em processamento ou indeterminado) nao se altera.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from app.db.models.venda import Venda
from app.db.models.documento_fiscal import DocumentoFiscal
from fastapi import HTTPException, status


# Estados de DocumentoFiscal que impedem mexer na venda de origem.
# AUTORIZADA: a nota vale na SEFAZ.
# PROCESSANDO/PENDENTE: a resposta ainda vem, pode virar autorizada.
# INDETERMINADA: nao sabemos se foi autorizada -- tratar como se fosse.
_STATUS_FISCAIS_BLOQUEANTES = ("AUTORIZADA", "PROCESSANDO", "PENDENTE", "INDETERMINADA")


def _documento_fiscal_bloqueante(db: Session, sale_in_db: Venda) -> DocumentoFiscal | None:
    """Retorna o documento fiscal que impede alterar esta venda, se houver."""
    # Venda ainda nao finalizada nao tem numero_venda e nao pode ter documento.
    identificadores = [i for i in (sale_in_db.numero_venda, sale_in_db.id) if i is not None]
    if not identificadores:
        return None

    return (
        db.query(DocumentoFiscal)
        .filter(
            DocumentoFiscal.origem_tipo == "VENDA",
            DocumentoFiscal.origem_id.in_(identificadores),
            DocumentoFiscal.status.in_(_STATUS_FISCAIS_BLOQUEANTES),
        )
        .first()
    )


def _assert_sem_documento_fiscal_ativo(db: Session, sale_in_db: Venda, acao: str) -> None:
    """
    Barra qualquer alteracao em venda que ja tenha nota fiscal viva.

    Sem isso, o operador cancela a venda no PDV -- estornando caixa e estoque --
    enquanto a nota continua valida na SEFAZ. O resultado e omissao de receita
    e passivo tributario para o cliente.
    """
    doc = _documento_fiscal_bloqueante(db, sale_in_db)
    if not doc:
        return

    if doc.status == "AUTORIZADA":
        motivo = (
            f"Esta venda possui NF-e autorizada (No {doc.numero_documento}, "
            f"Serie {doc.serie}). Cancele a nota na SEFAZ antes de {acao}."
        )
        codigo = "NF_AUTORIZADA"
    elif doc.status == "INDETERMINADA":
        motivo = (
            "A emissao desta venda nao teve retorno confirmado da SEFAZ e a nota "
            f"pode estar autorizada. Consulte o documento antes de {acao}."
        )
        codigo = "NF_INDETERMINADA"
    else:
        motivo = (
            "Esta venda possui uma emissao em andamento. Aguarde o retorno da "
            f"SEFAZ antes de {acao}."
        )
        codigo = "NF_EM_PROCESSAMENTO"

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={"codigo": codigo, "mensagem": motivo, "documento_id": doc.id},
    )
