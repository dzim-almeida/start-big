# ---------------------------------------------------------------------------
# ARQUIVO: schemas/cliente/pf_ou_pj.py
# DESCRICAO: Clientes - PF ou PJ num tipo so: o Pydantic escolhe pelo campo
#            `tipo` (discriminador). E o que os endpoints recebem e devolvem.
# ---------------------------------------------------------------------------

from pydantic import Field
from typing import Annotated, Union
from app.schemas.cliente.pessoa_fisica import ClientePFCreate, ClientePFRead, ClientePFSimpleRead, ClientePFUpdate
from app.schemas.cliente.pessoa_juridica import ClientePJCreate, ClientePJRead, ClientePJSimpleRead, ClientePJUpdate


# ===========================================================================
# UNIÕES POLIMÓRFICAS
# ===========================================================================

ClienteCreate = Annotated[
    Union[ClientePFCreate, ClientePJCreate],
    Field(discriminator="tipo")
]


ClienteRead = Annotated[
    Union[ClientePFRead, ClientePJRead],
    Field(discriminator="tipo")
]


ClienteSimpleRead = Annotated[
    Union[ClientePFSimpleRead, ClientePJSimpleRead],
    Field(discriminator="tipo")
]


ClienteUpdate = Annotated[
    Union[ClientePFUpdate, ClientePJUpdate],
    Field(discriminator="tipo")
]
