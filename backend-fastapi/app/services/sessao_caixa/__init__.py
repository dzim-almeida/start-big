# ---------------------------------------------------------------------------
# ARQUIVO: services/sessao_caixa/__init__.py
# DESCRIÇÃO: Regras do turno de caixa: abrir, suprir, sangrar, fechar e conferir.
#
# TUDO AQUI SÓ ACONTECE COM `controlar_caixa` LIGADO.
#
# A chave é por empresa (configuracoes_vendas) e nasce DESLIGADA. Loja que não a
# liga nunca chega a este arquivo: continua vendendo como sempre vendeu, sem
# turno, sem sangria e sem nada gravado no livro do dinheiro. É essa porta
# fechada que permite o caixa existir sem incomodar as lojas que já rodam.
#
# Era um arquivo so (sessao_caixa.py, 35 KB) ate 13/10/2026; virou pacote:
#   regras.py      - a chave do caixa, especie, sessao aberta obrigatoria e a
#                    trava de vender com o caixa fechado
#   autorizacao.py - quem autoriza abertura e sangria (PIN do gerente)
#   turno.py       - abrir, suprimento, sangria e fechar
#   consultas.py   - sessao atual, resumo, historico e saldo esperado
#   pagamentos.py  - o que entra no caixa pelas vendas e OS (e o estorno)
#
# Este __init__ reexporta tudo: `from app.services import sessao_caixa` continua
# valendo como antes (venda, OS, financeiro e o endpoint chamam caixa_service.X).
# ---------------------------------------------------------------------------

from app.services.sessao_caixa.regras import (
    NOMES_DE_ESPECIE,
    _config,
    caixa_esta_ligado,
    _exigir_caixa_ligado,
    _funcionario_do_token,
    _ids_das_formas_em_especie,
    _sessao_aberta_obrigatoria,
    exigir_caixa_aberto_para_vender,
)

from app.services.sessao_caixa.autorizacao import (
    _validar_autorizacao_sangria,
    _validar_autorizacao_abertura,
)

from app.services.sessao_caixa.consultas import (
    get_sessao_atual,
    get_resumo_de_sessao,
    listar_historico,
    calcular_saldo_esperado_em_especie,
    montar_resumo,
)

from app.services.sessao_caixa.turno import (
    abrir_caixa,
    registrar_suprimento,
    registrar_sangria,
    fechar_caixa,
)

from app.services.sessao_caixa.pagamentos import (
    valor_que_entra,
    registrar_pagamentos_de_venda,
    _conta_do_dinheiro,
    registrar_pagamentos_de_os,
    estornar_pagamentos_de_os,
)

__all__ = [
    "NOMES_DE_ESPECIE",
    "_config",
    "caixa_esta_ligado",
    "_exigir_caixa_ligado",
    "_funcionario_do_token",
    "_ids_das_formas_em_especie",
    "_sessao_aberta_obrigatoria",
    "exigir_caixa_aberto_para_vender",
    "_validar_autorizacao_sangria",
    "_validar_autorizacao_abertura",
    "get_sessao_atual",
    "get_resumo_de_sessao",
    "listar_historico",
    "calcular_saldo_esperado_em_especie",
    "montar_resumo",
    "abrir_caixa",
    "registrar_suprimento",
    "registrar_sangria",
    "fechar_caixa",
    "valor_que_entra",
    "registrar_pagamentos_de_venda",
    "_conta_do_dinheiro",
    "registrar_pagamentos_de_os",
    "estornar_pagamentos_de_os",
]
