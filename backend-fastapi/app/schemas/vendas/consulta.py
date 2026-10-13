# ---------------------------------------------------------------------------
# ARQUIVO: schemas/vendas/consulta.py
# DESCRICAO: Schemas da venda - filtros e listagem.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field, ConfigDict
from app.core.enum import VendaStatus
from typing import Optional, Sequence
from app.schemas.vendas.cadastro import VendaSimpleRead


class VendaSearchFilters(BaseModel):
    search: Optional[str] = Field(None, max_length=255, description="Termo de busca para filtrar vendas por número da venda, nome do cliente ou nome do funcionário")
    status: Optional[VendaStatus] = Field(None, description="Status para filtrar as vendas")
    funcionario_id: Optional[int] = Field(None, description="Filtrar vendas pelo funcionário responsável")
    na_fila: Optional[bool] = Field(
        None,
        description="True traz só as vendas entregues ao caixa; False só as em montagem; nulo traz todas",
    )


class VendaListRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    filters: VendaSearchFilters = Field(..., description="Filtros para pesquisa de vendas")
    vendas: Sequence[VendaSimpleRead] = Field(default_factory=list, description="Lista de vendas retornadas para os filtros aplicados")
    total: int = Field(0, ge=0, description="Total de vendas encontradas para os filtros aplicados")
    page: int = Field(1, ge=1, description="Número da página atual")
    limit: int = Field(20, ge=1, le=100, description="Número máximo de vendas retornadas por página")
    total_pages: int = Field(1, ge=1, description="Número total de páginas disponíveis para os filtros aplicados")
    links: dict = Field(..., description="Links de navegação para a próxima e anterior página, se aplicável")
