# ---------------------------------------------------------------------------
# ARQUIVO: pagination.py
# MÓDULO: Schemas Pydantic (DTOs)
# DESCRIÇÃO: Define regras de validação, tipos e documentação OpenAPI.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Union, Annotated, TYPE_CHECKING

# ===========================================================================
# SCHEMA BASE
# ===========================================================================

class Links(BaseModel):
    next: Optional[str] = Field(
        None,
        description="Link para a próxima página"
    )
    prev: Optional[str] = Field(
        None,
        description="Link para a página anterior"
    )


class PaginationBase(BaseModel):
    total_items: int = Field(
        ...,
        description="Descreve a quantidade total de itens"
    )
    page: int = Field(
        ...,
        description="Descreve a página atual"
    )
    limit: int = Field(
        ...,
        description="Descreve a quantidade de itens por página"
    )
    total_pages: int = Field(
        ...,
        description="Descreve a quantidade total de páginas"
    )
    links: Optional[Links] = Field(
        None,
        description="Links para paginação"
    )

    model_config = ConfigDict(
        from_attributes=True,
    )


# ===========================================================================
# SCHEMAS DE PAGINAÇÃO POR ENTIDADE
# ===========================================================================

from app.schemas.cliente import ClienteRead  # noqa: E402


class ClientePaginationRead(PaginationBase):
    items: List[ClienteRead] = Field(..., description="Lista de clientes")
    filters: Optional[dict] = Field(None, description="Filtros aplicados na busca")


