# ---------------------------------------------------------------------------
# ARQUIVO: app/services/compras/necessidade.py
# DESCRIÇÃO: Contas do módulo de Compras — funções PURAS, sem banco.
# ---------------------------------------------------------------------------
"""
Pura de propósito (plano, §6; RNC04 do resumo da marcenaria): é o coração da
tela de Necessidades, e um erro aqui compra a mais ou deixa faltar em silêncio.
Sem banco, cada regra vira teste de uma linha (test/services/compras/).

CONVENÇÕES (plano, D3):
- dinheiro em centavos, inteiro;
- quantidade a comprar inteira, na UNIDADE DE COMPRA (fardo, caixa);
- o estoque continua em Float (produto vendido por kg) — por isso as contas
  com saldo passam por `Decimal(str(x))`: 0.1 + 0.2 não pode virar "compra 1
  a mais" por resto de ponto flutuante.
"""

from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal
from typing import Iterable, Optional, Union

Numero = Union[int, float]


# O estoque fracionado vai até o grama (3 casas). Abaixo disso é resto de
# ponto flutuante: um saldo de 0,8 kg que o Float guardou como
# 0,7999999999999999 faria a falta de 12 kg virar 12,0000000000000001 — e o
# teto pediria 13. Arredondar ANTES da conta mata o resto sem perder grama.
CASAS_DA_QUANTIDADE = Decimal("0.001")


def _dec(valor: Numero) -> Decimal:
    return Decimal(str(valor)).quantize(CASAS_DA_QUANTIDADE, rounding=ROUND_HALF_UP)


def dividir_para_cima(a: int, b: int) -> int:
    """Divisão inteira que sempre arredonda para cima (a ≥ 0, b > 0). 7÷2 = 4."""
    if b <= 0:
        raise ValueError("divisor precisa ser positivo")
    return -(-a // b)


def sugerir_compra(
    saldo: Numero,
    em_pedido: Numero,
    minimo: Optional[Numero],
    ideal: Optional[Numero],
    fator: int,
) -> int:
    """Quantas UNIDADES DE COMPRA pedir para repor o estoque. 0 = não precisa.

    - saldo: o que há no estoque agora (unidade do produto);
    - em_pedido: o que já foi pedido e não chegou (unidade do produto);
    - minimo / ideal: do cadastro do estoque; sem mínimo, o produto não
      participa da sugestão (a loja não disse quando repor);
    - fator: unidades do produto por unidade de compra (fardo de 12 → 12).

    Gatilho: `saldo + em_pedido ≤ mínimo` — o que está a caminho conta, senão
    o mesmo produto seria sugerido de novo a cada abertura da tela.
    Alvo: o ideal, quando maior que o mínimo; senão o próprio mínimo.
    """
    if fator < 1:
        raise ValueError("fator precisa ser ao menos 1")
    if minimo is None:
        return 0

    disponivel = _dec(saldo) + _dec(em_pedido)
    if disponivel > _dec(minimo):
        return 0

    alvo = _dec(ideal) if ideal is not None and _dec(ideal) > _dec(minimo) else _dec(minimo)
    falta = alvo - disponivel
    if falta <= 0:
        return 0
    return int((falta / fator).to_integral_value(rounding=ROUND_CEILING))


def preco_por_unidade(preco_compra: int, fator: int) -> Decimal:
    """Centavos por unidade do produto. Exato (Decimal): só serve para COMPARAR.

    O fardo de 12 a R$ 40,00 e a caixa de 24 a R$ 79,00 só são comparáveis
    por unidade (D18). Não arredonda: arredondar empataria preços diferentes.
    """
    if fator < 1:
        raise ValueError("fator precisa ser ao menos 1")
    return Decimal(preco_compra) / fator


@dataclass(frozen=True)
class OfertaFornecedor:
    fornecedor_id: int
    preco_compra: Optional[int]
    fator: int


def mais_barato(ofertas: Iterable[OfertaFornecedor]) -> Optional[int]:
    """O fornecedor com o menor preço por unidade, ou None se não há disputa.

    Só há "mais barato" com ao menos DOIS preços conhecidos — com um só, o
    aviso seria sobre ninguém. Empate não elege ninguém: avisar "fulano é mais
    barato" por diferença zero só ensinaria o lojista a ignorar o aviso.
    """
    com_preco = [o for o in ofertas if o.preco_compra is not None and o.preco_compra > 0]
    if len(com_preco) < 2:
        return None
    por_unidade = sorted((preco_por_unidade(o.preco_compra, o.fator), o.fornecedor_id) for o in com_preco)
    (menor, quem), (segundo, _) = por_unidade[0], por_unidade[1]
    return quem if menor < segundo else None


def economia_percentual(preco_atual: Decimal, preco_menor: Decimal) -> int:
    """Quanto o menor é mais barato que o atual, em pontos-base (1000 = 10%), meio para cima."""
    if preco_atual <= 0 or preco_menor >= preco_atual:
        return 0
    bp = (preco_atual - preco_menor) * 10_000 / preco_atual
    return int(bp.to_integral_value(rounding=ROUND_HALF_UP))
