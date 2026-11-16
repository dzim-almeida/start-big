# ---------------------------------------------------------------------------
# ARQUIVO: schemas/endereco/__init__.py
# DESCRIÇÃO: Schemas Pydantic para validação de dados de Endereço.
#            Define as estruturas de entrada (Endereco), saída (EnderecoRead)
#            e atualização (EnderecoUpdate).
#
# Era um arquivo so (endereco.py) ate 13/10/2026; virou pacote:
#   entrada.py - Endereco e EnderecoUpdate
#   leitura.py - EnderecoRead
#
# Este __init__ reexporta tudo: `from app.schemas.endereco import ...` continua
# valendo como antes (cliente, empresa, fornecedor, funcionario e login usam).
# ---------------------------------------------------------------------------

from app.schemas.endereco.entrada import (
    Endereco,
    EnderecoUpdate,
)

from app.schemas.endereco.leitura import (
    EnderecoRead,
)

__all__ = [
    "Endereco",
    "EnderecoUpdate",
    "EnderecoRead",
]
