# ---------------------------------------------------------------------------
# ARQUIVO: services/etiquetas/__init__.py
# DESCRICAO: Regras das etiquetas: modelos de etiqueta e etiqueta de envio.
#
# Ate 13/10/2026 eram arquivos soltos; vieram INTEIROS para esta pasta:
#   envio.py   (era services/etiqueta_envio.py)
#   modelo.py  (era services/modelo_etiqueta.py)
#
# Este __init__ NAO importa nada, de proposito: cada assunto se importa pelo
# submodulo (ex.: `from app.services.etiquetas import modelo`).
# Assim o grafo de imports e o mesmo de antes.
# ---------------------------------------------------------------------------
