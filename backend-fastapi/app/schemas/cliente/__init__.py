# ---------------------------------------------------------------------------
# ARQUIVO: schemas/cliente/__init__.py
# DESCRICAO: Schemas Pydantic do cadastro de clientes.
#
# Era um arquivo so (cliente.py) ate 12/10/2026; virou pacote por assunto:
#   comum.py            - ClienteBase
#   pessoa_fisica.py    - ClientePF*
#   pessoa_juridica.py  - ClientePJ*
#   pf_ou_pj.py         - ClienteCreate/Read/SimpleRead/Update (PF ou PJ pelo `tipo`)
#   historico.py        - EquipamentoHistoricoRead
#
# Este __init__ reexporta tudo: `from app.schemas.cliente import ...`
# continua funcionando como antes.
# ---------------------------------------------------------------------------

from app.schemas.cliente.comum import (
    ClienteBase,
)

from app.schemas.cliente.pessoa_fisica import (
    ClientePFCreate,
    ClientePFRead,
    ClientePFSimpleRead,
    ClientePFUpdate,
)

from app.schemas.cliente.pessoa_juridica import (
    ClientePJCreate,
    ClientePJRead,
    ClientePJSimpleRead,
    ClientePJUpdate,
)

from app.schemas.cliente.pf_ou_pj import (
    ClienteCreate,
    ClienteRead,
    ClienteSimpleRead,
    ClienteUpdate,
)

from app.schemas.cliente.historico import (
    EquipamentoHistoricoRead,
)

__all__ = [
    "ClienteBase",
    "ClientePFCreate",
    "ClientePFRead",
    "ClientePFSimpleRead",
    "ClientePFUpdate",
    "ClientePJCreate",
    "ClientePJRead",
    "ClientePJSimpleRead",
    "ClientePJUpdate",
    "ClienteCreate",
    "ClienteRead",
    "ClienteSimpleRead",
    "ClienteUpdate",
    "EquipamentoHistoricoRead",
]
