# ---------------------------------------------------------------------------
# ARQUIVO: services/fiscal/derivacao/st_fabricante_ce.py
# DESCRICAO: Fabricante do Ceara que recolhe o ICMS-ST em DAE (Decreto CE
#            32.900/2018), na NF-e de venda do Simples Nacional.
#
# ORIGEM: orientacao do contador da marcenaria do Junior, em 05/11/2026 (CNAE
# 3101-2/00): 5401 dentro do CE e 6401 para outros estados, com CSOSN 500 e sem
# valor de ST na nota. O imposto retido e pago fora da nota, em DAE.
#
# A regra nasce DESLIGADA e so alcanca o item que o cadastro marca como 5401 (ou
# 6401) + CSOSN 500. Com a opcao desligada, a nota e a mesma de antes.
#
# Venda a nao contribuinte de outro estado fica RECUSADA: a orientacao nao trata
# esse caso, e o motor nao chuta situacao tributaria.
# ---------------------------------------------------------------------------

from typing import Any

CSOSN_ST_RECOLHIDA = "500"
SUFIXO_PRODUCAO_COM_ST = "401"
CFOP_INTERNO_ST_RECOLHIDA = "5401"

# Art. 6, par. 1: vale so para as operacoes internas.
TEXTO_NOTA_OPERACAO_INTERNA = "ICMS retido por substituicao tributaria, Decreto 32.900/2018"


def opcao_ligada(fiscal_settings: Any) -> bool:
    """Se a loja ligou a opcao. Sem configuracao, esta desligada."""
    return bool(getattr(fiscal_settings, "nfe_st_fabricante_ce", False))


def item_com_st_recolhida(fiscal: Any, simples_nacional: bool) -> bool:
    """Se o item e o caso da regra: 5401 ou 6401 + CSOSN 500, no Simples."""
    if not simples_nacional or fiscal is None:
        return False
    cfop = getattr(fiscal, "cfop_padrao", None) or ""
    return getattr(fiscal, "csosn", None) == CSOSN_ST_RECOLHIDA and cfop[1:] == SUFIXO_PRODUCAO_COM_ST
