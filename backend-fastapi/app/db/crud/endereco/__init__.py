# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/endereco/__init__.py
# DESCRICAO: Acesso ao banco dos enderecos.
#
# Era um arquivo so (endereco.py) ate 13/10/2026; virou pacote:
#   consultas.py - buscar endereco
#   escrita.py   - apagar endereco
#
# Este __init__ reexporta tudo: `from app.db.crud import endereco` continua
# valendo como antes.
# ---------------------------------------------------------------------------

from app.db.crud.endereco.consultas import (
    get_address_by_id,
)

from app.db.crud.endereco.escrita import (
    delete_address_by_id,
)

__all__ = [
    "get_address_by_id",
    "delete_address_by_id",
]
