# ---------------------------------------------------------------------------
# ARQUIVO: schemas/dashboard.py
# DESCRICAO: Schemas Pydantic para os endpoints do Dashboard.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal


# ===========================================================================
# Stats Cards
# ===========================================================================

class DashboardStats(BaseModel):
    vendas_total: int = Field(0, description="Valor total de vendas finalizadas no periodo (centavos)")
    vendas_total_variacao: float = Field(0.0, description="Variacao percentual vs periodo anterior")

    os_count: int = Field(0, description="Quantidade de OS criadas no periodo")
    os_count_variacao: float = Field(0.0, description="Variacao percentual vs periodo anterior")

    novos_clientes: int = Field(0, description="Novos clientes cadastrados no periodo")
    novos_clientes_variacao: float = Field(0.0, description="Variacao percentual vs periodo anterior")

    ticket_medio: int = Field(0, description="Ticket medio geral combinado vendas + OS (centavos)")
    ticket_medio_variacao: float = Field(0.0, description="Variacao percentual vs periodo anterior")


# ===========================================================================
# OS Vencendo
# ===========================================================================

class OSVencendoItem(BaseModel):
    numero_os: str = Field(..., description="Numero sequencial da OS")
    cliente_nome: str = Field(..., description="Nome do cliente vinculado")
    defeito_relatado: str = Field(..., description="Defeito relatado pelo cliente")
    data_previsao: datetime = Field(..., description="Data prevista para conclusao")
    urgencia: Literal["vermelho", "amarelo", "verde"] = Field(..., description="Faixa de urgencia")


class OSVencendoResponse(BaseModel):
    items: list[OSVencendoItem] = Field(default_factory=list)


# ===========================================================================
# Estoque Baixo
# ===========================================================================

class EstoqueBaixoItem(BaseModel):
    produto_id: int = Field(..., description="ID do produto")
    nome: str = Field(..., description="Nome do produto")
    quantidade: int = Field(..., description="Quantidade atual em estoque")
    quantidade_minima: Optional[int] = Field(None, description="Quantidade minima configurada")
    status: Literal["zerado", "baixo"] = Field(..., description="Status do estoque")


class EstoqueBaixoResponse(BaseModel):
    items: list[EstoqueBaixoItem] = Field(default_factory=list)


# ===========================================================================
# Ultimas Vendas
# ===========================================================================

class UltimaVendaItem(BaseModel):
    id: int = Field(..., description="ID da venda")
    cliente_nome: Optional[str] = Field(None, description="Nome do cliente")
    total: int = Field(0, description="Total da venda (centavos)")
    status: str = Field(..., description="Status da venda")
    criado_em: datetime = Field(..., description="Data de criacao")


class UltimasVendasResponse(BaseModel):
    items: list[UltimaVendaItem] = Field(default_factory=list)
