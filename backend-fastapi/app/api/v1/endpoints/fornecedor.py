# ---------------------------------------------------------------------------
# ARQUIVO: endpoints/fornecedor.py
# DESCRIÇÃO: Define os endpoints (rotas) da API para operações CRUD
#            relacionadas a Fornecedores.
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, status, Path, Query, Response
from sqlalchemy.orm import Session
from typing import Optional, Sequence, List

from app.core.depends import get_token, check_permission, _handle_db_transaction
from app.db.session import get_db

from app.schemas.fornecedor import FornecedorCreate, FornecedorRead, FornecedorUpdate
from app.services import fornecedor as fornecedor_service

# Cria um roteador específico. Assume que a URL base é /fornecedores
router = APIRouter()

# ===========================================================================
# ROTAS DE CRIAÇÃO (POST)
# ===========================================================================

@router.post(
    "/",
    response_model=FornecedorRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo fornecedor e seus endereços associados"
)
def create_fornecedor(
    user_token: dict = Depends(check_permission(required_permission="fornecedor")),
    *,
    fornecedor_to_add: FornecedorCreate,
    db: Session = Depends(get_db)
):
    """
    Cria um novo Fornecedor e seus endereços aninhados no sistema.

    Args:
        user_token (dict): Payload do token do usuário (injetado via dependência de permissão).
        fornecedor_to_add (FornecedorCreate): DTO contendo os dados do fornecedor e endereços.
        db (Session): Sessão de banco de dados ativa.

    Raises:
        HTTPException 403 FORBIDDEN: Se o usuário não tiver a permissão 'fornecedor'.
        HTTPException 409 CONFLICT: Se o CNPJ ou IE já estiverem cadastrados.

    Returns:
        FornecedorRead: O objeto FornecedorModel criado, formatado como DTO de saída.
    """
    return _handle_db_transaction(
        db,
        fornecedor_service.create_fornecedor,
        fornecedor_to_add
    )

# ===========================================================================
# ROTAS DE CRIAÇÃO (POST)
# ===========================================================================

@router.get(
    "/",
    response_model=List[FornecedorRead],
    status_code=status.HTTP_200_OK,
    summary="Buscar os fornecedores por nome ou CNPJ, ou retorna todos"
)
def get_fornecedor_by_search(
    user_token: dict = Depends(check_permission(required_permission="fornecedor")),
    *,
    buscar: Optional[str] = Query(
        None,
        max_length=255,
        description="Busca por nome, razão social ou CNPJ do fornecedor."
    ),
    db: Session = Depends(get_db)
):
    """
    Busca fornecedores ativos por termo de busca ou retorna todos os ativos se nenhum termo for fornecido.

    Args:
        user_token (dict): Payload do token do usuário (injetado via dependência de permissão).
        buscar (Optional[str]): Termo de busca parcial.
        db (Session): Sessão de banco de dados ativa.

    Raises:
        HTTPException 403 FORBIDDEN: Se o usuário não tiver a permissão 'fornecedor'.

    Returns:
        List[FornecedorRead]: Lista de fornecedores que correspondem ao critério de busca.
    """
    # FIX ARQUITETURA: Garantindo que o resultado do Service seja retornado.
    return _handle_db_transaction(
        db, 
        fornecedor_service.get_fornecedor_by_search,
        search=buscar # Passa o parâmetro 'buscar' para o serviço como 'search'
    )

# ===========================================================================
# ROTAS DE ATUALIZAÇÃO (PUT)
# ===========================================================================

@router.put(
    "/{fornecedor_id}",
    response_model=FornecedorRead,
    status_code=status.HTTP_200_OK,
    summary="Atualiza os dados de um fornecedor pelo ID"
)
def update_fornecedor_by_id(
    user_token: dict = Depends(check_permission(required_permission="fornecedor")),
    fornecedor_id: int = Path(..., description="ID do fornecedor a ser atualizado", ge=1),
    *,
    fornecedor_to_update: FornecedorUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza um fornecedor existente pelo seu ID, permitindo atualização parcial (PATCH-like)
    e a manipulação dos endereços aninhados.

    Args:
        user_token (dict): Payload do token do usuário.
        fornecedor_id (int): O ID único do fornecedor.
        fornecedor_to_update (FornecedorUpdate): DTO contendo os campos a serem atualizados.
        db (Session): Sessão de banco de dados ativa.

    Raises:
        HTTPException 403 FORBIDDEN: Se o usuário não tiver a permissão 'fornecedor'.
        HTTPException 404 NOT FOUND: Se o fornecedor não for encontrado.
        HTTPException 409 CONFLICT: Se a atualização resultar em duplicidade (CNPJ/IE).

    Returns:
        FornecedorRead: O objeto FornecedorModel atualizado, formatado como DTO de saída.
    """
    return _handle_db_transaction(
        db,
        fornecedor_service.update_fornecedor_by_id,
        fornecedor_id,
        fornecedor_to_update
    )


@router.put(
    "/toggle_ativo/{fornecedor_id}",
    response_model=FornecedorRead,
    status_code=status.HTTP_200_OK,
    summary="Ativa/Desativa um Fornecedor logicamente no BD"
)
def toggle_status_fornecedor(
    user_token: dict = Depends(check_permission(required_permission="fornecedor")),
    fornecedor_id: int = Path(..., description="ID do Fornecedor a ser ativado/desativado", ge=1),
    *,
    db: Session = Depends(get_db)
):
    """
    Altera o status `ativo` (True <-> False) de um fornecedor existente (Deleção Lógica).

    Args:
        user_token (dict): Payload do token do usuário.
        fornecedor_id (int): O ID único do fornecedor.
        db (Session): Sessão de banco de dados ativa.

    Raises:
        HTTPException 403 FORBIDDEN: Se o usuário não tiver a permissão 'fornecedor'.
        HTTPException 404 NOT FOUND: Se o fornecedor não for encontrado.

    Returns:
        FornecedorRead: O objeto FornecedorModel com o status 'ativo' atualizado.
    """
    return _handle_db_transaction(
        db,
        fornecedor_service.toggle_active_disable_fornecedor_by_id,
        fornecedor_id
    )