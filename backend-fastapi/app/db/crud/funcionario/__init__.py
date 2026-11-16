# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/funcionario/__init__.py
# DESCRICAO: Acesso ao banco de funcionarios e cargos.
#
# Era um arquivo so (funcionario.py) ate 12/10/2026; virou pacote:
#   consultas.py - buscas e verificacao de conflito
#   escrita.py   - criar e atualizar
#   cargo.py     - era db/crud/cargo.py
#
# Este __init__ reexporta o que era funcionario.py. O cargo fica no submodulo:
# `from app.db.crud.funcionario import cargo`.
# ---------------------------------------------------------------------------

from app.db.crud.funcionario.consultas import (
    verify_funcionario_conflict,
    get_funcionario_by_id,
    get_funcionario_by_user_id,
    get_funcionario_by_cpf,
    get_funcionario_by_email,
    get_funcionario_by_rg,
    get_funcionario_by_ctps,
    get_funcionario_by_cnh,
    get_funcionario_by_search,
)

from app.db.crud.funcionario.escrita import (
    create_funcionario,
    update_funcionario_in_db,
)

__all__ = [
    "verify_funcionario_conflict",
    "get_funcionario_by_id",
    "get_funcionario_by_user_id",
    "get_funcionario_by_cpf",
    "get_funcionario_by_email",
    "get_funcionario_by_rg",
    "get_funcionario_by_ctps",
    "get_funcionario_by_cnh",
    "get_funcionario_by_search",
    "create_funcionario",
    "update_funcionario_in_db",
]
