# ---------------------------------------------------------------------------
# ARQUIVO: services/financeiro/__init__.py
# DESCRICAO: Gestao financeira - contas a pagar e a receber, plano de contas,
#            contas bancarias, conciliacao, visao geral, fluxo, extrato e analise.
#
# Ate 12/10/2026 eram quatro arquivos soltos (financeiro.py, financeiro_receber.py,
# financeiro_visao.py e financeiro_analise.py), cortados as pressas pelo limite do
# PyArmor. Viraram este pacote, um arquivo por assunto. Este __init__ reexporta
# tudo: `from app.services import financeiro` continua valendo como antes.
# ---------------------------------------------------------------------------
"""(Texto de quando era services/financeiro.py; vale para o pacote inteiro.)

A REGRA QUE ATRAVESSA TUDO AQUI: documento muda, lançamento não.

`contas_pagar` é DOCUMENTO. Prorrogar vencimento e corrigir valor digitado
errado são operações legítimas, e cada uma deixa rastro em
`historico_financeiro`.

`movimentacoes_financeiras` é LANÇAMENTO. Só insere. Um pagamento lançado por
engano não se apaga: estorna-se, com um movimento contrário na data de HOJE.

Confundir as duas camadas é o que faz ERP virar planilha com senha.
"""

from app.services.financeiro.comum import (
    _funcionario_do_token,
    _somar_meses,
    ENTIDADE_CONTA_RECEBER,
    _nome_do_cliente,
)

from app.services.financeiro.plano_contas import (
    PLANO_CONTAS_PADRAO,
    _semear_plano_padrao,
    listar_planos_conta,
    criar_plano_conta,
    atualizar_plano_conta,
)

from app.services.financeiro.contas_bancarias import (
    _semear_conta_padrao,
    _conta_padrao_id,
    listar_contas_bancarias,
    criar_conta_bancaria,
    atualizar_conta_bancaria,
)

from app.services.financeiro.contas_pagar import (
    ENTIDADE_CONTA_PAGAR,
    _serializar_conta,
    listar_contas_pagar,
    get_conta_pagar,
    listar_historico_da_conta,
    _validar_referencias,
    criar_conta_pagar,
    CAMPOS_AUDITADOS,
    CAMPOS_LIVRES_APOS_PAGAMENTO,
    atualizar_conta_pagar,
    CAMPOS_PROPAGAVEIS,
    _propagar_nas_proximas_parcelas,
    reativar_conta_pagar,
    cancelar_conta_pagar,
)

from app.services.financeiro.contas_pagar_baixa import (
    _proximo_vencimento,
    pagar_conta,
    estornar_pagamento,
)

from app.services.financeiro.promessas import (
    _prazo_da_forma,
    _juros_da_operadora,
    aplicar_prazo_de_recebimento,
    _criar_promessa,
    registrar_promessas_de_venda,
    registrar_promessas_de_os,
    cancelar_promessas_do_documento,
)

from app.services.financeiro.contas_receber import (
    _serializar_receber,
    listar_contas_receber,
    get_conta_receber,
    criar_conta_receber,
    CAMPOS_AUDITADOS_RECEBER,
    atualizar_conta_receber,
    cancelar_conta_receber,
    receber_conta,
    estornar_recebimento,
    listar_historico_do_recebimento,
)

from app.services.financeiro.conciliacao import (
    baixar_automaticas,
    _formas_de_origem,
    get_conciliacao,
    baixar_lote,
)

from app.services.financeiro.saldo import (
    SaldoDasContas,
    saldo_atual_das_contas,
    saldo_atual_por_conta,
)

from app.services.financeiro.resumo import (
    DIAS_ATE_O_SALDO_ENVELHECER,
    FRACAO_MATERIAL_DO_FATURAMENTO,
    PISO_VALOR_MATERIAL,
    DIAS_DE_ATRASO_GRAVE,
    DIAS_ATE_O_APERTO_SER_URGENTE,
    _montar_alertas,
    CODIGOS_DE_ALERTA,
    adiar_alerta,
    get_resumo,
)

from app.services.financeiro.fluxo_caixa import (
    get_fluxo_caixa,
)

from app.services.financeiro.extrato import (
    listar_extrato,
    get_detalhe_custo,
)

from app.services.financeiro.analise import (
    MESES_DE_QUEDA_PARA_ALERTAR,
    QUEDA_GRAVE_ACUMULADA,
    QUEDA_DE_ORIGEM,
    FATIA_DE_DEPENDENCIA,
    CUSTO_CRESCE_VEZES_MAIS,
    PRAZO_LENTO_ACIMA_DE,
    ROTULO_ORIGEM_RECEITA,
    _primeiro_dia,
    _mes_anterior,
    _ultimo_dia_do_mes,
    get_serie,
    PORTAO_PROJECAO,
    MESES_NA_MEDIA,
    MARGEM_MINIMA,
    MARGEM_MAXIMA,
    CASTIGO_HISTORICO_CURTO,
    get_projecao,
    _media,
    alertas_de_tendencia,
)

__all__ = [
    "_funcionario_do_token",
    "_somar_meses",
    "ENTIDADE_CONTA_RECEBER",
    "_nome_do_cliente",
    "PLANO_CONTAS_PADRAO",
    "_semear_plano_padrao",
    "listar_planos_conta",
    "criar_plano_conta",
    "atualizar_plano_conta",
    "_semear_conta_padrao",
    "_conta_padrao_id",
    "listar_contas_bancarias",
    "criar_conta_bancaria",
    "atualizar_conta_bancaria",
    "ENTIDADE_CONTA_PAGAR",
    "_serializar_conta",
    "listar_contas_pagar",
    "get_conta_pagar",
    "listar_historico_da_conta",
    "_validar_referencias",
    "criar_conta_pagar",
    "CAMPOS_AUDITADOS",
    "CAMPOS_LIVRES_APOS_PAGAMENTO",
    "atualizar_conta_pagar",
    "CAMPOS_PROPAGAVEIS",
    "_propagar_nas_proximas_parcelas",
    "reativar_conta_pagar",
    "cancelar_conta_pagar",
    "_proximo_vencimento",
    "pagar_conta",
    "estornar_pagamento",
    "_prazo_da_forma",
    "_juros_da_operadora",
    "aplicar_prazo_de_recebimento",
    "_criar_promessa",
    "registrar_promessas_de_venda",
    "registrar_promessas_de_os",
    "cancelar_promessas_do_documento",
    "_serializar_receber",
    "listar_contas_receber",
    "get_conta_receber",
    "criar_conta_receber",
    "CAMPOS_AUDITADOS_RECEBER",
    "atualizar_conta_receber",
    "cancelar_conta_receber",
    "receber_conta",
    "estornar_recebimento",
    "listar_historico_do_recebimento",
    "baixar_automaticas",
    "_formas_de_origem",
    "get_conciliacao",
    "baixar_lote",
    "SaldoDasContas",
    "saldo_atual_das_contas",
    "saldo_atual_por_conta",
    "DIAS_ATE_O_SALDO_ENVELHECER",
    "FRACAO_MATERIAL_DO_FATURAMENTO",
    "PISO_VALOR_MATERIAL",
    "DIAS_DE_ATRASO_GRAVE",
    "DIAS_ATE_O_APERTO_SER_URGENTE",
    "_montar_alertas",
    "CODIGOS_DE_ALERTA",
    "adiar_alerta",
    "get_resumo",
    "get_fluxo_caixa",
    "listar_extrato",
    "get_detalhe_custo",
    "MESES_DE_QUEDA_PARA_ALERTAR",
    "QUEDA_GRAVE_ACUMULADA",
    "QUEDA_DE_ORIGEM",
    "FATIA_DE_DEPENDENCIA",
    "CUSTO_CRESCE_VEZES_MAIS",
    "PRAZO_LENTO_ACIMA_DE",
    "ROTULO_ORIGEM_RECEITA",
    "_primeiro_dia",
    "_mes_anterior",
    "_ultimo_dia_do_mes",
    "get_serie",
    "PORTAO_PROJECAO",
    "MESES_NA_MEDIA",
    "MARGEM_MINIMA",
    "MARGEM_MAXIMA",
    "CASTIGO_HISTORICO_CURTO",
    "get_projecao",
    "_media",
    "alertas_de_tendencia",
]
