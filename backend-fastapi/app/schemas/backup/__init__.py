# ---------------------------------------------------------------------------
# ARQUIVO: schemas/backup/__init__.py
# DESCRICAO: Schemas do backup local, da sincronizacao com a nuvem e da configuracao.
#
# Ate 13/10/2026 eram arquivos soltos; vieram INTEIROS para esta pasta:
#   operacoes.py           (era schemas/backup.py)
#
# Este __init__ NAO importa nada, de proposito: cada assunto se importa pelo
# submodulo (ex.: `import app.schemas.backup.operacoes`). Assim o grafo de imports e o
# mesmo de antes, e cada modulo continua um objeto so.
# ---------------------------------------------------------------------------
