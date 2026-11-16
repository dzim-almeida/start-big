# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/derivacao/troca_cfop.py
# DESCRIÇÃO: Trocar o CFOP na hora da nota, sem mexer no cadastro
#            (docs/nfe-cfop-e-notas-da-os-plano.md, C1).
# ---------------------------------------------------------------------------
"""
O CFOP escolhido na conferência da NF-e.

Pedido do Alan (01/11/2026): o sistema antigo da marcenaria deixa digitar o
CFOP na hora; aqui ele mora no cadastro do produto, e uma nota diferente
obrigava a editar o produto e lembrar de voltar.

COMO A TROCA É DITA
-------------------
`{"5102": "5101"}` = os itens que iam com 5102 vão com 5101. A chave é o CFOP
que o sistema SUGERIU (o de hoje), não o item: numa nota mista (peça sem ST
5102 + peça com ST 5405) cada grupo tem o seu campo, e um CFOP só por cima de
tudo levaria a peça com ST para o CSOSN 102 — nota aceita e errada (D1a).

O QUE PODE VIRAR O QUÊ
----------------------
Só dentro da mesma FAMÍLIA, que é o que impede trocar a operação de natureza:

  interna            5101 5102 5103 5104 5405
  fora, contribuinte 6101 6102 6103 6104
  fora, não contrib. 6107 6108
  entrega futura     x116 x117  (remessa da marcenaria)

O resto fica TRAVADO: 5922 (simples faturamento é o papel da nota), 6401/6403/
6404 (ST como substituto: decide o perfil tributário, e a tabela ainda espera o
contador — ver 37a0e7ed), 5933 e o que não estiver aqui. Família diferente por
construção também garante o 1º dígito certo (5 dentro, 6 fora): a troca nunca
contradiz o destino que o motor decidiu.

O QUE ACOMPANHA (D2)
--------------------
Entrar no 5405 ou sair dele muda a situação do ICMS junto (102↔500 no Simples,
00↔60 no regime normal). Fora disso a situação do produto é mantida. A natureza
da operação segue o CFOP quando a nota fica com um CFOP só.
"""
from typing import Optional

from .cfop import NATUREZA_POR_CFOP

SUFIXO_SUBSTITUIDO = "405"

# Situação do ICMS ao entrar no 5405 / ao sair dele.
CSOSN_SUBSTITUIDO = "500"
CSOSN_SEM_ST = "102"
CST_SUBSTITUIDO = "60"
CST_SEM_ST = "00"

FAMILIAS: tuple[frozenset[str], ...] = (
    frozenset({"5101", "5102", "5103", "5104", "5405"}),
    frozenset({"6101", "6102", "6103", "6104"}),
    frozenset({"6107", "6108"}),
    frozenset({"5116", "5117"}),
    frozenset({"6116", "6117"}),
)

# Descrição para a tela e para a natureza da operação. Sem acento, no mesmo
# formato de NATUREZA_POR_CFOP: é texto que vai para a SEFAZ.
DESCRICAO_CFOP: dict[str, str] = {
    **NATUREZA_POR_CFOP,
    "5103": "Venda de producao do estabelecimento fora do estabelecimento",
    "5104": "Venda de merc. adq. de terceiros fora do estabelecimento",
    "6103": "Venda de producao do estabelecimento fora do estabelecimento",
    "6104": "Venda de merc. adq. de terceiros fora do estabelecimento",
}


class TrocaCfopInvalidaError(ValueError):
    """A troca pedida mudaria a natureza da operação: recusa, não chuta."""


def opcoes_de_troca(cfop: Optional[str]) -> list[str]:
    """Os CFOPs que podem substituir `cfop` nesta nota (vazio = travado)."""
    for familia in FAMILIAS:
        if cfop in familia:
            return sorted(familia)
    return []


def descricao(cfop: str) -> str:
    return DESCRICAO_CFOP.get(cfop, "")


def validar_troca(de: str, para: str) -> None:
    if de == para:
        return
    opcoes = opcoes_de_troca(de)
    if not opcoes:
        raise TrocaCfopInvalidaError(
            f"O CFOP {de} não pode ser trocado na hora da nota: ele é decidido pela "
            f"operação (entrega futura, ST como substituto ou serviço)."
        )
    if para not in opcoes:
        raise TrocaCfopInvalidaError(
            f"O CFOP {para} não serve no lugar do {de} nesta nota. "
            f"Opções: {', '.join(opcoes)}."
        )


def situacao_apos_troca(
    de: str, para: str, simples: bool, csosn: Optional[str], cst_icms: Optional[str],
) -> tuple[Optional[str], Optional[str]]:
    """(csosn, cst_icms) depois da troca: só muda ao entrar no 5405 ou sair dele."""
    entra_st = para[1:] == SUFIXO_SUBSTITUIDO and de[1:] != SUFIXO_SUBSTITUIDO
    sai_st = de[1:] == SUFIXO_SUBSTITUIDO and para[1:] != SUFIXO_SUBSTITUIDO
    if not (entra_st or sai_st):
        return csosn, cst_icms
    if simples:
        return (CSOSN_SUBSTITUIDO if entra_st else CSOSN_SEM_ST), cst_icms
    return csosn, (CST_SUBSTITUIDO if entra_st else CST_SEM_ST)


def natureza_da_nota(cfops: set[str]) -> Optional[str]:
    """A natureza quando a nota ficou com um CFOP só; None = manter a de hoje."""
    if len(cfops) != 1:
        return None
    return DESCRICAO_CFOP.get(next(iter(cfops))) or None


# 6107/6108 são a 6101/6102 para não contribuinte: no cadastro mora o interno.
_SUFIXO_DO_CADASTRO = {"107": "101", "108": "102"}


def cfop_para_o_cadastro(cfop: str) -> str:
    """O CFOP que o cadastro do produto guarda (sempre o da operação interna)."""
    sufixo = cfop[1:]
    return f"5{_SUFIXO_DO_CADASTRO.get(sufixo, sufixo)}"
