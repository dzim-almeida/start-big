# ---------------------------------------------------------------------------
# ARQUIVO: schemas/etiquetas/__init__.py
# DESCRICAO: Schemas das etiquetas: modelos e etiqueta de envio.
#
# Ate 13/10/2026 eram arquivos soltos; vieram INTEIROS para esta pasta:
#   envio.py   (era schemas/etiqueta_envio.py)
#   modelo.py  (era schemas/modelo_etiqueta.py)
#
# Este __init__ NAO importa nada, de proposito: cada assunto se importa pelo
# submodulo (ex.: `from app.schemas.etiquetas import modelo`).
# Assim o grafo de imports e o mesmo de antes.
# ---------------------------------------------------------------------------
