# ---------------------------------------------------------------------------
# ARQUIVO: services/fiscal/configuracao/__init__.py
# DESCRICAO: Ligar a emissao: emitente da ativacao e reconferencia do certificado.
#
# Ate 13/10/2026 estes arquivos ficavam soltos na raiz de services/fiscal;
# vieram INTEIROS para esta pasta (fase 2 do fiscal):
#   ativacao.py                (era ativacao.py)
#   certificado.py             (era certificado.py)
#
# Este __init__ NAO importa nada, de proposito: cada modulo se importa pelo
# caminho completo. Assim o grafo de imports e o mesmo de antes, e cada modulo
# continua um objeto so (os testes trocam funcoes DENTRO deles com monkeypatch).
# ---------------------------------------------------------------------------
