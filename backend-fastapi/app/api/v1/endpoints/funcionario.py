# ---------------------------------------------------------------------------
# ARQUIVO: funcionario_endpoint.py
# DESCRIÇÃO: Define os endpoints (rotas) da API para operações CRUD
#            relacionadas a Funcionários.
#            Rotas: /funcionarios, /funcionarios/{id}, etc.
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, status, HTTPException, Query, Path, Response
from sqlalchemy.orm import Session
from typing import Sequence, List

# Importa os schemas de Funcionario (Create, Read, Update)
from app.schemas.funcionario import FuncionarioCreate, FuncionarioRead, FuncionarioUpdate
# Importa as dependências de autenticação e sessão
from app.core.depends import get_token
from app.db.session import get_db
# Importa a camada de serviço que contém a lógica de negócio
from app.services import funcionario as employee_service

# Cria um roteador específico. Assume que a URL base é /funcionarios
router = APIRouter()

# Função auxiliar para padronizar o tratamento de transações e exceções
# (Recomendado: Mover para um módulo 'utils' ou 'core' para evitar repetição)
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
# Endpoint: Criar Funcionário
# Rota: POST /funcionarios/
# =========================
@router.post(
    "/",
    response_model=FuncionarioRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo funcionário e o associa ao usuário logado (1:1)"
)
def create_employee(
    employee: FuncionarioCreate,
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Cria um novo Funcionário e estabelece a relação 1:1 com o usuário
    identificado pelo token.
    """
    # A lógica de serviço deve extrair o 'usuario_id' do token
    return _handle_db_transaction(
        db, 
        employee_service.create_employee, 
        employee,
        # token.get("user_id") # Assumindo que o ID do usuário está no payload do token
    )


# =========================
# Endpoint: Buscar TODOS os Funcionários (Sem Paginação)
# Rota: GET /funcionarios/all
# =========================
@router.get(
    "/all",
    response_model=Sequence[FuncionarioRead],
    status_code=status.HTTP_200_OK,
    summary="Retorna todos os funcionários ativos cadastrados"
)
def get_all_employees(
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Busca e retorna a lista completa de funcionários ativos.
    """
    # A busca (READ) não requer transação/commit/rollback
    return employee_service.get_all_employees(db)


# =========================
# Endpoint: Buscar Funcionários (Search)
# Rota: GET /funcionarios/
# =========================
@router.get(
    "/",
    response_model=List[FuncionarioRead],
    status_code=status.HTTP_200_OK,
    summary="Busca Funcionário(s) por termo (nome, CPF, email, etc.)"
)
def get_employee_by_search(
    buscar: str = Query(
        ...,
        min_length=1,
        max_length=255,
        description="Entrada pode ser nome, CPF, RG ou email."
    ),
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Busca funcionários usando um termo de pesquisa (search term).
    """
    # A busca (READ) não requer transação/commit/rollback
    return employee_service.get_employee_by_search(db, buscar)


# =========================
# Endpoint: Atualizar Funcionário (PUT)
# Rota: PUT /funcionarios/{id}
# =========================
@router.put(
    "/{id}",
    response_model=FuncionarioRead,
    status_code=status.HTTP_200_OK,
    summary="Atualiza dados de um funcionário (incluindo endereços) pelo ID"
)
def update_employee_by_id(
    id: int = Path(..., description="ID do funcionário a ser editado", ge=1),
    *,
    employee: FuncionarioUpdate,
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Atualiza um funcionário existente pelo seu ID.
    """
    return _handle_db_transaction(
        db, 
        employee_service.update_employee_by_id, 
        id, 
        employee
    )


# =========================
# Endpoint: Ativar Funcionário (Update Lógico)
# Rota: PUT /funcionarios/ativa/{id}
# =========================
@router.put(
    "/ativa/{id}",
    response_model=FuncionarioRead,
    status_code=status.HTTP_200_OK,
    summary="Ativa um funcionário logicamente no BD (seta 'ativo' para True)"
)
def active_employee_by_id(
    id: int = Path(..., description="ID do funcionário a ser ativado", ge=1),
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Ativa um funcionário existente pelo seu ID.
    """
    return _handle_db_transaction(
        db, 
        employee_service.active_employee_by_id, 
        id
    )


# =========================
# Endpoint: Desativar Funcionário (Update Lógico)
# Rota: PUT /funcionarios/desativa/{id}
# =========================
@router.put(
    "/desativa/{id}",
    # Retorna uma Response vazia com status 204
    status_code=status.HTTP_204_NO_CONTENT, 
    summary="Desativa um funcionário logicamente no BD (seta 'ativo' para False)"
)
def disable_employee_by_id(
    id: int = Path(..., description="ID do funcionário a ser desativado", ge=1),
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Desativa um funcionário existente pelo seu ID (Soft Delete).
    Retorna 204 No Content se a operação for bem-sucedida.
    """
    # Para rotas 204, o serviço é chamado e a resposta é controlada pelo status_code
    _handle_db_transaction(
        db, 
        employee_service.disable_employee_by_id, 
        id
    )
    # Retorna uma resposta vazia 204 NO CONTENT
    return Response(status_code=status.HTTP_204_NO_CONTENT)