# ---------------------------------------------------------------------------
# ARQUIVO: app/core/embalagem.py
# DESCRIÇÃO: Preço da embalagem (fardo/caixa) — conta pura, sem banco.
# ---------------------------------------------------------------------------
"""
Espelho de `precoDaEmbalagem` (frontend/src/shared/utils/embalagem.ts): o
preço que o card mostra tem de ser o preço que o caixa cobra, centavo por
centavo. Mudou aqui, muda lá.
"""
from typing import Optional


def preco_da_embalagem(fator: int, preco: Optional[int], desconto_bp: Optional[int], preco_unidade: int) -> int:
    """Centavos: o preço próprio (D14); senão fator × unidade com o desconto (A4);
    senão fator × unidade (D5). Arredonda meio centavo para cima, como o
    `Math.round` do frontend (o `round` do Python arredondaria para o par)."""
    if preco is not None:
        return preco
    cheio = fator * preco_unidade
    if desconto_bp:
        return (cheio * (10000 - desconto_bp) + 5000) // 10000
    return cheio
