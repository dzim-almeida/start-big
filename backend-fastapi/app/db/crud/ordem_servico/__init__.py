# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/ordem_servico/__init__.py
# DESCRICAO: Queries SQL via SQLAlchemy para manipulação de Ordens de Serviço.
#
# Estrutura das funções:
#   LEITURA  → select sem efeito colateral; retorna model ou None
#   ESCRITA  → modifica estado do banco; usa flush() + refresh() (sem commit)
#              O commit é responsabilidade do _handle_db_transaction no endpoint.
#
# Era um arquivo so (ordem_servico.py) ate 13/10/2026; virou pacote:
#   consultas.py   - leitura da OS, numeracao, item e foto, abandono e atrasadas
#   objetos.py     - objeto/equipamento: por identificador, revisao, ultima OS
#   escrita.py     - criar e atualizar OS, item, pagamento e foto
#   nota_fiscal.py - dados fiscais da OS (era db/crud/ordem_servico_nota_fiscal.py)
#
# Este __init__ reexporta o que era ordem_servico.py. A nota fiscal fica no
# submodulo (os nomes dela sao genericos: create, update, upsert):
# `from app.db.crud.ordem_servico import nota_fiscal`.
# ---------------------------------------------------------------------------

from app.db.crud.ordem_servico.consultas import (
    get_ordem_servico_by_id,
    get_ordem_servico_by_numero_os,
    get_ordens_servico_by_search,
    get_ordens_servico_by_cliente_id,
    get_ordem_servico_stats,
    get_next_numero,
    get_os_item_by_id,
    get_os_foto_by_id,
    get_os_abandono,
    get_os_atrasadas,
)

from app.db.crud.ordem_servico.objetos import (
    get_ordens_by_objeto_id,
    get_objetos_com_revisao_agendada,
    get_objeto_ativo_by_cliente_e_serie,
    _identificador_normalizado_sql,
    get_objetos_ativos_por_identificador,
    buscar_objetos_por_identificador,
    get_ultima_os_do_objeto,
)

from app.db.crud.ordem_servico.escrita import (
    create_ordem_servico,
    update_ordem_servico,
    create_os_item,
    update_os_item,
    delete_os_item,
    create_os_pagamento,
    create_os_foto,
    delete_os_foto,
)

__all__ = [
    "get_ordem_servico_by_id",
    "get_ordem_servico_by_numero_os",
    "get_ordens_servico_by_search",
    "get_ordens_servico_by_cliente_id",
    "get_ordem_servico_stats",
    "get_next_numero",
    "get_os_item_by_id",
    "get_os_foto_by_id",
    "get_os_abandono",
    "get_os_atrasadas",
    "get_ordens_by_objeto_id",
    "get_objetos_com_revisao_agendada",
    "get_objeto_ativo_by_cliente_e_serie",
    "_identificador_normalizado_sql",
    "get_objetos_ativos_por_identificador",
    "buscar_objetos_por_identificador",
    "get_ultima_os_do_objeto",
    "create_ordem_servico",
    "update_ordem_servico",
    "create_os_item",
    "update_os_item",
    "delete_os_item",
    "create_os_pagamento",
    "create_os_foto",
    "delete_os_foto",
]
