# ---------------------------------------------------------------------------
# ARQUIVO: schemas/relatorio/os_performance.py
# DESCRICAO: Schemas de relatorio - desempenho de OS.
# ---------------------------------------------------------------------------

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


# ===========================================================================
# RELATORIO DE OS-PERFORMANCE (Fase 4b)
# ===========================================================================

class OSReparoResumo(BaseModel):
    """Desfecho das OS finalizadas no período (situacao_equipamento)."""
    reparado: int = 0
    sem_reparo: int = 0
    condenado: int = 0
    nao_informado: int = Field(0, description="Finalizadas sem situação registrada")
    taxa_reparo_pct: float = Field(0.0, description="% REPARADO sobre as finalizadas")


class OSStatusItem(BaseModel):
    """Quantidade de OS ativas por status atual (snapshot do backlog)."""
    status: str
    quantidade: int


class OSTecnicoItem(BaseModel):
    """Desempenho de um técnico (funcionário) nas OS finalizadas do período."""
    funcionario_id: int
    nome: str
    finalizadas: int
    tempo_medio_horas: Optional[float] = Field(None, description="Média de (finalização - criação) em horas")
    faturamento: int = Field(..., description="Σ valor_total das OS finalizadas (centavos)")


class RelatorioOSPerformance(BaseModel):
    """Desempenho de OS no período: throughput, tempo, reparo e por técnico."""
    inicio: date
    fim: date
    abertas: int = Field(..., description="OS criadas no período")
    finalizadas: int = Field(..., description="OS finalizadas no período")
    tempo_medio_horas: Optional[float] = Field(None, description="Tempo médio de conclusão (horas); None se não há finalizadas")
    faturamento_total: int = Field(..., description="Σ valor_total das OS finalizadas no período (centavos)")
    reparo: OSReparoResumo
    por_status: list[OSStatusItem] = Field(default_factory=list)
    por_tecnico: list[OSTecnicoItem] = Field(default_factory=list)
