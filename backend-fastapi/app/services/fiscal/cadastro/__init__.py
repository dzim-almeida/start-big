# ---------------------------------------------------------------------------
# ARQUIVO: services/fiscal/cadastro/__init__.py
# DESCRICAO: Dados fiscais do cadastro: perfil tributario, fiscal do produto e do
# servico, campos do produto, cascata de tributacao e avisos de cadastro.
#
# Ate 13/10/2026 estes arquivos ficavam soltos na raiz de services/fiscal;
# vieram INTEIROS para esta pasta (fase 2 do fiscal):
#   avisos.py                  (era avisos.py)
#   campos_produto.py          (era campos_produto.py)
#   perfil_tributario.py       (era perfil_tributario.py)
#   produto.py                 (era produto.py)
#   servico.py                 (era servico.py)
#   tributacao.py              (era tributacao.py)
#
# Este __init__ NAO importa nada, de proposito: cada modulo se importa pelo
# caminho completo. Assim o grafo de imports e o mesmo de antes, e cada modulo
# continua um objeto so (os testes trocam funcoes DENTRO deles com monkeypatch).
# ---------------------------------------------------------------------------
