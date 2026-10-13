# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/sessao_caixa/__init__.py
# DESCRIÇÃO: Acesso a dados do turno de caixa e do livro do dinheiro.
#
# Era um arquivo so (sessao_caixa.py) ate 13/10/2026; virou pacote:
#   sessao.py         - buscar, abrir e listar sessoes
#   livro_dinheiro.py - movimentos e somas do livro do dinheiro
#
# Este __init__ reexporta tudo: `from app.db.crud import sessao_caixa as caixa_crud`
# continua valendo como antes.
# ---------------------------------------------------------------------------

from app.db.crud.sessao_caixa.sessao import (
    get_sessao_by_id,
    get_sessao_aberta_do_funcionario,
    get_sessao_aberta_do_terminal,
    criar_sessao,
    listar_sessoes,
)

from app.db.crud.sessao_caixa.livro_dinheiro import (
    registrar_movimento,
    listar_movimentos_da_sessao,
    somar_por_origem,
    somar_por_forma_pagamento,
    somar_dinheiro_em_especie,
    somar_saidas_em_especie,
    _somar_em_especie,
    existe_movimento_do_pagamento,
)

__all__ = [
    "get_sessao_by_id",
    "get_sessao_aberta_do_funcionario",
    "get_sessao_aberta_do_terminal",
    "criar_sessao",
    "listar_sessoes",
    "registrar_movimento",
    "listar_movimentos_da_sessao",
    "somar_por_origem",
    "somar_por_forma_pagamento",
    "somar_dinheiro_em_especie",
    "somar_saidas_em_especie",
    "_somar_em_especie",
    "existe_movimento_do_pagamento",
]
