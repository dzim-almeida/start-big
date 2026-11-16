# ---------------------------------------------------------------------------
# ARQUIVO: schemas/comum/__init__.py
# DESCRICAO: Schemas comuns a varios modulos (paginacao).
#
# Ate 13/10/2026 eram arquivos soltos; vieram INTEIROS para esta pasta:
#   paginacao.py           (era schemas/pagination.py)
#
# Este __init__ NAO importa nada, de proposito: cada assunto se importa pelo
# submodulo (ex.: `import app.schemas.comum.paginacao`). Assim o grafo de imports e o
# mesmo de antes, e cada modulo continua um objeto so.
# ---------------------------------------------------------------------------
