# ---------------------------------------------------------------------------
# ARQUIVO: services/fiscal/emissoes/__init__.py
# DESCRICAO: Emitir a nota: nucleo comum, NFC-e, NF-e de venda e de OS, NF-e de teste,
# reemissao, reconciliacao, numeracao, snapshot dos itens, espelho na venda,
# OS com cara de venda, linha de embalagem e o diagnostico das rejeicoes.
#
# Ate 13/10/2026 estes arquivos ficavam soltos na raiz de services/fiscal;
# vieram INTEIROS para esta pasta (fase 2 do fiscal):
#   adaptador_os.py            (era adaptador_os.py)
#   diagnostico_sefaz.py       (era diagnostico_sefaz.py)
#   embalagem_nota.py          (era embalagem_nota.py)
#   espelho_nota.py            (era espelho_nota.py)
#   nfce.py                    (era emissao_nfce.py)
#   nfe_os.py                  (era emissao_nfe_os.py)
#   nfe_venda.py               (era emissao_nfe_venda.py)
#   nucleo.py                  (era emissao_nucleo.py)
#   numeracao.py               (era numeracao.py)
#   reconciliacao.py           (era reconciliacao.py)
#   reemissao.py               (era reemissao.py)
#   snapshot.py                (era snapshot.py)
#   teste.py                   (era emissao_teste.py)
#
# Este __init__ NAO importa nada, de proposito: cada modulo se importa pelo
# caminho completo. Assim o grafo de imports e o mesmo de antes, e cada modulo
# continua um objeto so (os testes trocam funcoes DENTRO deles com monkeypatch).
# ---------------------------------------------------------------------------
