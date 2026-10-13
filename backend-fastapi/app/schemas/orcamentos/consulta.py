# ---------------------------------------------------------------------------
# ARQUIVO: schemas/orcamentos/consulta.py
# DESCRICAO: Schemas do orcamento - filtros e listagem.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Sequence
from app.schemas.orcamentos.cadastro import OrcamentoSimpleRead


class OrcamentoSearchFilters(BaseModel):
    search: Optional[str] = Field(None, max_length=255, description="Termo de busca")
    convertido: Optional[bool] = Field(None, description="Filtrar por status de conversao")
    funcionario_id: Optional[int] = Field(None, description="Filtrar por funcionario")


class OrcamentoListRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    filters: OrcamentoSearchFilters = Field(..., description="Filtros aplicados")
    orcamentos: Sequence[OrcamentoSimpleRead] = Field(default_factory=list, description="Lista de orcamentos")
    total: int = Field(0, ge=0, description="Total de orcamentos encontrados")
    page: int = Field(1, ge=1, description="Pagina atual")
    limit: int = Field(20, ge=1, le=100, description="Limite por pagina")
    total_pages: int = Field(1, ge=1, description="Total de paginas")
    links: dict = Field(..., description="Links de navegacao")
