# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fabrica/calculo.py
# DESCRIÇÃO: Conversão consumo → unidade de compra da marcenaria-fábrica
#            (docs/marcenaria-fabrica-plano.md, §5; RC01, RC02, RNC04).
# ---------------------------------------------------------------------------
"""
Funções PURAS, só inteiros: o orçamento fala em mm² e mm, o estoque em chapa e
rolo. Erro aqui compra a menos ou a mais em silêncio, então nada de float — a
divisão arredondada para cima é `-(-a // b)`.

Unidades:
- consumo / consumo_por_unidade: mm² (M2), mm (M) ou unidades (UN);
- perda_bp: pontos-base, 1000 = 10%;
- custo: centavos POR UNIDADE DE COMPRA (por chapa, por rolo).
"""

from dataclasses import dataclass

UNIDADES_CONSUMO = ("M2", "M", "UN")

PERDA_MAXIMA_BP = 5000  # 50%: acima disso é erro de digitação, não perda
BASE_BP = 10000


def _ceil_div(a: int, b: int) -> int:
    return -(-a // b)


def consumo_com_perda(consumo: int, perda_bp: int, sofre_perda: bool) -> int:
    """⌈ consumo × (1 + perda) ⌉, só para insumo que sofre perda (DC3)."""
    if consumo < 0:
        raise ValueError("consumo negativo")
    if not 0 <= perda_bp <= PERDA_MAXIMA_BP:
        raise ValueError("perda fora de 0% a 50%")
    if not sofre_perda or perda_bp == 0:
        return consumo
    return _ceil_div(consumo * (BASE_BP + perda_bp), BASE_BP)


def quantidade_de_compra(consumo_total: int, consumo_por_unidade: int) -> int:
    """⌈ consumo ÷ rendimento da unidade ⌉ — chapas, rolos, unidades inteiras (D3)."""
    if consumo_por_unidade <= 0:
        raise ValueError("consumo_por_unidade precisa ser maior que zero")
    if consumo_total < 0:
        raise ValueError("consumo negativo")
    return _ceil_div(consumo_total, consumo_por_unidade)


def custo_do_material(
    consumo: int,
    perda_bp: int,
    sofre_perda: bool,
    consumo_por_unidade: int,
    custo_unitario: int,
) -> int:
    """Custo da FRAÇÃO de chapa que um móvel usa, em centavos (meio para cima).

    Não arredonda a chapa: a chapa é dividida entre os móveis no corte, e a
    sobra do arredondamento volta ao estoque (DC7). É o custo do MÓVEL, não o
    da compra.
    """
    if consumo_por_unidade <= 0:
        raise ValueError("consumo_por_unidade precisa ser maior que zero")
    usado = consumo_com_perda(consumo, perda_bp, sofre_perda)
    # round half up em inteiro: ⌊(2·a + b) ÷ 2b⌋
    return (2 * usado * custo_unitario + consumo_por_unidade) // (2 * consumo_por_unidade)


@dataclass(frozen=True)
class LinhaDeMaterial:
    produto_id: int
    consumo: int
    sofre_perda: bool
    consumo_por_unidade: int


def quantidades_por_insumo(linhas: list[LinhaDeMaterial], perda_bp: int) -> dict[int, int]:
    """Soma o consumo de cada insumo em TODOS os móveis e só então arredonda.

    Três móveis de 1 m² cabem numa chapa: arredondar por móvel compraria três
    (plano, §2). Devolve {produto_id: unidades de compra}.
    """
    total: dict[int, int] = {}
    rendimento: dict[int, int] = {}
    for linha in linhas:
        total[linha.produto_id] = total.get(linha.produto_id, 0) + consumo_com_perda(
            linha.consumo, perda_bp, linha.sofre_perda
        )
        rendimento[linha.produto_id] = linha.consumo_por_unidade
    return {pid: quantidade_de_compra(t, rendimento[pid]) for pid, t in total.items()}
