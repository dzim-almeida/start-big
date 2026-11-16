# ---------------------------------------------------------------------------
# ARQUIVO: schemas/precificacao/__init__.py
# DESCRICAO: Schemas de preco: regras de preco do produto e o tipo da quantidade.
#
# Ate 13/10/2026 eram arquivos soltos; vieram INTEIROS para esta pasta:
#   quantidade.py          (era schemas/quantidade.py)
#   regras.py              (era schemas/produto_regra_preco.py)
#
# Este __init__ NAO importa nada, de proposito: cada assunto se importa pelo
# submodulo (ex.: `import app.schemas.precificacao.quantidade`). Assim o grafo de imports e o
# mesmo de antes, e cada modulo continua um objeto so.
# ---------------------------------------------------------------------------
