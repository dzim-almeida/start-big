# ---------------------------------------------------------------------------
# ARQUIVO: services/fiscal/documentos/__init__.py
# DESCRICAO: Guardar e entregar a nota: consultas do Centro Fiscal, XML e DANFE no
# computador da loja e o pacote de XMLs para o contador.
#
# Ate 13/10/2026 estes arquivos ficavam soltos na raiz de services/fiscal;
# vieram INTEIROS para esta pasta (fase 2 do fiscal):
#   arquivos.py                (era arquivos.py)
#   consultas.py               (era documento.py)
#   exportacao_xml.py          (era exportacao_xml.py)
#
# Este __init__ NAO importa nada, de proposito: cada modulo se importa pelo
# caminho completo. Assim o grafo de imports e o mesmo de antes, e cada modulo
# continua um objeto so (os testes trocam funcoes DENTRO deles com monkeypatch).
# ---------------------------------------------------------------------------
