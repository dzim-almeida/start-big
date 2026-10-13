# ---------------------------------------------------------------------------
# ARQUIVO: services/fiscal/eventos/__init__.py
# DESCRICAO: Depois de emitir: consulta e cancelamento, carta de correcao,
# inutilizacao de faixas e NF-e de devolucao.
#
# Ate 13/10/2026 estes arquivos ficavam soltos na raiz de services/fiscal;
# vieram INTEIROS para esta pasta (fase 2 do fiscal):
#   carta_correcao.py          (era carta_correcao.py)
#   consulta_cancelamento.py   (era emissao_eventos.py)
#   devolucao.py               (era devolucao.py)
#   inutilizacao.py            (era inutilizacao.py)
#
# Este __init__ NAO importa nada, de proposito: cada modulo se importa pelo
# caminho completo. Assim o grafo de imports e o mesmo de antes, e cada modulo
# continua um objeto so (os testes trocam funcoes DENTRO deles com monkeypatch).
# ---------------------------------------------------------------------------
