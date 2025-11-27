# ---------------------------------------------------------------------------
# ARQUIVO: funcionario.py
# DESCRIÇÃO: Define os endpoints (rotas) da API para operações CRUD
#            relacionadas a Funcionários.
#            Rotas base: /funcionarios
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, status, Query, Path, Response
from sqlalchemy.orm import Session
from typing import Sequence, List

# Importa os schemas de Funcionario (Create, Read, Update)
from app.schemas.funcionario import FuncionarioCreate, FuncionarioRead, FuncionarioUpdate
# Importa as dependências de autenticação, sessão e transação
from app.core.depends import check_permission, get_token, _handle_db_transaction
from app.db.session import get_db
# Importa a camada de serviço que contém a lógica de negócio
from app.services import funcionario as employee_service

# Cria um roteador específico. Assume que a URL base é /funcionarios
router = APIRouter()

# ===============================================
# Endpoint 1: Criar Funcionário (POST /)
# ===============================================
@router.post(
    "/",
    response_model=FuncionarioRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo funcionário e o associa ao usuário logado (1:1)"
)
def create_employee(
    employee: FuncionarioCreate,
    # Requer a permissão "funcionario"
    permission: dict = Depends(check_permission("funcionario")),
    db: Session = Depends(get_db)
):
    """
    Cria um novo Funcionário.
    
    Estabelece a relação 1:1 com o usuário identificado pelo token (implícito).
    """
    # Chama o serviço de criação dentro do gerenciador de transação
    # Nota: Se o 'usuario_id' é obrigatório, o serviço deve extraí-lo do 'permission' dict
    # ou o 'permission' dict deve ser passado como argumento. O código original
    # comentou a passagem do token, mas o serviço pode ainda depender dele.
    return _handle_db_transaction(
        db, 
        employee_service.create_employee, 
        employee,
    )


# ===============================================
# Endpoint 2: Buscar TODOS os Funcionários (GET /all)
# ===============================================
@router.get(
    "/all",
    response_model=Sequence[FuncionarioRead],
    status_code=status.HTTP_200_OK,
    summary="Retorna todos os funcionários ativos cadastrados"
)
def get_all_employees(
    # Apenas requer o token para autenticação, mas não verifica permissão específica
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Busca e retorna a lista completa de funcionários ativos.
    
    Operações de leitura simples (GET) não utilizam o `_handle_db_transaction`.
    """
    # Chama o serviço de busca direta
    return employee_service.get_all_employees(db)


# ===============================================
# Endpoint 3: Buscar Funcionários por Termo (GET /)
# ===============================================
@router.get(
    "/",
    response_model=List[FuncionarioRead],
    status_code=status.HTTP_200_OK,
    summary="Busca Funcionário(s) por termo (nome, CPF, email, etc.)"
)
def get_employee_by_search(
    # Parâmetro de busca obrigatório, obtido via Query Parameter
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
    # Chama o serviço de busca direta
    return employee_service.get_employee_by_search(db, buscar)


# ===============================================
# Endpoint 4: Atualizar Funcionário (PUT /{id})
# ===============================================
@router.put(
    "/{id}",
    response_model=FuncionarioRead,
    status_code=status.HTTP_200_OK,
    summary="Atualiza dados de um funcionário (incluindo endereços) pelo ID"
)
def update_employee_by_id(
    # ID do funcionário a ser editado
    id: int = Path(..., description="ID do funcionário a ser editado", ge=1),
    *,
    # Dados de atualização
    employee: FuncionarioUpdate,
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Atualiza um funcionário existente pelo seu ID.
    """
    # Chama o serviço de atualização dentro do gerenciador de transação
    return _handle_db_transaction(
        db, 
        employee_service.update_employee_by_id, 
        id, 
        employee
    )


# ===============================================
# Endpoint 5: Ativar Funcionário (PUT /ativa/{id})
# ===============================================
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
    # Chama o serviço de ativação (Soft Update) dentro do gerenciador de transação
    return _handle_db_transaction(
        db, 
        employee_service.active_employee_by_id, 
        id
    )


# ===============================================
# Endpoint 6: Desativar Funcionário (PUT /desativa/{id})
# ===============================================
@router.put(
    "/desativa/{id}",
    # Retorna uma Response vazia com status 204 No Content
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
    # O `_handle_db_transaction` executa o serviço e gerencia a transação
    _handle_db_transaction(
        db, 
        employee_service.disable_employee_by_id, 
        id
    )
    # Retorna o status 204 No Content
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ===============================================
# Endpoint 7: Adicionar Cargo ao Funcionário (PUT /{id}/cargo)
# ===============================================
@router.put(
    "/{funcionario_id}/cargo",
    response_model=FuncionarioRead,
    status_code=status.HTTP_200_OK,
    summary="Adiciona/Atualiza o cargo de um funcionário"
)
def add_cargo_funcionario(
    # Requer a permissão "funcionario"
    user_token: dict = Depends(check_permission(required_permission="funcionario")),
    # ID do funcionário
    funcionario_id: int = Path(
        ...,
        description="ID único do funcionário que vai receber o cargo",
        ge=1
    ),
    # ID do cargo a ser adicionado, obtido via Query Parameter
    cargo_id: int = Query(
        ...,
        description="ID do cargo a ser adicionado no funcionário",
    ),
    db: Session = Depends(get_db)
):
    """
    Associa um cargo existente a um funcionário específico.
    """
    # Chama o serviço de atualização de cargo dentro do gerenciador de transação
    return _handle_db_transaction(
        db,
        employee_service.update_cargo_funcionario,
        funcionario_id,
        cargo_id
    )