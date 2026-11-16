# ---------------------------------------------------------------------------
# ARQUIVO: services/sistema/__init__.py
# DESCRICAO: Rotinas do sistema: setup inicial, segmento da empresa e limpezas
# periodicas (vendas e orcamentos expirados, pastas temporarias).
#
# Ate 13/10/2026 eram arquivos soltos; vieram INTEIROS para esta pasta:
#   limpeza_temporal.py    (era services/limpeza_temporal.py)
#   segmentos.py           (era services/segmentos.py)
#   setup.py               (era services/setup.py)
#
# Este __init__ NAO importa nada, de proposito: cada assunto se importa pelo
# submodulo (ex.: `import app.services.sistema.limpeza_temporal`). Assim o grafo de imports e o
# mesmo de antes, e cada modulo continua um objeto so.
# ---------------------------------------------------------------------------
