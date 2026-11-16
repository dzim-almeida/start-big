# ---------------------------------------------------------------------------
# ARQUIVO: services/precificacao/__init__.py
# DESCRICAO: Preco de venda e custo: regras de preco por quantidade (R1/R2/R3),
# quantidade fracionada (kg, m...) e o custo da mercadoria vendida (CMV).
#
# Ate 13/10/2026 eram arquivos soltos; vieram INTEIROS para esta pasta:
#   custo_mercadoria.py    (era services/custo_mercadoria.py)
#   quantidade.py          (era services/quantidade_venda.py)
#   regras.py              (era services/regras_preco.py)
#
# Este __init__ NAO importa nada, de proposito: cada assunto se importa pelo
# submodulo (ex.: `import app.services.precificacao.custo_mercadoria`). Assim o grafo de imports e o
# mesmo de antes, e cada modulo continua um objeto so.
# ---------------------------------------------------------------------------
