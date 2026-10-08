# ---------------------------------------------------------------------------
# ARQUIVO: app/core/regras_preco.py
# DESCRIÇÃO: Regras de preço por quantidade (R1, R2, R3) — conta pura, sem banco.
# ---------------------------------------------------------------------------
"""
Plano de embalagens, §6.1 (fase 5). Recebe "quantas unidades avulsas do
produto estão no carrinho, a que preço" e devolve a regra que vale, ou None.

- R1 — avulsas que completam uma embalagem cobram o preço dela. Fardo de 15 por
  R$ 50,00 e unidade a R$ 4,50: 17 latas = R$ 50,00 + 2 × R$ 4,50 = R$ 59,00.
  Vira DESCONTO da regra (R$ 17,50): R$ 59,00 ÷ 17 não existe em centavos.
- R2 — "a partir de N un, cada uma sai por X". Muda o PREÇO da unidade
  (centavos exatos, vai no vUnCom da nota).
- R3 — "leve X, pague Y". Vira DESCONTO da regra (o jeito que a SEFAZ aceita
  de dizer "levou 3, pagou 2").

Uma regra por produto — nunca somam. Quando mais de uma serve (D17), o dono
escolhe: o menor total para o cliente (padrão) ou a ordem que ele definiu.
Uma regra que não baixa o total não conta como candidata.
"""
from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable, Optional, Sequence

REGRAS = ("R1", "R2", "R3")
MENOR_PRECO = "MENOR_PRECO"
ORDEM = "ORDEM"


@dataclass(frozen=True)
class EmbalagemR1:
    sigla: str
    fator: int
    preco: int  # centavos, já resolvido (próprio, % ou fator × unidade)


@dataclass(frozen=True)
class FaixaR2:
    quantidade: int  # a partir de N un
    preco: int  # centavos por unidade


@dataclass(frozen=True)
class LevePagueR3:
    leve: int
    pague: int


@dataclass(frozen=True)
class Resultado:
    regra: str  # R1, R2, R3
    total: int  # total das unidades com a regra (centavos)
    desconto: int  # R1/R3: quanto sai do cheio. R2: 0
    preco_unitario: Optional[int]  # R2: o novo preço da unidade. R1/R3: None
    descricao: str  # o que a linha mostra


def reais(centavos: int) -> str:
    """R$ 1.234,56 — só para a descrição da linha."""
    inteiro, cent = divmod(abs(centavos), 100)
    return f"R$ {inteiro:,}".replace(",", ".") + f",{cent:02d}"


def _r1(unidades: int, preco_unidade: int, embalagens: Iterable[EmbalagemR1]) -> Optional[Resultado]:
    # Só entra embalagem que sai mais barata que as unidades soltas. A de melhor
    # preço por unidade é usada primeiro; no empate, a maior.
    uteis = sorted(
        (e for e in embalagens if e.fator >= 2 and e.preco < e.fator * preco_unidade),
        key=lambda e: (Fraction(e.preco, e.fator), -e.fator),
    )
    restante, total, partes = unidades, 0, []
    for emb in uteis:
        n, restante = divmod(restante, emb.fator)
        if n:
            total += n * emb.preco
            partes.append(f"{n} {emb.sigla} ({emb.fator} un)")
    if not partes:
        return None
    total += restante * preco_unidade
    cheio = unidades * preco_unidade
    return Resultado("R1", total, cheio - total, None, ("Preço de " + " + ".join(partes))[:80])


def _r2(unidades: int, preco_unidade: int, faixas: Iterable[FaixaR2]) -> Optional[Resultado]:
    # De todas as faixas alcançadas, a de menor preço — com faixas em escada
    # (6 → 3,80; 24 → 3,50) é a de maior quantidade, como o mercado faz.
    alcancadas = [f for f in faixas if f.quantidade >= 2 and unidades >= f.quantidade and f.preco < preco_unidade]
    if not alcancadas:
        return None
    faixa = min(alcancadas, key=lambda f: (f.preco, -f.quantidade))
    descricao = f"A partir de {faixa.quantidade} un: {reais(faixa.preco)}"
    return Resultado("R2", unidades * faixa.preco, 0, faixa.preco, descricao)


def _r3(unidades: int, preco_unidade: int, promocoes: Iterable[LevePagueR3]) -> Optional[Resultado]:
    melhor: Optional[Resultado] = None
    for promo in promocoes:
        if promo.pague < 1 or promo.leve <= promo.pague:
            continue
        gratis = (unidades // promo.leve) * (promo.leve - promo.pague)
        if not gratis:
            continue
        desconto = gratis * preco_unidade
        if melhor is None or desconto > melhor.desconto:
            descricao = f"Leve {promo.leve}, pague {promo.pague}: {gratis} grátis"
            melhor = Resultado("R3", unidades * preco_unidade - desconto, desconto, None, descricao)
    return melhor


def calcular(
    unidades: int,
    preco_unidade: int,
    *,
    embalagens: Iterable[EmbalagemR1] = (),
    faixas: Iterable[FaixaR2] = (),
    leve_pague: Iterable[LevePagueR3] = (),
    conflito: str = MENOR_PRECO,
    ordem: Sequence[str] = REGRAS,
) -> Optional[Resultado]:
    """A regra que vale para `unidades` avulsas a `preco_unidade`, ou None.

    Quem chama só passa as regras LIGADAS pela loja (e vigentes): regra que
    não chegou aqui não existe.
    """
    if unidades < 2 or preco_unidade <= 0:
        return None
    cheio = unidades * preco_unidade
    candidatos = {
        r.regra: r
        for r in (
            _r1(unidades, preco_unidade, embalagens),
            _r2(unidades, preco_unidade, faixas),
            _r3(unidades, preco_unidade, leve_pague),
        )
        if r is not None and r.total < cheio
    }
    if not candidatos:
        return None
    # Ordem incompleta (config antiga ou mexida à mão) completa com a padrão.
    ordem = list(dict.fromkeys([r for r in ordem if r in REGRAS] + list(REGRAS)))
    if conflito == ORDEM:
        return next(candidatos[r] for r in ordem if r in candidatos)
    posicao = {r: i for i, r in enumerate(ordem)}
    return min(candidatos.values(), key=lambda r: (r.total, posicao.get(r.regra, 9)))
