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

E a mensagem para mandar a nota ao cliente pelo WhatsApp (O2).

Cancelar pela OS (O1 de docs/nfe-cfop-e-notas-da-os-plano.md): cada nota diz
se ainda dá para cancelar (`pode_cancelar`) e até quando (`cancelar_ate`).
A tela não calcula prazo: a régua é a mesma do cancelamento
(`JANELA_CANCELAMENTO_POR_TIPO`). NFS-e não tem prazo aqui -- é de cada
município, e quem recusa fora dele é o Sistema Nacional.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.enum import OrdemServicoStatus
from app.core.modulos import requer_modulo
from app.db.crud import fiscal as crud
from app.db.models.documento_fiscal import DocumentoFiscal
from app.services.fiscal.emissoes.adaptador_os import itens_de_produto
from app.services.fiscal.eventos.consulta_cancelamento import JANELA_CANCELAMENTO_POR_TIPO
from app.services.fiscal.nfse.payload import desconto_dos_servicos, servicos_da_os


def _tem_modulo(db: Session, identificador: str) -> bool:
    try:
        requer_modulo(identificador)(db=db)
        return True
    except HTTPException:
        return False


def _cancelar_ate(doc: DocumentoFiscal) -> Optional[datetime]:
    """Fim do prazo legal de cancelamento (NF-e/NFC-e); None = sem prazo nosso."""
    janela = JANELA_CANCELAMENTO_POR_TIPO.get(doc.tipo_documento)
    if janela is None or doc.data_autorizacao is None:
        return None
    autorizacao = doc.data_autorizacao
    if autorizacao.tzinfo is None:
        autorizacao = autorizacao.replace(tzinfo=timezone.utc)
    return autorizacao + janela


def _resumo_doc(doc: Optional[DocumentoFiscal]) -> Optional[dict]:
    if doc is None:
        return None
    ate = _cancelar_ate(doc) if doc.status == "AUTORIZADA" else None
    return {
        "id": doc.id,
        "status": doc.status,
        "numero": doc.numero_documento,
        "motivo": doc.mensagem_sefaz or doc.motivo_rejeicao,
        "url_pdf": doc.url_pdf,
        "valor": doc.valor_total,
        "papel": doc.papel,
        "pode_cancelar": doc.status == "AUTORIZADA" and (ate is None or datetime.now(timezone.utc) < ate),
        "cancelar_ate": ate.isoformat() if ate else None,
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
    from app.services.fiscal.nfse.nova_tentativa import STATUS_RECUSADA
    from app.services.fiscal.nfse.substituicao import eh_substituicao

    nfse_por_papel: dict = {}
    for d in docs:
        if d.tipo_documento != "NFSE" or d.papel in nfse_por_papel:
            continue
        # Substituta recusada: a nota que vale é a original, ainda autorizada.
        if d.status in STATUS_RECUSADA and eh_substituicao(db, d):
            continue
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


# ---------------------------------------------------------------------------
# Mandar a nota ao cliente (O2 de docs/nfe-cfop-e-notas-da-os-plano.md)
# ---------------------------------------------------------------------------

# O PDF da NF-e mora na plataforma e só abre com o token da loja: link dele
# para o cliente daria tela de login. O DANFSe da NFS-e Nacional é um link
# público do S3 da Focus (ver `client_startbig._headers_do_arquivo`).
HOST_DA_PLATAFORMA = "api.startbig.com.br"
PORTAL_NFE = "www.nfe.fazenda.gov.br"


def _reais(centavos: Optional[int]) -> str:
    inteiro, resto = divmod(int(centavos or 0), 100)
    return f"R$ {inteiro:,}".replace(",", ".") + f",{resto:02d}"


def _nome_do_cliente(cliente) -> str:
    return (
        getattr(cliente, "nome", None)
        or getattr(cliente, "nome_fantasia", None)
        or getattr(cliente, "razao_social", None)
        or ""
    ).strip()


def _link_publico(url: Optional[str]) -> Optional[str]:
    if not url or not url.startswith("https://") or HOST_DA_PLATAFORMA in url:
        return None
    return url


def mensagem_whatsapp(db: Session, numero_os: str, documento_id: int) -> Optional[dict]:
    """
    Texto da nota para o WhatsApp do cliente, e o número dele (com 55).

    Só nota AUTORIZADA desta OS. NF-e vai com a chave de acesso (o cliente
    consulta no portal); NFS-e com o link do DANFSe quando ele é público e o
    código de verificação. `telefone` nulo = cliente sem celular: a tela copia
    o texto. None = OS ou nota não encontrada.
    """
    from app.services.compras.pedidos import telefone_whatsapp

    os_obj = crud.get_os_completa(db, numero_os)
    doc = db.get(DocumentoFiscal, documento_id)
    if not os_obj or doc is None or doc.origem_numero_os != numero_os:
        return None
    if doc.status != "AUTORIZADA":
        raise HTTPException(status_code=422, detail="Só nota autorizada pode ser mandada ao cliente.")

    cliente = getattr(os_obj.objeto, "cliente", None) if os_obj.objeto else None
    nome = _nome_do_cliente(cliente)
    tipo = "NFS-e" if doc.tipo_documento == "NFSE" else "NF-e"
    linhas = [
        f"Olá{', ' + nome.split()[0] if nome else ''}! Segue a {tipo} nº {doc.numero_documento or '—'} "
        f"da {numero_os}, no valor de {_reais(doc.valor_total)}.",
    ]
    if doc.tipo_documento == "NFSE":
        # A consulta no portal vale mais que o PDF da emissora: abre sem login e
        # não expira (mesma preferência do espelho da NFS-e).
        consulta = _link_publico(doc.url_consulta)
        if consulta:
            linhas.append(f"Nota no portal: {consulta}")
        elif _link_publico(doc.url_pdf):
            linhas.append(f"PDF da nota: {doc.url_pdf}")
        if doc.codigo_verificacao:
            linhas.append(f"Código de verificação: {doc.codigo_verificacao}")
    elif doc.chave_acesso:
        linhas.append(f"Chave de acesso: {doc.chave_acesso}")
        linhas.append(f"Consulte em {PORTAL_NFE}")

    return {"texto": "\n".join(linhas), "telefone": telefone_whatsapp(cliente)}

