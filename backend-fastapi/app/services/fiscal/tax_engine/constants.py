# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/tax_engine/constants.py
# DESCRIÇÃO: Constantes do motor de cálculo tributário.
#            CSTs/CSOSNs suportados, precisão numérica e defaults.
# ---------------------------------------------------------------------------

from decimal import Decimal, ROUND_HALF_UP

# --- Precisão numérica ---
PRECISAO = Decimal("0.01")
ROUND_MODE = ROUND_HALF_UP

# --- CSTs de ICMS suportados (Regime Normal) ---
CST_ICMS_TRIBUTADO = frozenset({"00"})       # Tributada integralmente
CST_ICMS_REDUZIDA = frozenset({"20"})        # Com redução de base de cálculo
CST_ICMS_ISENTO = frozenset({"40", "41"})    # Isenta / Não tributada
CST_ICMS_ST = frozenset({"60"})              # ICMS cobrado anteriormente por ST
# O que o CADASTRO do produto aceita (validators.py). CST 10/70 ficam de fora
# de propósito: a condição de substituto é da OPERAÇÃO interestadual e é
# derivada na emissão a partir da regra do perfil, nunca gravada no produto.
CST_ICMS_SUPORTADOS = CST_ICMS_TRIBUTADO | CST_ICMS_REDUZIDA | CST_ICMS_ISENTO | CST_ICMS_ST
# Remetente como SUBSTITUTO (TASK008): própria como 00/20 + retenção da ST.
# Só o calculador aceita, e só com regra de ST no item.
CST_ICMS_SUBSTITUTO = frozenset({"10"})          # Tributada e com cobrança por ST
CST_ICMS_SUBSTITUTO_REDUZIDA = frozenset({"70"}) # Com redução de base e cobrança por ST

# --- CSOSNs suportados (Simples Nacional) ---
CSOSN_COM_CREDITO = frozenset({"101"})       # Tributada com permissão de crédito
CSOSN_SEM_CREDITO = frozenset({"102"})       # Tributada sem permissão de crédito
CSOSN_ST = frozenset({"500"})                # ICMS cobrado anteriormente por ST
CSOSN_SUPORTADOS = CSOSN_COM_CREDITO | CSOSN_SEM_CREDITO | CSOSN_ST  # cadastro
CSOSN_SUBSTITUTO_COM_CREDITO = frozenset({"201"})  # 101 + cobrança por ST (só na emissão)
CSOSN_SUBSTITUTO_SEM_CREDITO = frozenset({"202"})  # 102 + cobrança por ST (só na emissão)

# --- CSTs de PIS/COFINS ---
CST_PIS_COFINS_TRIBUTADO = frozenset({"01", "02"})  # Alíquota normal / diferenciada
CST_PIS_COFINS_ISENTO = frozenset({"04", "05", "06", "07", "08", "09"})

# Saída do Simples Nacional: os tributos vão na guia única, não na nota.
# 49 = Outras Operações de Saída, com base e alíquota zeradas.
CST_PIS_COFINS_SIMPLES = "49"

# --- IPI (comércio/serviços — não calculado) ---
CST_IPI_NAO_TRIBUTADO = "53"
IPI_CODIGO_ENQUADRAMENTO = "999"

# --- Defaults de alíquota PIS/COFINS, por regime de apuração ---
#
# PIS e COFINS são tributos FEDERAIS: a alíquota vem do regime de apuração da
# empresa, não da UF. Até 05/09/2026 o motor usava 1,65/7,60 para todo mundo,
# rotulado como "Lucro Presumido cumulativo" — que é justamente o regime onde
# esses números NÃO se aplicam. Confirmado com a contabilidade:
#
#   Cumulativo     (Lucro Presumido) → 0,65% / 3,00%
#   Não-cumulativo (Lucro Real)      → 1,65% / 7,60%
#
# Quem está no Simples não passa por aqui: sai com CST 49 zerado.
PIS_CUMULATIVO = Decimal("0.65")
COFINS_CUMULATIVO = Decimal("3.00")
PIS_NAO_CUMULATIVO = Decimal("1.65")
COFINS_NAO_CUMULATIVO = Decimal("7.60")
