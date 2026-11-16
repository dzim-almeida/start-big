# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/terminal/__init__.py
# DESCRICAO: Acesso ao banco dos terminais e dos terminais conectados a licenca.
#
# Ate 13/10/2026 eram arquivos soltos; vieram INTEIROS para esta pasta:
#   conectados.py          (era db/crud/terminal_conectado.py)
#   estacoes.py            (era db/crud/terminal.py)
#
# Este __init__ NAO importa nada, de proposito: cada assunto se importa pelo
# submodulo (ex.: `import app.db.crud.terminal.conectados`). Assim o grafo de imports e o
# mesmo de antes, e cada modulo continua um objeto so.
# ---------------------------------------------------------------------------
