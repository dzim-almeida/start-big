# ---------------------------------------------------------------------------
# ARQUIVO: schemas/fiscal/__init__.py
# DESCRICAO: Schemas do modulo fiscal.
#
# Ate 13/10/2026 eram arquivos soltos em schemas/; vieram INTEIROS para esta
# pasta: documento.py (era documento_fiscal.py), emissao.py (emissao_fiscal.py),
# perfil_tributario.py, produto.py (produto_fiscal.py), servico.py
# (servico_fiscal.py), tributacao.py e verificacao.py (verificacao_fiscal.py).
# O nfe_entrada fica para o modulo de Compras.
#
# Este __init__ NAO importa nada, de proposito: cada schema se importa pelo
# submodulo (ex.: `from app.schemas.fiscal.emissao import EmissaoResponse`).
# Assim o grafo de imports e o mesmo de antes.
# ---------------------------------------------------------------------------
