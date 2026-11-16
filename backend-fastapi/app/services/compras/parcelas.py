# ---------------------------------------------------------------------------
# ARQUIVO: app/services/compras/parcelas.py
# DESCRIÇÃO: Condição de pagamento → parcelas. Função PURA, sem banco.
# ---------------------------------------------------------------------------
"""
O lojista escreve a condição como fala com o fornecedor: "30/60/90", "28 dd",
"à vista". Daqui saem as parcelas do pedido (D8a), que NÃO são conta a pagar:
a conta nasce no recebimento (fase 3), proporcional ao que chegou.

Regra do dinheiro (igual ao parcelamento do financeiro): divide em partes
iguais em centavos e o RESTO vai na última parcela — a soma fecha exata, nunca
um centavo a mais ou a menos.
"""

import re
from dataclasses import dataclass

MAX_PARCELAS = 24
MAX_DIAS = 365

_A_VISTA = {"", "0", "a vista", "à vista", "avista", "à-vista", "a-vista"}


@dataclass(frozen=True)
class Parcela:
    numero: int
    dias: int
    valor: int


def dias_da_condicao(condicao: str | None) -> list[int]:
    """Os prazos, em dias, de uma condição escrita à mão.

    "30/60/90" → [30, 60, 90]; "28 dd" → [28]; "à vista"/vazio → [0].
    Recusa (ValueError) o que não dá para entender, em vez de adivinhar:
    parcela com prazo errado é dívida com data errada.
    """
    texto = (condicao or "").strip().lower()
    if texto in _A_VISTA:
        return [0]
    texto = re.sub(r"\b(dd|ddl|dias?)\b", " ", texto)
    partes = [p for p in re.split(r"[\s/,;+]+", texto) if p]
    if not partes or not all(p.isdigit() for p in partes):
        raise ValueError(f'Não entendi a condição "{condicao}". Use os dias separados por barra, ex.: 30/60/90.')
    dias = [int(p) for p in partes]
    if len(dias) > MAX_PARCELAS:
        raise ValueError(f"No máximo {MAX_PARCELAS} parcelas.")
    if any(d > MAX_DIAS for d in dias):
        raise ValueError(f"Prazo acima de {MAX_DIAS} dias.")
    if dias != sorted(dias) or len(set(dias)) != len(dias):
        raise ValueError("Os prazos precisam ser crescentes e sem repetir, ex.: 30/60/90.")
    return dias


def gerar_parcelas(total: int, condicao: str | None) -> list[Parcela]:
    """Divide `total` (centavos) pelos prazos da condição; o resto vai na última."""
    if total < 0:
        raise ValueError("Total negativo.")
    dias = dias_da_condicao(condicao)
    n = len(dias)
    base = total // n
    resto = total - base * n
    return [
        Parcela(numero=i + 1, dias=d, valor=base + (resto if i == n - 1 else 0))
        for i, d in enumerate(dias)
    ]
