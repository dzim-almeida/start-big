# ---------------------------------------------------------------------------
# ARQUIVO: services/endereco/__init__.py
# DESCRIÇÃO: Camada de serviço com a lógica de negócio para Endereços.
#            Contém funções utilitárias para criação e atualização
#            de endereços polimórficos, usados por outras entidades (Empresa,
#            Funcionario, Cliente, Fornecedor).
#
# Era um arquivo so (endereco.py) ate 13/10/2026; virou pacote:
#   escrita.py - criar, atualizar e apagar os enderecos de uma entidade
#
# Este __init__ reexporta tudo: `from app.services import endereco` continua
# valendo como antes.
# ---------------------------------------------------------------------------

from app.services.endereco.escrita import (
    address_to_db,
    update_address_in_db,
    delete_address_in_db,
)

__all__ = [
    "address_to_db",
    "update_address_in_db",
    "delete_address_in_db",
]
