# ---------------------------------------------------------------------------
# ARQUIVO: services/fiscal/payload/__init__.py
# DESCRICAO: Montar o que vai para a SEFAZ: builder, utilitarios comuns, emitente,
# destinatario, itens, totais e os tributos lidos do XML autorizado.
#
# Ate 13/10/2026 estes arquivos ficavam soltos na raiz de services/fiscal;
# vieram INTEIROS para esta pasta (fase 2 do fiscal):
#   builder.py                 (era payload_builder.py)
#   comum.py                   (era payload_comum.py)
#   destinatario.py            (era payload_destinatario.py)
#   emitente.py                (era payload_emitente.py)
#   itens.py                   (era payload_itens.py)
#   totais.py                  (era payload_totais.py)
#   tributos_xml.py            (era tributos_xml.py)
#
# Este __init__ NAO importa nada, de proposito: cada modulo se importa pelo
# caminho completo. Assim o grafo de imports e o mesmo de antes, e cada modulo
# continua um objeto so (os testes trocam funcoes DENTRO deles com monkeypatch).
# ---------------------------------------------------------------------------
