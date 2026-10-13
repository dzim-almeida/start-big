# ---------------------------------------------------------------------------
# ARQUIVO: services/servico/__init__.py
# MÓDULO: Regras de Negócio (Service Layer)
# DESCRIÇÃO: Orquestra validações, verificação de conflitos e persistência
#            para operações relacionadas a Serviços (o cadastro; o fiscal do
#            serviço fica em services/fiscal/cadastro/servico.py).
#
# Era um arquivo so (servico.py) ate 13/10/2026; virou pacote:
#   cadastro.py  - criar, editar, ativar e desativar (e as excecoes)
#   consultas.py - busca e estatisticas
#
# Este __init__ reexporta tudo: `from app.services import servico` continua
# valendo como antes.
# ---------------------------------------------------------------------------

from app.services.servico.cadastro import (
    not_found_exce,
    conflict_exce,
    create_servico,
    update_servico_by_id,
    toggle_active_disable_servico_by_id,
)

from app.services.servico.consultas import (
    SERVICE_URL,
    get_servico_by_search,
    get_servico_stats,
)

__all__ = [
    "not_found_exce",
    "conflict_exce",
    "create_servico",
    "update_servico_by_id",
    "toggle_active_disable_servico_by_id",
    "SERVICE_URL",
    "get_servico_by_search",
    "get_servico_stats",
]
