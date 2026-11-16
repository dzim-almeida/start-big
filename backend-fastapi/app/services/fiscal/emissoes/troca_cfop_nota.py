# ---------------------------------------------------------------------------
# ARQUIVO: services/fiscal/emissoes/troca_cfop_nota.py
# DESCRIÇÃO: O CFOP trocado na conferência, do lado da emissão: grupos da
#            prévia, natureza, rastro no documento e "usar como padrão"
#            (docs/nfe-cfop-e-notas-da-os-plano.md, C1).
# ---------------------------------------------------------------------------
"""
A regra da troca (o que pode virar o quê, o que acompanha) está em
`derivacao/troca_cfop.py` e é aplicada no resolver. Aqui fica o que só a
emissão sabe: o payload, o documento e o usuário.

Venda e OS passam pelos mesmos quatro pontos, sempre só quando há troca:
sem `trocar_cfop` nada aqui muda o payload nem o documento.
"""
import json
import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.db.models.documento_fiscal import DocumentoFiscal
from app.db.models.produto_fiscal import ProdutoFiscal
from app.services.fiscal.derivacao.troca_cfop import (
    SUFIXO_SUBSTITUIDO,
    cfop_para_o_cadastro,
    descricao,
    natureza_da_nota,
    opcoes_de_troca,
)
from app.services.fiscal.tax_engine.types import ResultadoCalculo

logger = logging.getLogger(__name__)

# D4 só grava CFOP de VENDA no cadastro: remessa de entrega futura (x116/x117)
# no cadastro faria a venda comum sair como remessa.
_SUFIXOS_DE_CADASTRO = frozenset({"101", "102", "103", "104", "405", "107", "108"})


def grupos_cfop(resultado: Optional[ResultadoCalculo]) -> list[dict]:
    """Um campo por CFOP sugerido distinto, na ordem dos itens."""
    grupos: dict[str, dict] = {}
    for imp in (resultado.itens if resultado else []):
        if not imp.cfop:
            continue
        sugerido = imp.cfop_sugerido or imp.cfop
        grupo = grupos.setdefault(sugerido, {
            "cfop_sugerido": sugerido,
            "cfop": imp.cfop,
            "descricao": descricao(imp.cfop),
            "itens": [],
            "opcoes": [{"cfop": c, "descricao": descricao(c)} for c in opcoes_de_troca(sugerido)],
        })
        grupo["itens"].append(imp.numero_item)
    return list(grupos.values())


def houve_troca(resultado: Optional[ResultadoCalculo]) -> bool:
    return bool(resultado) and any(imp.cfop_sugerido for imp in resultado.itens)


def aplicar_natureza(payload: dict, resultado: Optional[ResultadoCalculo]) -> None:
    """D2: com troca e um CFOP só na nota, a natureza segue o CFOP escolhido."""
    if not houve_troca(resultado):
        return
    natureza = natureza_da_nota({imp.cfop for imp in resultado.itens if imp.cfop})
    if natureza:
        payload["natureza_operacao"] = natureza


def registrar(doc: DocumentoFiscal, resultado: Optional[ResultadoCalculo], usuario: Optional[str]) -> None:
    """O rastro: o que foi trocado e por quem. A reemissão lê daqui."""
    if not houve_troca(resultado):
        return
    trocas = {imp.cfop_sugerido: imp.cfop for imp in resultado.itens if imp.cfop_sugerido}
    doc.cfop_trocado = json.dumps({"trocas": trocas, "por": usuario}, ensure_ascii=False)


def trocas_do_documento(doc: Optional[DocumentoFiscal]) -> Optional[dict[str, str]]:
    """A troca que a tentativa anterior levou (a reemissão repete a mesma nota)."""
    bruto = getattr(doc, "cfop_trocado", None)
    if not bruto:
        return None
    try:
        return json.loads(bruto).get("trocas") or None
    except (ValueError, AttributeError):
        return None


def gravar_como_padrao(db: Session, venda: Any, resultado: Optional[ResultadoCalculo]) -> None:
    """
    D4: o CFOP escolhido vira o `cfop_padrao` dos produtos trocados.

    Só no cadastro PRÓPRIO do produto: quem herda da regra por NCM ou do padrão
    da loja não ganha uma linha nova por causa de uma nota. Entrar no 5405 ou
    sair dele leva a situação do ICMS junto, senão o cadastro fica incoerente.
    """
    if not houve_troca(resultado):
        return
    itens = list(getattr(venda, "itens", None) or [])
    for imp in resultado.itens:
        if not imp.cfop_sugerido or imp.cfop[1:] not in _SUFIXOS_DE_CADASTRO:
            continue
        if not (0 < imp.numero_item <= len(itens)):
            continue
        produto_id = getattr(itens[imp.numero_item - 1], "produto_id", None)
        fiscal = db.query(ProdutoFiscal).filter(ProdutoFiscal.produto_id == produto_id).first() if produto_id else None
        if fiscal is None:
            continue
        fiscal.cfop_padrao = cfop_para_o_cadastro(imp.cfop)
        cruzou_st = (imp.cfop_sugerido[1:] == SUFIXO_SUBSTITUIDO) != (imp.cfop[1:] == SUFIXO_SUBSTITUIDO)
        situacao = imp.icms_situacao_tributaria or ""
        if cruzou_st and len(situacao) == 3:
            fiscal.csosn = situacao
        elif cruzou_st and len(situacao) == 2:
            fiscal.cst_icms = situacao
        logger.info("[FISCAL] CFOP padrão do produto %s agora %s (troca na nota)", produto_id, fiscal.cfop_padrao)
