# ---------------------------------------------------------------------------
# ARQUIVO: schemas/servico/consulta.py
# DESCRICAO: Schemas de servico - filtros e pagina.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Sequence
from app.schemas.pagination import PaginationBase as Pagination
from app.schemas.servico.leitura import ServicoRead


    
    # Nota: O 'model_config' e o 'example' são herdados de ServicoCreate
    # e podem ser sobrescritos aqui se necessário.

class ServicoFilterParams(BaseModel):
    search: Optional[str] = Field(
        None,
        description="Query de Busca"
    )
    active: Optional[bool] = Field(
        None,
        description="Filtro de status ativo/inativo"
    )

    model_config = ConfigDict(
        from_attributes=True,
    )


class ServicoQuery(Pagination):
    filters: ServicoFilterParams
    items: Sequence[ServicoRead]
