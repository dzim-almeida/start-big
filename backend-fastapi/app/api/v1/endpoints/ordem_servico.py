# ---------------------------------------------------------------------------
# ARQUIVO: endpoints/ordem_servico.py
# DESCRICAO: Gerencia as Ordens de Servico (OS) do sistema.
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, status, Path, Query
from sqlalchemy.orm import Session
from typing import Sequence

from app.core.depends import check_permission, _handle_db_transaction
from app.db.session import get_db
from app.schemas.ordem_servico import (
    OrdemServicoCreate, OrdemServicoRead, OrdemServicoListRead,
    OrdemServicoUpdate, OrdemServicoFinalizar, OrdemServicoCancelar,
    OrdemServicoFilterParams, OrdemServicoQuery, OrdemServicoStats,
)
from app.services import ordem_servico as os_service

router = APIRouter()


# ===========================================================================
# ROTAS DE CRIACAO (POST)
# ===========================================================================

@router.post(
    "/",
    response_model=OrdemServicoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Nova OS",
    description="Cria uma nova Ordem de Servico."
)
def create_ordem_servico(
    user_token: dict = Depends(check_permission(required_permission="servico")),
    *,
    os_data: OrdemServicoCreate,
    db: Session = Depends(get_db)
):
    return _handle_db_transaction(db, os_service.create_ordem_servico, os_data)


# ===========================================================================
# ROTAS DE LEITURA (GET)
# ===========================================================================

@router.get(
    "/estatisticas",
    response_model=OrdemServicoStats,
    status_code=status.HTTP_200_OK,
    summary="Estatisticas das OS",
    description="Retorna estatisticas agregadas das Ordens de Servico."
)
def get_ordem_servico_stats(
    user_token: dict = Depends(check_permission(required_permission="servico")),
    *,
    db: Session = Depends(get_db)
):
    return _handle_db_transaction(db, os_service.get_ordem_servico_stats)


@router.get(
    "/proximo_numero",
    status_code=status.HTTP_200_OK,
    summary="Proximo Numero de OS",
    description="Retorna o proximo numero sequencial para criacao de OS."
)
def get_next_numero(
    user_token: dict = Depends(check_permission(required_permission="servico")),
    *,
    db: Session = Depends(get_db)
):
    return _handle_db_transaction(db, os_service.get_next_numero)


@router.get(
    "/",
    response_model=OrdemServicoQuery,
    status_code=status.HTTP_200_OK,
    summary="Listar OS",
    description="Retorna Ordens de Servico com filtros e paginacao."
)
def get_ordens_servico(
    user_token: dict = Depends(check_permission(required_permission="servico")),
    *,
    filters: OrdemServicoFilterParams = Depends(),
    page: int = Query(1, ge=1, description="Pagina atual"),
    limit: int = Query(10, ge=1, le=100, description="Itens por pagina"),
    db: Session = Depends(get_db)
):
    filters_dict = filters.model_dump(exclude_unset=True)
    return _handle_db_transaction(db, os_service.get_ordens_servico_by_search, filters_dict, page, limit)


@router.get(
    "/cliente/{cliente_id}",
    response_model=list[OrdemServicoListRead],
    status_code=status.HTTP_200_OK,
    summary="OS por Cliente",
    description="Retorna todas as OS de um cliente."
)
def get_ordens_servico_by_cliente(
    user_token: dict = Depends(check_permission(required_permission="servico")),
    cliente_id: int = Path(..., ge=1, description="ID do cliente"),
    *,
    db: Session = Depends(get_db)
):
    return _handle_db_transaction(db, os_service.get_ordens_servico_by_cliente, cliente_id)


@router.get(
    "/{os_id}",
    response_model=OrdemServicoRead,
    status_code=status.HTTP_200_OK,
    summary="Buscar OS por ID",
    description="Retorna uma OS completa pelo ID."
)
def get_ordem_servico_by_id(
    user_token: dict = Depends(check_permission(required_permission="servico")),
    os_id: int = Path(..., ge=1, description="ID da OS"),
    *,
    db: Session = Depends(get_db)
):
    return _handle_db_transaction(db, os_service.get_ordem_servico_by_id, os_id)


# ===========================================================================
# ROTAS DE ATUALIZACAO (PUT)
# ===========================================================================

@router.put(
    "/{os_id}",
    response_model=OrdemServicoRead,
    status_code=status.HTTP_200_OK,
    summary="Atualizar OS",
    description="Atualiza dados de uma OS existente."
)
def update_ordem_servico(
    user_token: dict = Depends(check_permission(required_permission="servico")),
    os_id: int = Path(..., ge=1, description="ID da OS"),
    *,
    os_data: OrdemServicoUpdate,
    db: Session = Depends(get_db)
):
    return _handle_db_transaction(db, os_service.update_ordem_servico, os_id, os_data)


@router.put(
    "/{os_id}/finalizar",
    response_model=OrdemServicoRead,
    status_code=status.HTTP_200_OK,
    summary="Finalizar OS",
    description="Finaliza uma OS com solucao e pagamentos."
)
def finalizar_ordem_servico(
    user_token: dict = Depends(check_permission(required_permission="servico")),
    os_id: int = Path(..., ge=1, description="ID da OS"),
    *,
    data: OrdemServicoFinalizar,
    db: Session = Depends(get_db)
):
    return _handle_db_transaction(db, os_service.finalizar_ordem_servico, os_id, data)


@router.put(
    "/{os_id}/cancelar",
    response_model=OrdemServicoRead,
    status_code=status.HTTP_200_OK,
    summary="Cancelar OS",
    description="Cancela uma OS com motivo opcional."
)
def cancelar_ordem_servico(
    user_token: dict = Depends(check_permission(required_permission="servico")),
    os_id: int = Path(..., ge=1, description="ID da OS"),
    *,
    data: OrdemServicoCancelar,
    db: Session = Depends(get_db)
):
    return _handle_db_transaction(db, os_service.cancelar_ordem_servico, os_id, data)


@router.put(
    "/{os_id}/reabrir",
    response_model=OrdemServicoRead,
    status_code=status.HTTP_200_OK,
    summary="Reabrir OS",
    description="Reabre uma OS finalizada ou cancelada."
)
def reabrir_ordem_servico(
    user_token: dict = Depends(check_permission(required_permission="servico")),
    os_id: int = Path(..., ge=1, description="ID da OS"),
    *,
    db: Session = Depends(get_db)
):
    return _handle_db_transaction(db, os_service.reabrir_ordem_servico, os_id)


@router.put(
    "/toggle_ativo/{os_id}",
    response_model=OrdemServicoRead,
    status_code=status.HTTP_200_OK,
    summary="Ativar/Desativar OS",
    description="Alterna o status logico (Soft Delete) de uma OS."
)
def toggle_ativo_ordem_servico(
    user_token: dict = Depends(check_permission(required_permission="servico")),
    os_id: int = Path(..., ge=1, description="ID da OS"),
    *,
    db: Session = Depends(get_db)
):
    return _handle_db_transaction(db, os_service.toggle_ativo_ordem_servico, os_id)
