# ---------------------------------------------------------------------------
# ARQUIVO: app/core/segregacao_receita.py
# DESCRIÇÃO: Em que grupo do PGDAS-D cai a receita de um produto (conta pura).
# ---------------------------------------------------------------------------
"""
O PGDAS-D separa a receita de REVENDA por duas perguntas, e a resposta de cada
uma muda o DAS:

- **ICMS já pago por substituição tributária?** Se sim, a parte do ICMS sai do
  DAS sobre aquela receita. No cadastro: CSOSN 500 (Simples) ou CST 60 (regime
  normal) — "ICMS cobrado anteriormente por ST".
- **PIS/COFINS monofásico?** Se sim, a parte de PIS/COFINS sai do DAS. No
  cadastro: CST de PIS ou de COFINS 04 ("monofásica, revenda a alíquota zero").

A conta é sobre o cadastro, não sobre a lei: o sistema não decide se uma
bebida É ST no estado (ver `services/fiscal/derivacao/situacao.py`, que se
recusa a inferir isso). Produto sem o código que responde a pergunta do ICMS
volta como "sem classificação", para o lojista corrigir — chutar "normal"
faria a loja pagar ICMS duas vezes sem ninguém ver.
"""

from dataclasses import dataclass
from typing import Optional

# CRT 1 (Simples) e 4 (MEI) usam CSOSN; 2 e 3 usam CST.
CRT_QUE_USAM_CSOSN = frozenset({1, 4})

CSOSN_ST_RETIDO = "500"
CST_ST_RETIDO = "60"
CST_PIS_COFINS_MONOFASICO = "04"


@dataclass(frozen=True)
class Grupo:
    icms_st: bool
    monofasico: bool


def _limpo(codigo: Optional[str]) -> Optional[str]:
    codigo = (codigo or "").strip()
    return codigo or None


def classificar(
    crt: Optional[int],
    csosn: Optional[str],
    cst_icms: Optional[str],
    cst_pis: Optional[str],
    cst_cofins: Optional[str],
) -> Optional[Grupo]:
    """O grupo da receita, ou None quando o cadastro não responde a pergunta do ICMS.

    Com o CRT da loja, lê só o campo do regime dela (o outro pode ter sobrado
    de uma troca de regime). Sem CRT, usa o que estiver preenchido.
    """
    csosn, cst_icms = _limpo(csosn), _limpo(cst_icms)
    if crt in CRT_QUE_USAM_CSOSN:
        codigo, st = csosn, CSOSN_ST_RETIDO
    elif crt is not None:
        codigo, st = cst_icms, CST_ST_RETIDO
    else:
        codigo = csosn or cst_icms
        st = CSOSN_ST_RETIDO if csosn else CST_ST_RETIDO
    if codigo is None:
        return None

    # Basta um dos dois: na prática o contador marca os dois juntos, e um
    # só marcado já diz que a tributação foi concentrada na indústria.
    monofasico = CST_PIS_COFINS_MONOFASICO in (_limpo(cst_pis), _limpo(cst_cofins))
    return Grupo(icms_st=codigo == st, monofasico=monofasico)


def ratear(total: int, pesos: list[int]) -> list[int]:
    """Divide `total` centavos na proporção de `pesos`, somando exatamente `total`.

    Usado para espalhar o desconto da OS (que é da OS, não do item) pelos
    itens. A sobra do arredondamento vai para o maior peso.
    """
    soma = sum(pesos)
    if soma <= 0 or not pesos:
        return [0] * len(pesos)
    partes = [total * p // soma for p in pesos]
    partes[pesos.index(max(pesos))] += total - sum(partes)
    return partes
