# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/embalagem_nota.py
# DESCRIÇÃO: Linha de embalagem (fardo/caixa) na NF-e e na NFC-e.
#            Plano de embalagens, fase 4 — decisões D8 e D9.
# ---------------------------------------------------------------------------
"""
A nota de uma linha "2 FD de 12 a R$ 48,00" tem DUAS unidades:

  comercial  → como foi vendido:  uCom = FD, qCom = 2,  vUnCom = 48,00,
               cEAN = código do fardo (DUN-14/EAN do fardo)
  tributável → a unidade do produto: uTrib = UN, qTrib = 24, vUnTrib = 4,00,
               cEANTrib = GTIN da unidade

Regras da SEFAZ que isto respeita:
  * 629 — vProd = qCom × vUnCom      (é o subtotal da linha, fecha por construção)
  * 630 — vProd = qTrib × vUnTrib    (vUnTrib = vProd ÷ qTrib, com 10 casas)
  * 885/886 — GTIN num lado e não no outro: se algum dos dois não for GTIN
    válido, os DOIS vão "SEM GTIN" (D9).
  * cEANTrib nunca recebe GTIN-14 (o DUN é de embalagem, não de unidade).

Linha de unidade (fator 1) não passa por aqui: o payload continua exatamente
o de antes (B8 do plano).
"""
from decimal import ROUND_HALF_UP, Decimal
from typing import Callable, Optional

# Tolerância da SEFAZ nas regras 629/630: R$ 0,01.
TOLERANCIA = Decimal("0.01")


def campos_da_embalagem(
    *,
    quantidade: Decimal,
    fator: int,
    sigla: str,
    valor_bruto: Decimal,
    unidade_base: str,
    gtin_embalagem: Optional[str],
    gtin_unidade: Optional[str],
    gtin_valido: Callable[[Optional[str]], bool],
    sem_gtin: str,
) -> dict:
    """Os campos comerciais/tributáveis que mudam numa linha de embalagem."""
    q_trib = quantidade * fator
    v_un_trib = (valor_bruto / q_trib).quantize(Decimal("0.0000000001"), rounding=ROUND_HALF_UP)

    unidade_ok = _gtin_publico(gtin_unidade, gtin_valido) and len(gtin_unidade.strip()) != 14
    embalagem_ok = _gtin_publico(gtin_embalagem, gtin_valido)
    if unidade_ok and embalagem_ok:
        cean, cean_trib = gtin_embalagem.strip(), gtin_unidade.strip()
    else:
        cean = cean_trib = sem_gtin

    return {
        "unidade_comercial": sigla,
        "codigo_barras_comercial": cean,
        "unidade_tributavel": unidade_base,
        "codigo_barras_tributavel": cean_trib,
        "quantidade_tributavel": float(q_trib),
        "valor_unitario_tributavel": float(v_un_trib),
    }


def _gtin_publico(codigo: Optional[str], gtin_valido: Callable[[Optional[str]], bool]) -> bool:
    """GTIN válido E de circulação pública. O código interno da loja (prefixo 2,
    D18 — é o que o sistema gera para fardo sem código) passa no dígito
    verificador mas não está no Cadastro Centralizado: na nota vai "SEM GTIN"."""
    if not gtin_valido(codigo):
        return False
    digitos = codigo.strip()
    if len(digitos) == 13 and digitos.startswith("2"):
        return False
    if len(digitos) == 14 and digitos[1] == "2":
        return False
    return True


def conferir_valores_do_item(item: dict) -> list[str]:
    """629/630 antes de mandar: a SEFAZ nunca vê uma linha que não fecha."""
    problemas = []
    v_prod = Decimal(str(item.get("valor_bruto") or 0))
    q_com = Decimal(str(item.get("quantidade_comercial") or 0))
    v_un_com = Decimal(str(item.get("valor_unitario_comercial") or 0))
    if abs(q_com * v_un_com - v_prod) > TOLERANCIA:
        problemas.append(f"Item {item.get('numero_item')}: qCom × vUnCom não fecha com vProd (rejeição 629).")
    if "quantidade_tributavel" in item:
        q_trib = Decimal(str(item["quantidade_tributavel"]))
        v_un_trib = Decimal(str(item.get("valor_unitario_tributavel") or 0))
        if abs(q_trib * v_un_trib - v_prod) > TOLERANCIA:
            problemas.append(f"Item {item.get('numero_item')}: qTrib × vUnTrib não fecha com vProd (rejeição 630).")
    return problemas
