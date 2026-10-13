# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/orcamento/__init__.py
# DESCRICAO: Acesso ao banco dos orcamentos.
#
# Era um arquivo so (orcamento.py) ate 13/10/2026; virou pacote:
#   consultas.py - buscar orcamento e item, listar e resumo por status
#   escrita.py   - criar, atualizar e apagar orcamento e itens
#
# Este __init__ reexporta tudo: `from app.db.crud import orcamento` continua
# valendo como antes.
# ---------------------------------------------------------------------------

from app.db.crud.orcamento.consultas import (
    get_orcamento_by_id,
    get_product_by_id,
    get_orcamentos_by_search,
    get_orcamentos_status,
)

from app.db.crud.orcamento.escrita import (
    create_orcamento,
    add_product_to_orcamento,
    update_orcamento,
    update_product_in_orcamento,
    remove_product_from_orcamento,
    delete_orcamento,
)

__all__ = [
    "get_orcamento_by_id",
    "get_product_by_id",
    "get_orcamentos_by_search",
    "get_orcamentos_status",
    "create_orcamento",
    "add_product_to_orcamento",
    "update_orcamento",
    "update_product_in_orcamento",
    "remove_product_from_orcamento",
    "delete_orcamento",
]
