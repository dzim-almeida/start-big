# ---------------------------------------------------------------------------
# ARQUIVO: schemas/servico/__init__.py
# DESCRIÇÃO: Schemas Pydantic (modelos de dados) para validação de
#            entrada (Create/Update) e saída (Read) da API de Serviços.
#
# Era um arquivo so (servico.py) ate 13/10/2026; virou pacote:
#   cadastro.py - entrada (criar e editar)
#   leitura.py  - saida e estatisticas
#   consulta.py - filtros e pagina
#
# Este __init__ reexporta tudo: `from app.schemas.servico import ...` continua
# valendo como antes.
# ---------------------------------------------------------------------------

from app.schemas.servico.cadastro import (
    ServicoCreate,
    ServicoUpdate,
)

from app.schemas.servico.leitura import (
    ServicoRead,
    ServicoStats,
)

from app.schemas.servico.consulta import (
    ServicoFilterParams,
    ServicoQuery,
)

__all__ = [
    "ServicoCreate",
    "ServicoUpdate",
    "ServicoRead",
    "ServicoStats",
    "ServicoFilterParams",
    "ServicoQuery",
]
