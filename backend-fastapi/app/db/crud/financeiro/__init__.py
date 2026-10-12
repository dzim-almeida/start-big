# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/financeiro/__init__.py
# DESCRICAO: Acesso ao banco da gestao financeira.
#
# Ate 12/10/2026 eram dois arquivos (financeiro.py e financeiro_receber.py), o
# segundo cortado do primeiro pelo limite do PyArmor. Viraram este pacote, um
# arquivo por assunto. Este __init__ reexporta tudo: `from app.db.crud import
# financeiro` continua valendo como antes (inclusive para o que era do
# financeiro_receber).
# ---------------------------------------------------------------------------

from app.db.crud.financeiro.plano_contas import (
    listar_planos_conta,
    get_plano_conta,
    get_plano_conta_por_nome,
    criar_plano_conta,
    ids_de_planos_em_uso,
)

from app.db.crud.financeiro.contas_bancarias import (
    listar_contas_bancarias,
    get_conta_principal,
    get_conta_bancaria,
    criar_conta_bancaria,
    limpar_principal,
)

from app.db.crud.financeiro.contas_pagar import (
    _query_contas,
    listar_contas_pagar,
    totais_contas_pagar,
    get_conta_pagar,
    criar_conta_pagar,
    get_ocorrencia_gerada,
    apagar_conta,
    proximas_a_vencer,
    listar_parcelas_seguintes,
)

from app.db.crud.financeiro.despesas import (
    despesas_por_categoria,
    _total_pago,
    total_despesas_pagas,
    total_compras_estoque,
)

from app.db.crud.financeiro.historico import (
    registrar_historico,
    listar_historico,
)

from app.db.crud.financeiro.contas_receber import (
    _query_receber,
    listar_contas_receber,
    totais_contas_receber,
    pendentes_por_vencimento,
    get_conta_receber,
    criar_conta_receber,
    get_receber_do_pagamento,
    total_recebido,
    listar_receber_pendentes_do_documento,
)

from app.db.crud.financeiro.conciliacao import (
    listar_baixas_automaticas_vencidas,
    formas_de_origem_completas,
    formas_de_origem,
)

from app.db.crud.financeiro.extrato import (
    _query_extrato,
    listar_extrato,
    totais_extrato,
    documentos_de_origem,
)

from app.db.crud.financeiro.livro import (
    ORIGENS_DE_RECEITA,
    ORIGENS_DE_SALDO,
    entradas_e_saidas_desde,
    total_entrou_no_caixa,
    total_saiu_do_caixa,
)

from app.db.crud.financeiro.alertas import (
    vencimento_mais_antigo_pendente,
    codigos_dispensados,
    dispensar_alerta,
    prazo_medio_recebimento,
)

__all__ = [
    "listar_planos_conta",
    "get_plano_conta",
    "get_plano_conta_por_nome",
    "criar_plano_conta",
    "ids_de_planos_em_uso",
    "listar_contas_bancarias",
    "get_conta_principal",
    "get_conta_bancaria",
    "criar_conta_bancaria",
    "limpar_principal",
    "_query_contas",
    "listar_contas_pagar",
    "totais_contas_pagar",
    "get_conta_pagar",
    "criar_conta_pagar",
    "get_ocorrencia_gerada",
    "apagar_conta",
    "proximas_a_vencer",
    "listar_parcelas_seguintes",
    "despesas_por_categoria",
    "_total_pago",
    "total_despesas_pagas",
    "total_compras_estoque",
    "registrar_historico",
    "listar_historico",
    "_query_receber",
    "listar_contas_receber",
    "totais_contas_receber",
    "pendentes_por_vencimento",
    "get_conta_receber",
    "criar_conta_receber",
    "get_receber_do_pagamento",
    "total_recebido",
    "listar_receber_pendentes_do_documento",
    "listar_baixas_automaticas_vencidas",
    "formas_de_origem_completas",
    "formas_de_origem",
    "_query_extrato",
    "listar_extrato",
    "totais_extrato",
    "documentos_de_origem",
    "ORIGENS_DE_RECEITA",
    "ORIGENS_DE_SALDO",
    "entradas_e_saidas_desde",
    "total_entrou_no_caixa",
    "total_saiu_do_caixa",
    "vencimento_mais_antigo_pendente",
    "codigos_dispensados",
    "dispensar_alerta",
    "prazo_medio_recebimento",
]
