# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/payload_totais.py
# DESCRIÇÃO: Totais da nota e formas de pagamento (com o fechamento conferido).
#
# Saiu do payload_builder.py na F5 (07/10/2026), sem mudar comportamento: o
# código foi movido, não reescrito. O payload da nota não muda nem um byte
# (test_payload_fotografias.py).
# ---------------------------------------------------------------------------

from typing import Optional
from app.db.models.venda import Venda
from .tax_engine.types import ResultadoCalculo
from .payload_comum import _centavos_para_reais


def _totais_interestaduais(t) -> dict:
    """vBCST/vST e vICMSUFDest/vFCPUFDest do cabeçalho — só quando existem."""
    campos = {}
    if t.valor_icms_st and t.valor_icms_st > 0:
        campos["icms_base_calculo_st"] = float(t.base_calculo_icms_st)
        campos["icms_valor_total_st"] = float(t.valor_icms_st)
    if t.valor_difal and t.valor_difal > 0:
        campos["icms_valor_total_uf_destino"] = float(t.valor_difal)    # vICMSUFDest
    if t.valor_fcp and t.valor_fcp > 0:
        campos["fcp_valor_total_uf_destino"] = float(t.valor_fcp)       # vFCPUFDest
    return campos


# Códigos SEFAZ que representam cartão. Só neles o grupo `card` faz sentido —
# dizer "não integrado" num pagamento em dinheiro é ruído no XML.
_CODIGOS_SEFAZ_CARTAO = {"03", "04"}  # 03 = crédito, 04 = débito


# tpIntegra da SEFAZ: 1 = integrado ao sistema (TEF), 2 = não integrado (POS).
_TP_INTEGRA = {"TEF": 1, "POS": 2}


def _montar_pagamentos(venda: Venda) -> list[dict]:
    pagamentos = []

    for pag in venda.pagamentos:
        forma = pag.forma_pagamento
        codigo = forma.codigo_sefaz or "99"
        pag_dict = {
            "forma_pagamento": codigo,
            "valor_pagamento": _centavos_para_reais(pag.valor),  # já retorna float
        }

        if codigo in _CODIGOS_SEFAZ_CARTAO:
            # Sem classificação cadastrada, assume POS (não integrado). É o
            # arranjo da maioria das lojas pequenas, e afirmar integração que
            # não existe descreveria mal a operação num documento fiscal.
            integracao = getattr(forma, "tipo_integracao", None) or "POS"
            if integracao != "NAO_SE_APLICA":
                pag_dict["tipo_integracao"] = _TP_INTEGRA.get(integracao, 2)

        pagamentos.append(pag_dict)

    return pagamentos


def _validar_fechamento_pagamentos(
    pagamentos: list[dict], valor_troco: float, valor_total_nota: float
) -> None:
    """
    Confere a regra do grupo <pag>: soma dos pagamentos − troco == total da nota.

    A SEFAZ audita isso (Rejeição 767). Falhar aqui é barato; descobrir na
    transmissão custa o número da nota e uma inutilização.
    """
    soma_pagamentos = round(sum(p["valor_pagamento"] for p in pagamentos), 2)
    liquido = round(soma_pagamentos - valor_troco, 2)

    if liquido != round(valor_total_nota, 2):
        raise ValueError(
            f"Pagamentos não fecham com o total da nota: "
            f"soma dos pagamentos R$ {soma_pagamentos:.2f} − troco R$ {valor_troco:.2f} "
            f"= R$ {liquido:.2f}, mas o total da nota é R$ {valor_total_nota:.2f}."
        )


def _montar_totais_pagamentos(
    venda: Venda, resultado_calculo: Optional[ResultadoCalculo]
) -> tuple[dict, list[dict], float]:
    """Totais, formas de pagamento e troco — comuns a NF-e e NFC-e.

    Já deixa a equação de fechamento conferida: a SEFAZ audita
    `Σ pagamentos − troco == total` nos dois modelos (Rejeição 767), e na NFC-e
    o troco em dinheiro é a regra, não a exceção.
    """
    if resultado_calculo:
        t = resultado_calculo.totais
        totais = {
            "valor_produtos": float(t.valor_total_produtos),
            "valor_frete": float(t.valor_frete),
            "valor_seguro": float(t.valor_seguro),
            "valor_outras_despesas": float(t.valor_outras_despesas),
            "valor_desconto": float(t.valor_desconto),
            "icms_base_calculo": float(t.base_calculo_icms),
            "icms_valor_total": float(t.valor_icms),
            "valor_total": float(t.valor_total_nota),   # já inclui a ST (não o DIFAL)
            **_totais_interestaduais(t),
        }
    else:
        totais = {
            "valor_produtos": _centavos_para_reais(venda.total),
            "valor_desconto": 0.0,
            "valor_frete": 0.0,
            "valor_seguro": 0.0,
            "valor_outras_despesas": 0.0,
            "icms_base_calculo": 0.0,
            "icms_valor_total": 0.0,
            "valor_total": _centavos_para_reais(venda.total),
        }

    formas_pagamento = _montar_pagamentos(venda)
    valor_troco = _centavos_para_reais(venda.troco or 0)

    _validar_fechamento_pagamentos(formas_pagamento, valor_troco, totais["valor_total"])

    return totais, formas_pagamento, valor_troco
