# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/venda/__init__.py
# DESCRICAO: Acesso ao banco das vendas.
#
# Era um arquivo so (venda.py) ate 13/10/2026; virou pacote:
#   consultas.py   - buscar venda e item, listar e resumo por status
#   escrita.py     - criar e atualizar venda e itens
#   nota_fiscal.py - dados fiscais da venda (era db/crud/venda_nota_fiscal.py)
#
# Este __init__ reexporta o que era venda.py. A nota fiscal fica no submodulo
# (nomes genericos: create, update, upsert):
# `from app.db.crud.venda import nota_fiscal`.
# ---------------------------------------------------------------------------

from app.db.crud.venda.consultas import (
    get_sale_by_id,
    get_product_by_id,
    get_sales_by_search,
    get_sales_status,
)

from app.db.crud.venda.escrita import (
    create_sale,
    add_product_to_sale,
    update_sale,
    update_product_in_sale,
    remove_product_from_sale,
)

__all__ = [
    "get_sale_by_id",
    "get_product_by_id",
    "get_sales_by_search",
    "get_sales_status",
    "create_sale",
    "add_product_to_sale",
    "update_sale",
    "update_product_in_sale",
    "remove_product_from_sale",
]
