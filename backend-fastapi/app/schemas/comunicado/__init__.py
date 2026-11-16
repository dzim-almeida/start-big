# ---------------------------------------------------------------------------
# ARQUIVO: schemas/comunicado/__init__.py
# DESCRICAO: Schemas dos comunicados.
#
# Ate 13/10/2026 eram arquivos soltos; vieram INTEIROS para esta pasta:
#   comunicados.py         (era schemas/comunicado.py)
#
# Este __init__ NAO importa nada, de proposito: cada assunto se importa pelo
# submodulo (ex.: `import app.schemas.comunicado.comunicados`). Assim o grafo de imports e o
# mesmo de antes, e cada modulo continua um objeto so.
# ---------------------------------------------------------------------------
