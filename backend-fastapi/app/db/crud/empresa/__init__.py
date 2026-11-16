# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/empresa/__init__.py
# DESCRICAO: Acesso ao banco da empresa (uma por instalacao).
#
# Era um arquivo so (empresa.py) ate 12/10/2026; virou pacote:
#   consultas.py - por id e a empresa atual
#   escrita.py   - criar e atualizar
#
# Este __init__ reexporta tudo: `from app.db.crud import empresa` continua
# valendo como antes.
# ---------------------------------------------------------------------------

from app.db.crud.empresa.consultas import (
    get_empresa_by_id,
    get_empresa_atual,
)

from app.db.crud.empresa.escrita import (
    create_empresa,
    update_empresa,
)

__all__ = [
    "get_empresa_by_id",
    "get_empresa_atual",
    "create_empresa",
    "update_empresa",
]
