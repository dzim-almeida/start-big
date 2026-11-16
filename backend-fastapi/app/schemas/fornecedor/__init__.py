# ---------------------------------------------------------------------------
# ARQUIVO: schemas/fornecedor/__init__.py
# DESCRIÇÃO: Schemas Pydantic para validação de dados de Fornecedor.
#            Define as estruturas de entrada (Create/Update) e saída (Read).
#
# Era um arquivo so (fornecedor.py) ate 13/10/2026; virou pacote:
#   cadastro.py - entrada (criar e editar)
#   leitura.py  - saida
#
# Este __init__ reexporta tudo: `from app.schemas.fornecedor import ...` continua
# valendo como antes.
# ---------------------------------------------------------------------------

from app.schemas.fornecedor.cadastro import (
    FornecedorCreate,
    FornecedorUpdate,
)

from app.schemas.fornecedor.leitura import (
    FornecedorRead,
)

__all__ = [
    "FornecedorCreate",
    "FornecedorUpdate",
    "FornecedorRead",
]
