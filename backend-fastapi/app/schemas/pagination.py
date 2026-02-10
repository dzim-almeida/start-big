# ---------------------------------------------------------------------------
# ARQUIVO: pagination.py
# MÓDULO: Schemas Pydantic (DTOs)
# DESCRIÇÃO: Define regras de validação, tipos e documentação OpenAPI.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field

# ===========================================================================
# SCHEMA BASE
# ===========================================================================

class PaginationBase(BaseModel):
    items: int = Field(
        ...,
        description="Descreve a quantidade de itens retornados"
    )
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


