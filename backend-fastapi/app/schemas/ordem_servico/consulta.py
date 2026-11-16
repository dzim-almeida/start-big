# ---------------------------------------------------------------------------
# ARQUIVO: schemas/ordem_servico/consulta.py
# DESCRICAO: Schemas da OS - filtros de listagem, pagina e estatisticas.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field
from typing import Optional, Sequence
from app.core.enum import (
    OrdemServicoStatus,
    SituacaoEquipamento,
)
from app.schemas.comum.paginacao import PaginationBase as Pagination
from app.schemas.ordem_servico.ordem import OrdemServicoRead


# ===========================================================================
# FILTROS E PAGINAÇÃO
# ===========================================================================

class OrdemServicoFilterParams(BaseModel):
    """Query parameters para listagem e busca de OS."""
    search: Optional[str] = Field(
        None,
        description="Busca por número da OS, nome ou razão social do cliente"
    )
    status: Optional[OrdemServicoStatus] = Field(
        None,
        description="Filtro por status: ABERTA, EM_ANDAMENTO, AGUARDANDO_PECAS, AGUARDANDO_APROVACAO, AGUARDANDO_RETIRADA, FINALIZADA ou CANCELADA"
    )
    situacao_equipamento: Optional[SituacaoEquipamento] = Field(
        None,
        description=(
            "Filtro pelo desfecho do objeto: REPARADO, SEM_REPARO ou CONDENADO. "
            "Considera apenas OS FINALIZADA — reabrir não limpa o campo."
        )
    )
    priority_sort: Optional[bool] = Field(
        None,
        description="Se true, ordena por prioridade (URGENTE → ALTA → NORMAL → BAIXA)"
    )


class OrdemServicoQuery(Pagination):
    """Resposta paginada de listagem de OS."""
    filters: OrdemServicoFilterParams
    items: Sequence[OrdemServicoRead]


# ===========================================================================
# ESTATÍSTICAS
# ===========================================================================

class OrdemServicoStats(BaseModel):
    """Estatísticas agregadas das Ordens de Serviço."""
    total: int = Field(..., description="Total de OS no sistema")
    abertas: int = Field(..., description="OS com status ABERTA")
    finalizadas: int = Field(..., description="OS com status FINALIZADA")
    ticket_medio: int = Field(..., description="Valor médio das OS finalizadas em centavos")
