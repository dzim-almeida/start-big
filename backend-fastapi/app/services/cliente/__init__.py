# ---------------------------------------------------------------------------
# ARQUIVO: services/cliente/__init__.py
# DESCRICAO: Regras de negocio do cadastro de clientes (PF e PJ).
#
# Era um arquivo so (cliente.py) ate 12/10/2026; virou pacote por assunto:
#   cadastro.py   - criar PF/PJ, editar, ativar/desativar, busca, unicidade
#   historico.py  - historico de equipamentos do cliente
#
# Este __init__ reexporta tudo: `from app.services import cliente` continua
# funcionando como antes.
# ---------------------------------------------------------------------------

from app.services.cliente.cadastro import (
    not_found_exce,
    conflito_dados_exce,
    validation_exce,
    VALIDATORS_MAP,
    FIELD_LABELS,
    _validar_unicidade_cliente,
    _get_cliente_or_raise,
    get_cliente_by_id,
    create_cliente_pf,
    create_cliente_pj,
    get_cliente_by_search,
    get_cliente_simple_by_search,
    cliente_exists,
    update_cliente_by_id,
    toggle_active_disable_cliente_by_id,
)

from app.services.cliente.historico import (
    EQUIPMENT_HISTORY_LIMIT,
    get_equipamentos_historico_by_cliente_id,
)

__all__ = [
    "not_found_exce",
    "conflito_dados_exce",
    "validation_exce",
    "VALIDATORS_MAP",
    "FIELD_LABELS",
    "_validar_unicidade_cliente",
    "_get_cliente_or_raise",
    "get_cliente_by_id",
    "create_cliente_pf",
    "create_cliente_pj",
    "get_cliente_by_search",
    "get_cliente_simple_by_search",
    "cliente_exists",
    "update_cliente_by_id",
    "toggle_active_disable_cliente_by_id",
    "EQUIPMENT_HISTORY_LIMIT",
    "get_equipamentos_historico_by_cliente_id",
]
