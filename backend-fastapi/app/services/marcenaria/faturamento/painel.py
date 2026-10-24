# ---------------------------------------------------------------------------
# ARQUIVO: app/services/marcenaria/faturamento/painel.py
# DESCRICAO: O faturamento de UMA OS da marcenaria, para a tela: cada movel
#            aprovado, se esta pronto, no estoque ou em que nota saiu
#            (docs/marcenaria-faturamento-plano.md, F3).
# ---------------------------------------------------------------------------

from typing import Any

from sqlalchemy.orm import Session

from app.db.models.documento_fiscal import DocumentoFiscal
from app.services.marcenaria import producao
from app.services.marcenaria.faturamento import DESLIGADO, empresa_atual_id
from app.services.marcenaria.faturamento.estoque_acabado import linhas_da_os
from app.services.marcenaria.orcamento_comum import os_e_orcamento_aprovado

MSG_SEM_ORCAMENTO = "Esta OS não veio de um orçamento de marcenaria aprovado."


def _documento(doc: DocumentoFiscal) -> dict[str, Any]:
    return {
        "id": doc.id, "numero": doc.numero_documento, "serie": doc.serie, "status": doc.status,
        "chave_acesso": doc.chave_acesso, "valor_total": doc.valor_total,
        "data_emissao": doc.data_emissao, "mensagem": doc.mensagem_sefaz, "papel": doc.papel,
    }


def ler(db: Session, numero_os: str) -> dict[str, Any]:
    """GET /marcenaria/os/{numero_os}/faturamento."""
    from app.db.crud.configuracao.marcenaria import get_configuracao_marcenaria

    os_, orc = os_e_orcamento_aprovado(db, numero_os, MSG_SEM_ORCAMENTO)
    config = get_configuracao_marcenaria(db, empresa_atual_id(db))
    modo = config.faturamento_modo if config is not None else DESLIGADO
    linhas = linhas_da_os(db, os_.id)
    docs = {d.id: d for d in db.query(DocumentoFiscal).filter(
        DocumentoFiscal.origem_tipo == "OS", DocumentoFiscal.origem_id == os_.id).all()}

    entrega_futura = modo == "ENTREGA_FUTURA"
    sf_por_movel = {m.id: docs.get(m.simples_faturamento_id) for a in orc.ambientes for m in a.moveis
                    if m.aprovado and m.simples_faturamento_id}
    moveis = []
    for linha_producao in producao.montar_producao(db, os_, orc)["moveis"]:
        movel_id = linha_producao["movel_id"]
        linha = linhas.get(movel_id)
        situacao = linha.situacao if linha is not None and linha.situacao != "ESTORNADO" else None
        doc = docs.get(linha.documento_fiscal_id) if linha is not None and linha.documento_fiscal_id else None
        sf = sf_por_movel.get(movel_id)
        sf_autorizado = sf is not None and sf.status == "AUTORIZADA"
        moveis.append({
            "movel_id": movel_id,
            "nome": linha_producao["nome"],
            "ambiente": linha_producao["ambiente"],
            "quantidade": linha_producao["quantidade"],
            "pronto": linha_producao["pronto"],
            "situacao": situacao,                         # None | NO_ESTOQUE | FATURADO
            # Entrega futura: a remessa so sai com o simples faturamento autorizado.
            "pode_faturar": modo != DESLIGADO and situacao == "NO_ESTOQUE" and (sf_autorizado or not entrega_futura),
            "documento": _documento(doc) if doc is not None else None,
            "simples_faturamento": _documento(sf) if sf is not None else None,
        })
    vivos = ("AUTORIZADA", "PROCESSANDO", "INDETERMINADA")
    return {
        "numero_os": os_.numero_os,
        "faturamento_modo": modo,
        "instalacao_modo": config.instalacao_modo if config is not None else "EMBUTIDA",
        "moveis": moveis,
        "notas": [_documento(d) for d in sorted(docs.values(), key=lambda d: d.id)],
        # Entrega futura: falta simples faturamento para algum movel? (o aditivo ganha o seu)
        "falta_simples_faturamento": entrega_futura and any(
            m["simples_faturamento"] is None or m["simples_faturamento"]["status"] not in vivos for m in moveis),
    }
