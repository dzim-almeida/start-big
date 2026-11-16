# ---------------------------------------------------------------------------
# ARQUIVO: services/comunicado/__init__.py
# DESCRICAO: Comunicados internos da empresa (avisos aos funcionarios).
#
# Ate 13/10/2026 eram arquivos soltos; vieram INTEIROS para esta pasta:
#   comunicados.py         (era services/comunicado.py)
#
# Este __init__ NAO importa nada, de proposito: cada assunto se importa pelo
# submodulo (ex.: `import app.services.comunicado.comunicados`). Assim o grafo de imports e o
# mesmo de antes, e cada modulo continua um objeto so.
# ---------------------------------------------------------------------------
