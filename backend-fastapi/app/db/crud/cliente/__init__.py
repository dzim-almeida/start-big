# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/cliente/__init__.py
# DESCRICAO: Acesso ao banco do cadastro de clientes.
#
# Era um arquivo so (cliente.py) ate 12/10/2026; virou pacote por assunto:
#   consultas.py  - buscas (id, CPF, CNPJ, e-mail, RG, IE), pesquisa e conflito
#   escrita.py    - criar, atualizar, desativar
#   historico.py  - objetos/equipamentos do cliente
#
# Este __init__ reexporta tudo: `from app.db.crud import cliente` continua
# funcionando como antes.
# ---------------------------------------------------------------------------

from app.db.crud.cliente.consultas import (
    _campos_busca,
    verify_cliente_conflict,
    get_cliente_by_id,
    get_cliente_by_email,
    get_cliente_by_cpf,
    get_cliente_by_cnpj,
    get_cliente_by_rg,
    get_cliente_by_ie,
    get_cliente_by_search,
    get_cliente_simple_by_search,
)

from app.db.crud.cliente.escrita import (
    create_cliente,
    update_cliente,
    deactivate_cliente,
)

from app.db.crud.cliente.historico import (
    get_objetos_by_cliente_id,
)

__all__ = [
    "_campos_busca",
    "verify_cliente_conflict",
    "get_cliente_by_id",
    "get_cliente_by_email",
    "get_cliente_by_cpf",
    "get_cliente_by_cnpj",
    "get_cliente_by_rg",
    "get_cliente_by_ie",
    "get_cliente_by_search",
    "get_cliente_simple_by_search",
    "create_cliente",
    "update_cliente",
    "deactivate_cliente",
    "get_objetos_by_cliente_id",
]
