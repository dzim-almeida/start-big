# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/configuracao/__init__.py
# DESCRICAO: Acesso ao banco das configuracoes de cada modulo, e o registro da licenca.
#
# Ate 13/10/2026 eram arquivos soltos (db/crud/configuracao_X.py); vieram
# INTEIROS para esta pasta, um por assunto (o configuracao_os virou
# ordem_servico.py, para nao ter um submodulo chamado `os`):
#   backup.py
#   clientes.py
#   licenca.py   (o registro da licenca do sistema)
#   marcenaria.py
#   ordem_servico.py   (era configuracao_os.py)
#   produtos.py
#   seguranca.py
#   vendas.py
#
# Este __init__ NAO importa nada, de proposito: cada assunto se importa pelo
# submodulo (ex.: `from app.db.crud.configuracao import vendas as config_vendas_crud`).
# Assim o grafo de imports e o mesmo de antes, e cada modulo continua um objeto
# so -- o que os testes trocam com monkeypatch (ex.: licenca) chega em quem chama.
# ---------------------------------------------------------------------------
