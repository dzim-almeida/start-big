# ---------------------------------------------------------------------------
# ARQUIVO: endpoints/dashboard.py
# DESCRICAO: Endpoints read-only para o Dashboard.
#
# Estrutura:
#   GET /stats?periodo=hoje|semana|mes  → Metricas com variacao
#   GET /os-vencendo                    → OS proximas/passadas do prazo
#   GET /estoque-baixo                  → Produtos com estoque critico
#   GET /ultimas-vendas                 → Vendas recentes
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.depends import get_current_active_user, get_db
from app.schemas.dashboard import (
    DashboardStats,
    OSVencendoResponse,
    EstoqueBaixoResponse,
    UltimasVendasResponse,
)
from app.services import dashboard as dashboard_service

router = APIRouter()


@router.get(
    "/stats",
    response_model=DashboardStats,
    summary="Metricas do Dashboard",
    description="Retorna vendas totais, OS criadas, novos clientes e ticket medio com variacao percentual.",
)
def obter_stats(
    user_token: dict = Depends(get_current_active_user),
    *,
    db: Session = Depends(get_db),
    periodo: str = Query("hoje", pattern="^(hoje|semana|mes)$", description="Periodo de filtragem"),
):
    return dashboard_service.get_dashboard_stats(db, periodo, user_token["empresa_id"])


@router.get(
    "/os-vencendo",
    response_model=OSVencendoResponse,
    summary="OS Proximas do Prazo",
    description="Retorna ordens de servico ativas ordenadas por urgencia de prazo.",
)
def obter_os_vencendo(
    user_token: dict = Depends(get_current_active_user),
    *,
    db: Session = Depends(get_db),
):
    return dashboard_service.get_os_vencendo(db, user_token["empresa_id"])


@router.get(
    "/estoque-baixo",
    response_model=EstoqueBaixoResponse,
    summary="Produtos com Estoque Critico",
    description="Retorna produtos com estoque zerado ou abaixo da quantidade minima.",
)
def obter_estoque_baixo(
    user_token: dict = Depends(get_current_active_user),
    *,
    db: Session = Depends(get_db),
):
    return dashboard_service.get_estoque_baixo(db)


@router.get(
    "/ultimas-vendas",
    response_model=UltimasVendasResponse,
    summary="Vendas Recentes",
    description="Retorna as ultimas vendas e orcamentos realizados.",
)
def obter_ultimas_vendas(
    user_token: dict = Depends(get_current_active_user),
    *,
    db: Session = Depends(get_db),
):
    return dashboard_service.get_ultimas_vendas(db, user_token["empresa_id"])
