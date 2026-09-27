# ---------------------------------------------------------------------------
# ARQUIVO: app/core/gtin.py
# DESCRIÇÃO: Dígito verificador GS1 e códigos internos de embalagem.
# ---------------------------------------------------------------------------
"""
O cálculo GS1 (módulo 10, pesos 3 e 1 da direita para a esquerda) vale para
EAN-8, UPC-A, EAN-13 e DUN-14. O espelho no frontend é
`shared/etiquetas/codigoBarras.ts` (`digitoVerificadorGs1`).

Código INTERNO de embalagem (plano de embalagens, D18): EAN-13 com prefixo
"29" — faixa de circulação restrita da GS1 (prefixos 20–29), que nunca colide
com código de fabricante. Serve para o leitor do caixa; na nota fiscal sai
como "SEM GTIN", porque não está no Cadastro Centralizado de GTIN.

O "29" (e não só "2") é de propósito: balanças costumam imprimir etiquetas
com "2" + código do produto + peso/preço; ficar no "29" reduz a chance de
colisão se o PDV um dia ler etiqueta de balança (plano, §11.3).
"""

PREFIXO_INTERNO = "29"


def digito_verificador(corpo: str) -> int:
    soma = 0
    for posicao, caractere in enumerate(reversed(corpo)):
        soma += int(caractere) * (3 if posicao % 2 == 0 else 1)
    return (10 - soma % 10) % 10


def gtin_valido(codigo: str | None) -> bool:
    """GTIN-8/12/13/14 com dígito verificador certo."""
    if not codigo or not codigo.isdigit() or len(codigo) not in (8, 12, 13, 14):
        return False
    return digito_verificador(codigo[:-1]) == int(codigo[-1])


def codigo_interno_embalagem(embalagem_id: int) -> str:
    """EAN-13 interno, determinístico pelo id: '29' + id em 10 dígitos + DV."""
    corpo = f"{PREFIXO_INTERNO}{embalagem_id:010d}"
    return f"{corpo}{digito_verificador(corpo)}"
