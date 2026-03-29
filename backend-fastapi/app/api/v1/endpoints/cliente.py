# ---------------------------------------------------------------------------
# ARQUIVO: cliente_endpoint.py
# MÓDULO: Interface de API (Controller)
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, status, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional, List

from app.schemas.cliente import (
    ClienteRead, ClienteUpdate,
    ClientePFCreate, ClientePFRead,
    ClientePJCreate, ClientePJRead
)

from app.schemas.pagination import ClientePaginationRead
from app.core.depends import _handle_db_transaction, check_permission
from app.db.session import get_db
from app.services import cliente as cliente_service
from app.db.models.ordem_servico_equipamento import OrdemServicoEquipamento

router = APIRouter()

# ===========================================================================
# ROTAS DE CRIAÇÃO (POST)
# ===========================================================================

@router.post(
    "/cliente_pf",
    response_model=ClientePFRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar Pessoa Física",
    description="Cria um novo registro de cliente Pessoa Física (PF) e seus endereços vinculados."
)
def create_new_cliente_pf(
    user_token: dict = Depends(check_permission(required_permission="cliente")),
    *,
    cliente_pf_to_add: ClientePFCreate,
    db: Session = Depends(get_db)
):
    """
    Endpoint para criar um novo cliente do tipo Pessoa Física.

    Args:
        cliente_pf_to_add (ClientePFCreate): Payload com dados do cliente PF e endereços.
        db (Session): Sessão de banco de dados injetada.

    Returns:
        ClientePFRead: O objeto cliente criado com ID e dados persistidos.
    """
    return _handle_db_transaction(
        db, 
        cliente_service.create_cliente_pf, 
        cliente_pf_to_add,
    )


@router.post(
    "/cliente_pj",
    response_model=ClientePJRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar Pessoa Jurídica",
    description="Cria um novo registro de cliente Pessoa Jurídica (PJ) e seus endereços vinculados."
)
def create_new_cliente_pj(
    user_token: dict = Depends(check_permission(required_permission="cliente")),
    *,
    cliente_pj_to_add: ClientePJCreate,
    db: Session = Depends(get_db)
):
    """
    Endpoint para criar um novo cliente do tipo Pessoa Jurídica.

    Args:
        cliente_pj_to_add (ClientePJCreate): Payload com dados do cliente PJ e endereços.
        db (Session): Sessão de banco de dados injetada.

    Returns:
        ClientePJRead: O objeto cliente criado com ID e dados persistidos.
    """
    return _handle_db_transaction(
        db, 
        cliente_service.create_cliente_pj, 
        cliente_pj_to_add
    )

# ===========================================================================
# ROTAS DE LEITURA (GET)
# ===========================================================================

@router.get(
    "/",
    response_model=ClientePaginationRead,  # ← Corrigido: usa o schema de paginação
    status_code=status.HTTP_200_OK,
    summary="Listar ou Buscar Clientes",
    description="Recupera uma lista de clientes. Permite busca polimórfica (PF e PJ) por termo."
)
def get_client_by_search(
    user_token: dict = Depends(check_permission(required_permission="cliente")),
    *,
    buscar: Optional[str] = Query(
        None,
        description="Termo de busca (Nome, CPF, Razão Social, CNPJ ou Nome Fantasia)."
    ),
    only_active: bool = Query(
        False,
        description="True retorna só ativos. False retorna todos (ativos e inativos)."
    ),
    page: int = Query(1, ge=1, description="Página atual."),
    limit: int = Query(20, ge=1, le=100, description="Itens por página."),
    db: Session = Depends(get_db)
):
    filters = {"search": buscar, "only_active": only_active}
    return _handle_db_transaction(
        db,
        cliente_service.get_cliente_by_search,
        filters,
        page,
        limit
    )

@router.get(
    "/{cliente_id}/equipamentos",
    response_model=List[dict],
    status_code=status.HTTP_200_OK,
    summary="Histórico de Equipamentos do Cliente",
    description="Retorna equipamentos já cadastrados para o cliente (histórico para pré-preenchimento ao abrir nova OS)."
)
def get_equipamentos_by_cliente(
    user_token: dict = Depends(check_permission(required_permission="cliente")),
    cliente_id: int = Path(..., description="ID do cliente", ge=1),
    *,
    db: Session = Depends(get_db)
):
    equipamentos = db.scalars(
        select(OrdemServicoEquipamento)
        .where(OrdemServicoEquipamento.cliente_id == cliente_id)
        .where(OrdemServicoEquipamento.ativo == True)
        .order_by(OrdemServicoEquipamento.data_criacao.desc())
    ).all()
    return [
        {
            "equipamento": e.tipo_equipamento.value,
            "marca": e.marca,
            "modelo": e.modelo,
            "numero_serie": e.numero_serie,
        }
        for e in equipamentos
    ]

# ===========================================================================
# ROTAS DE ATUALIZAÇÃO (PUT)
# ===========================================================================


@router.put(
    "/toggle_ativo/{cliente_id}",
    response_model=ClienteRead,
    status_code=status.HTTP_200_OK,
    summary="Ativar/Desativar Cliente",
    description="Alterna o status lógico (ativo/inativo) do cliente."
)
def toggle_status_cliente(
    user_token: dict = Depends(check_permission(required_permission="cliente")),
    cliente_id: int = Path(..., description="ID do cliente alvo", ge=1),
    *,
    db: Session = Depends(get_db)
):
    """
    Alterna a flag 'ativo' do cliente. Usado para soft-delete ou reativação.

    Args:
        cliente_id (int): ID do cliente.
        db (Session): Sessão de banco de dados.

    Returns:
        ClienteRead: O objeto cliente com o novo status.
    """
    return _handle_db_transaction(
        db, 
        cliente_service.toggle_active_disable_cliente_by_id, 
        cliente_id
    )

@router.put(
    "/{cliente_id}",
    response_model=ClienteRead,
    status_code=status.HTTP_200_OK,
    summary="Atualizar Cliente Completo",
    description="Atualiza dados cadastrais e endereços de um cliente (PF ou PJ) existente."
)
def update_client_by_id(
    user_token: dict = Depends(check_permission(required_permission="cliente")),
    cliente_id: int = Path(..., description="ID do cliente a ser editado", ge=1),
    *,
    client_to_update: ClienteUpdate,
    db: Session = Depends(get_db)
):
    """
    Endpoint para atualizar um cliente pelo ID. Aceita payload polimórfico.

    Args:
        cliente_id (int): ID do cliente na URL.
        client_to_udate (ClienteUpdate): Payload com dados a atualizar.
        db (Session): Sessão de banco de dados.

    Returns:
        ClienteRead: O objeto cliente atualizado.
    """
    return _handle_db_transaction(
        db, 
        cliente_service.update_cliente_by_id, 
        cliente_id, 
        client_to_update
    )

