# ---------------------------------------------------------------------------
# ARQUIVO: services/funcionario/__init__.py
# DESCRICAO: Gestao de equipe - funcionarios e cargos.
#
# Era um arquivo so (funcionario.py) ate 12/10/2026; virou pacote:
#   cadastro.py  - criar, buscar, editar, trocar o cargo, ativar/desativar
#   acesso.py    - conceder login a quem ja e funcionario
#   cargo.py     - era services/cargo.py (o cadastro de cargos)
#
# Este __init__ reexporta so o que era funcionario.py. O cargo NAO e
# reexportado: os dois tinham `update_cargo_funcionario` e `not_found_exce`
# com sentidos diferentes. Use `from app.services.funcionario import cargo`.
# ---------------------------------------------------------------------------

from app.services.funcionario.cadastro import (
    conflict_funcionario_exce,
    not_found_exce,
    validation_exce,
    unique_fields,
    validators,
    create_funcionario,
    get_funcionario_by_search,
    funcionario_exists,
    update_funcionario_by_id,
    update_cargo_funcionario,
    toggle_active_disable_funcionario_by_id,
)

from app.services.funcionario.acesso import (
    conceder_acesso,
)

__all__ = [
    "conflict_funcionario_exce",
    "not_found_exce",
    "validation_exce",
    "unique_fields",
    "validators",
    "create_funcionario",
    "get_funcionario_by_search",
    "funcionario_exists",
    "update_funcionario_by_id",
    "update_cargo_funcionario",
    "toggle_active_disable_funcionario_by_id",
    "conceder_acesso",
]
