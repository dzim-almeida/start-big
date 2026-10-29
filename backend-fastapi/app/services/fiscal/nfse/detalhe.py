# ---------------------------------------------------------------------------
# ARQUIVO: services/fiscal/nfse/detalhe.py
# DESCRIÇÃO: O detalhe de uma NFS-e para a gaveta da aba NFS-e: o motivo
#            inteiro, o que fazer, os itens e as tentativas anteriores.
# ---------------------------------------------------------------------------
"""
Pedido do Alan em 29/10/2026: a linha mostrava "Empresa não habilitada para
emissão de NFSe no am…" cortado, sem como ver o resto nem o que fazer — na
aba NF-e, clicar na linha abre a gaveta com tudo isso.

Só leitura. A `dica` traduz as recusas que já se conhece em uma ação ("peça
ao suporte para ligar…"); as outras vêm só com o motivo da emissora.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.core.busca import normalizar
from app.db.crud import fiscal as crud
from app.db.models.documento_fiscal import DocumentoFiscal

# (trecho do motivo, sem acento nem caixa) → o que o lojista faz. A primeira que casar vale.
DICAS: tuple[tuple[str, str], ...] = (
    ("nao habilitada para emissao de nfse",
     "A NFS-e ainda não está ligada na emissora para este ambiente. Peça ao suporte StartBig para ativar "
     "(ou reenvie o certificado em Centro Fiscal › Configurações) e emita de novo."),
    ("certificado",
     "Problema com o certificado digital. Confira a validade e reenvie em Centro Fiscal › Configurações."),
    ("tributacao nacional",
     "O código de tributação nacional do serviço foi recusado. Revise o cadastro do serviço e emita de novo."),
    ("nbs",
     "O NBS do serviço foi recusado. Revise o cadastro do serviço (o NBS sugerido para o código) e emita de novo."),
    ("inscricao municipal",
     "A inscrição municipal da empresa foi recusada. Confira em Dados da Empresa."),
)

DICA_SEM_RETORNO = (
    "A emissora ainda não respondeu. Use “Consultar” em instantes: nunca emita de novo por cima, "
    "a nota pode já ter saído."
)
DICA_GERAL = "Corrija o que o motivo aponta e emita de novo: sai uma nova tentativa, sem gastar número."


def dica_para(status: str, motivo: Optional[str]) -> Optional[str]:
    if status in ("PROCESSANDO", "INDETERMINADA"):
        return DICA_SEM_RETORNO
    if status not in ("REJEITADA", "NAO_TRANSMITIDA", "ERRO"):
        return None
    texto = normalizar(motivo or "")
    for trecho, dica in DICAS:
        if trecho in texto:
            return dica
    return DICA_GERAL


def _resumo(doc) -> dict:
    return {
        "id": doc.id,
        "status": doc.status,
        "motivo": doc.mensagem_sefaz or doc.motivo_rejeicao,
        "data": doc.data_emissao.isoformat() if doc.data_emissao else None,
        "ref": doc.ref_api,
    }


def detalhe_nfse(db: Session, documento_id: int) -> Optional[dict]:
    doc = crud.get_documento_fiscal(db, documento_id)
    if not doc or doc.tipo_documento != "NFSE":
        return None

    motivo = doc.mensagem_sefaz or doc.motivo_rejeicao
    # Tentativas anteriores da mesma nota: a NFS-e da OS tenta de novo com outra
    # `ref` (os-158-nfse-2), sem ligar `tentativa_anterior` -- então são as
    # outras NFS-e da mesma OS e do mesmo papel, mais antigas que esta.
    anteriores = []
    if doc.origem_numero_os:
        outras = (
            db.query(DocumentoFiscal)
            .filter(
                DocumentoFiscal.tipo_documento == "NFSE",
                DocumentoFiscal.origem_numero_os == doc.origem_numero_os,
                DocumentoFiscal.papel == doc.papel,
                DocumentoFiscal.id < doc.id,
            )
            .order_by(DocumentoFiscal.id.desc())
            .limit(10)
            .all()
        )
        anteriores = [_resumo(o) for o in outras]

    return {
        "id": doc.id,
        "status": doc.status,
        "status_focus": doc.status_focus,
        "origem": doc.origem_tipo,
        "numero_os": doc.origem_numero_os,
        "numero": doc.numero_documento,
        "codigo_verificacao": doc.codigo_verificacao,
        "chave_acesso": doc.chave_acesso,
        "ref": doc.ref_api,
        "ambiente": doc.ambiente_emissao,
        "valor_total": doc.valor_total,
        "tomador": doc.destinatario_nome_enviado,
        "tomador_documento": doc.destinatario_documento_enviado,
        "motivo": motivo,
        "codigo_status": doc.codigo_status_sefaz,
        "dica": dica_para(doc.status, motivo),
        "url_pdf": doc.url_pdf,
        "url_xml": doc.url_xml,
        "url_consulta": doc.url_consulta,
        "data_emissao": doc.data_emissao.isoformat() if doc.data_emissao else None,
        "data_autorizacao": doc.data_autorizacao.isoformat() if doc.data_autorizacao else None,
        "itens": [
            {"descricao": i.descricao, "codigo": i.codigo_produto, "valor": i.valor_bruto,
             "desconto": getattr(i, "valor_desconto", 0) or 0}
            for i in (doc.itens or [])
        ],
        "tentativas_anteriores": anteriores,
    }
