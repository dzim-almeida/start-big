# ---------------------------------------------------------------------------
# ARQUIVO: app/services/quantidade_venda.py
# DESCRIÇÃO: Quem pode vender quantidade quebrada, e o dinheiro de uma linha.
#
# Venda fracionada (docs/venda-fracionada-plano.md), decisões aceitas pelo
# Alan em 07/10/2026:
#   D1 — fracionado é decidido pela UNIDADE do produto: KG, G, L, ML, M, CM, M2, M3.
#        Sem campo novo no cadastro; a unidade já diz.
#   D3 — UN (e qualquer outra) com 1,5: recusa com mensagem clara.
#   D5 — embalagem (fardo/caixa) é sempre inteira; item avulso, sem unidade
#        cadastrada, também.
#
# O dinheiro continua inteiro em centavos: `subtotal_da_linha` arredonda
# meio-para-cima (3,5 kg × R$ 10,01 = R$ 35,035 → R$ 35,04). Para quantidade
# inteira o resultado é exatamente `quantidade × unitário`, como sempre foi.
# ---------------------------------------------------------------------------

from decimal import ROUND_HALF_UP, Decimal
from typing import Optional, Union

from app.helpers.exceptions import BadRequestException

# ⚠️ ESPELHO de `UNIDADES_FRACIONADAS` em frontend/src/shared/utils/quantidade.ts.
# Divergir é o erro de 10/08 de novo (a tela aceita, o servidor recusa).
# test_quantidade_venda.py confere as duas listas.
UNIDADES_FRACIONAVEIS = frozenset({"KG", "G", "L", "ML", "M", "CM", "M2", "M3"})

_NOMES = "KG, G, L, ML, M, CM, M² e M³"


def _unidade(produto) -> str:
    bruta = (getattr(produto, "unidade_medida", None) or "").strip().upper()
    return bruta.replace("²", "2").replace("³", "3")


def eh_fracionavel(produto) -> bool:
    """O produto pode ser vendido em quantidade quebrada (3,5 kg)?"""
    return produto is not None and _unidade(produto) in UNIDADES_FRACIONAVEIS


def exigir_quantidade_permitida(
    quantidade: Union[int, float], produto, fator_embalagem: Optional[int] = 1
) -> None:
    """Recusa quantidade quebrada onde ela não cabe. Inteira passa sempre."""
    if float(quantidade).is_integer():
        return
    if produto is None:
        raise BadRequestException(detail="Item avulso é vendido em quantidade inteira.")
    if (fator_embalagem or 1) > 1:
        raise BadRequestException(detail="Embalagem (fardo, caixa) é vendida inteira.")
    if not eh_fracionavel(produto):
        unidade = _unidade(produto) or "sem unidade"
        raise BadRequestException(
            detail=(
                f"{produto.nome} é vendido em unidade inteira ({unidade}). "
                f"Só produtos em {_NOMES} aceitam quantidade quebrada."
            )
        )


def subtotal_da_linha(quantidade: Union[int, float], valor_unitario: int) -> int:
    """quantidade × unitário em centavos, arredondado meio-para-cima."""
    valor = Decimal(str(quantidade)) * Decimal(int(valor_unitario or 0))
    return int(valor.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
