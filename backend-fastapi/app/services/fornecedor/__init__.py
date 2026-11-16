# ---------------------------------------------------------------------------
# ARQUIVO: services/fornecedor/__init__.py
# DESCRIÇÃO: Camada de serviço com a lógica de negócio para Fornecedores.
#            Implementa o CRUD completo, incluindo a gestão de
#            endereços polimórficos.
#
# Era um arquivo so (fornecedor.py) ate 13/10/2026; virou pacote:
#   validacao.py - excecoes e campos unicos (CNPJ, IE)
#   cadastro.py  - criar, editar, ativar e desativar
#   consultas.py - busca
#
# Este __init__ reexporta tudo: `from app.services import fornecedor` continua
# valendo como antes.
# ---------------------------------------------------------------------------

from app.services.fornecedor.validacao import (
    conflict_exce,
    not_found_exce,
    validation_exce,
    unique_fields,
    validators,
)

from app.services.fornecedor.cadastro import (
    create_fornecedor,
    update_fornecedor_by_id,
    toggle_active_disable_fornecedor_by_id,
)

from app.services.fornecedor.consultas import (
    get_fornecedor_by_search,
)

__all__ = [
    "conflict_exce",
    "not_found_exce",
    "validation_exce",
    "unique_fields",
    "validators",
    "create_fornecedor",
    "update_fornecedor_by_id",
    "toggle_active_disable_fornecedor_by_id",
    "get_fornecedor_by_search",
]
