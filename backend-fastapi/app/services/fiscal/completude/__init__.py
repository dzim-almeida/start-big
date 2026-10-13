# ---------------------------------------------------------------------------
# ARQUIVO: services/fiscal/completude/__init__.py
# DESCRICAO: O que falta para poder emitir: regras de completude (core), validadores
# e a verificacao fiscal da venda e da OS.
#
# Ate 13/10/2026 estes arquivos ficavam soltos na raiz de services/fiscal;
# vieram INTEIROS para esta pasta (fase 2 do fiscal):
#   core.py                    (era core.py)
#   validators.py              (era validators.py)
#   verificacao.py             (era verificacao.py)
#
# Este __init__ NAO importa nada, de proposito: cada modulo se importa pelo
# caminho completo. Assim o grafo de imports e o mesmo de antes, e cada modulo
# continua um objeto so (os testes trocam funcoes DENTRO deles com monkeypatch).
# ---------------------------------------------------------------------------
