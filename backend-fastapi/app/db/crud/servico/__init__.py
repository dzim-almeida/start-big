# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/servico/__init__.py
# MÓDULO: Acesso a Dados (Repository)
# DESCRIÇÃO: Executa queries SQL via SQLAlchemy para manipulação de Serviços.
#
# Era um arquivo so (servico.py) ate 13/10/2026; virou pacote:
#   consultas.py - buscas (com o resgate por similaridade) e estatisticas
#   escrita.py   - criar e atualizar
#
# Este __init__ reexporta tudo: `from app.db.crud import servico` continua
# valendo como antes.
# ---------------------------------------------------------------------------

from app.db.crud.servico.consultas import (
    _CAMPOS_BUSCA,
    _TETO_RESGATE,
    get_servico_by_id,
    _resgatar_por_similaridade,
    get_servico_by_search,
    get_servico_stats,
    get_servico_by_description,
)

from app.db.crud.servico.escrita import (
    create_servico,
    update_servico,
)

__all__ = [
    "_CAMPOS_BUSCA",
    "_TETO_RESGATE",
    "get_servico_by_id",
    "_resgatar_por_similaridade",
    "get_servico_by_search",
    "get_servico_stats",
    "get_servico_by_description",
    "create_servico",
    "update_servico",
]
