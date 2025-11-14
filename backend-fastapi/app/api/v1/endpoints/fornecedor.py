# ---------------------------------------------------------------------------
# ARQUIVO: endpoints/fornecedor.py
# DESCRIÇÃO: Define os endpoints (rotas) da API para operações CRUD
#            relacionadas a Fornecedores.
#            Rotas: /fornecedores, /fornecedores/all, /fornecedores/{id}, etc.
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, HTTPException, status, Path, Query, Response
from sqlalchemy.orm import Session
from typing import Sequence, List

from app.core.depends import get_token
from app.db.session import get_db

from app.schemas.fornecedor import FornecedorCreate, FornecedorRead, FornecedorUpdate
from app.services import fornecedor as supplier_service

# Cria um roteador específico. Assume que a URL base é /fornecedores
router = APIRouter()

# Função auxiliar para padronizar o tratamento de transações e exceções (Recomendado: Mover para um módulo 'utils' ou 'core')
def _handle_db_transaction(db: Session, func, *args, **kwargs):
    """Executa a lógica de serviço, gerencia a transação e trata exceções."""
    try:
        result = func(db, *args, **kwargs)
        db.commit()
        return result
    except HTTPException as http_exce:
        # Erros de negócio (ex: 404 Not Found, 409 Conflict)
        print(f"Erro de negócio: {http_exce.detail}")
        db.rollback()
        raise http_exce
    except Exception as e:
        # Erros inesperados (ex: falha de conexão, erro de lógica no serviço)
        print(f"Erro inesperado: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro interno no servidor."
        )

# =========================
# Endpoint: Criar Fornecedor
# Rota: POST /fornecedores
# =========================
@router.post(
    "/", # Mantido "/", mas poderia ser "/create" para evitar ambiguidades com a busca
    response_model=FornecedorRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo fornecedor e seus endereços associados"
)
def create_supplier(
    supplier: FornecedorCreate,
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Cria um novo Fornecedor com o payload aninhado.
    Utiliza a função auxiliar para gerenciar a transação.
    """
    return _handle_db_transaction(
        db,
        supplier_service.create_supplier,
        supplier
    )

# =========================
# Endpoint: Buscar TODOS os Fornecedores (Sem Paginação)
# Rota: GET /fornecedores/all
# =========================
@router.get(
    "/all", # Rota alterada de '/a' para '/all' (melhor legibilidade)
    response_model=Sequence[FornecedorRead],
    status_code=status.HTTP_200_OK,
    summary="Retorna todos os fornecedores cadastrados (rota de utilidade)"
)
def get_all_suppliers(
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Busca e retorna a lista completa de fornecedores.
    """
    # A busca não altera o estado do BD
    return supplier_service.get_all_suppliers(db)

# =========================
# Endpoint: Buscar Fornecedores (Search)
# Rota: GET /fornecedores/
# =========================
@router.get(
    "/",
    response_model=List[FornecedorRead],
    status_code=status.HTTP_200_OK,
    summary="Buscar os fornecedores por nome ou CNPJ"
)
def get_supplier_by_search(
    buscar: str = Query(
        ...,
        min_length=1,
        max_length=255,
        description="Busca por nome, razão social ou CNPJ do fornecedor."
    ),
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Busca fornecedores pelo nome ou CNPJ.
    """
    # A busca não altera o estado do BD
    return supplier_service.get_supplier_by_search(db, buscar)

# =========================
# Endpoint: Atualizar Fornecedor (PUT)
# Rota: PUT /fornecedores/{id}
# =========================
@router.put(
    "/{id}",
    response_model=FornecedorRead,
    status_code=status.HTTP_200_OK,
    summary="Atualiza os dados de um fornecedor pelo ID"
)
def update_supplier(
    id: int = Path(..., description="ID do fornecedor a ser atualizado", ge=1),
    *,
    supplier: FornecedorUpdate,
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Atualiza um fornecedor existente pelo seu ID.
    """
    return _handle_db_transaction(
        db,
        supplier_service.update_supplier,
        id,
        supplier
    )

# =========================
# Endpoint: Ativar Fornecedor (Update Lógico)
# Rota: PUT /fornecedores/ativa/{id}
# =========================
@router.put(
    "/ativa/{id}",
    response_model=FornecedorRead,
    status_code=status.HTTP_200_OK,
    summary="Ativa um Fornecedor logicamente no BD"
)
def active_supplier_by_id(
    id: int = Path(..., description="ID do Fornecedor a ser ativado", ge=1),
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Ativa um Fornecedor existente pelo seu ID.
    """
    return _handle_db_transaction(
        db,
        supplier_service.active_supplier_by_id,
        id
    )

# =========================
# Endpoint: Desativar Fornecedor (Update Lógico)
# Rota: PUT /fornecedores/desativa/{id}
# =========================
@router.put(
    "/desativa/{id}",
    status_code=status.HTTP_204_NO_CONTENT, # Sem corpo de resposta
    summary="Desativa um Fornecedor logicamente no BD"
)
def disable_supplier_by_id(
    id: int = Path(..., description="ID do Fornecedor a ser desativado", ge=1),
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Desativa um Fornecedor existente pelo seu ID (Soft Delete).
    Retorna 204 No Content se a operação for bem-sucedida.
    """
    # A função auxiliar fará o serviço, commit e tratamento de erro
    _handle_db_transaction(
        db,
        supplier_service.disable_supplier_by_id,
        id
    )
    # Retorna Response vazia 204
    return Response(status_code=status.HTTP_204_NO_CONTENT)