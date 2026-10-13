# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/fornecedor/__init__.py
# DESCRIÇÃO: Funções de CRUD (Create, Read, Update, Delete) para interagir
#            com a tabela de Fornecedores no banco de dados (Repository Layer).
#
# Era um arquivo so (fornecedor.py) ate 13/10/2026; virou pacote:
#   consultas.py - buscas e verificacao de conflito
#   escrita.py   - criar e atualizar
#
# Este __init__ reexporta tudo: `from app.db.crud import fornecedor` continua
# valendo como antes.
# ---------------------------------------------------------------------------

from app.db.crud.fornecedor.consultas import (
    SearchMethod,
    verify_fornecedor_conflict,
    get_fornecedor_by_id,
    get_fornecedor_by_cnpj,
    get_fornecedor_by_ie,
    get_fornecedor_by_search,
)

from app.db.crud.fornecedor.escrita import (
    create_fornecedor,
    update_fornecedor,
)

__all__ = [
    "SearchMethod",
    "verify_fornecedor_conflict",
    "get_fornecedor_by_id",
    "get_fornecedor_by_cnpj",
    "get_fornecedor_by_ie",
    "get_fornecedor_by_search",
    "create_fornecedor",
    "update_fornecedor",
]
