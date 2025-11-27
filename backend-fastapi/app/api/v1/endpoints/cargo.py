from typing import Sequence
from fastapi import APIRouter, status, Depends, Path
# Nota: 'Session' do pytest não é necessário para endpoints, assumindo que era
# Session do SQLAlchemy ou que o import de Session do FastAPI/SQLAlchemy foi omitido.
# Corrigido para sqlalchemy.orm.Session para consistência, se o tipo for esse.
from sqlalchemy.orm import Session # Assumindo sqlalchemy.orm.Session

from app.core.depends import _handle_db_transaction, check_permission
from app.db.session import get_db
from app.schemas.cargo import CargoCreate, CargoRead, CargoUpdate
from app.services import cargo as cargo_service

# Inicializa o roteador do FastAPI
router = APIRouter()

# -------------------------------------------------------------------
# Endpoint: Criação de Cargo (POST)
# -------------------------------------------------------------------
@router.post(
    "/",
    response_model=CargoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria novos cargos de permissão para funcionários"
)
def create_cargo_funcionario(
    # Dados do novo cargo, validados pelo Pydantic Schema
    new_cargo: CargoCreate,
    # Injeção da sessão do banco de dados
    db: Session = Depends(get_db),
    # Verificação de permissão: Requer a permissão "cargo" para executar
    user_permission: dict = Depends(check_permission(required_permission="cargo"))
):
    """
    Cria um novo cargo de permissão no sistema.
    
    A transação é encapsulada na dependência `_handle_db_transaction`,
    garantindo que o serviço seja executado e a transação seja comitada ou revertida.
    """
    # Chama o serviço de criação de cargo dentro do gerenciador de transação
    return _handle_db_transaction(
        db,
        cargo_service.create_cargo_funcionario,
        user_permission, # O token de permissão (que pode conter o user_id) é passado
        new_cargo
    )

# -------------------------------------------------------------------
# Endpoint: Listagem de Cargos (GET All)
# -------------------------------------------------------------------
@router.get(
    "/",
    response_model=Sequence[CargoRead],
    status_code=status.HTTP_200_OK,
    summary="Retorna todos os cargos do sistema",
    description="Retorna todos os cargos do sistema"
)
def get_cargo_funcionarios(
    # Apenas verifica a permissão, o retorno (dict) não é usado na função de serviço
    user_token: dict = Depends(check_permission(required_permission="cargo")),
    db: Session = Depends(get_db)
):
    """
    Busca e retorna a lista completa de todos os cargos cadastrados.
    
    Operações de leitura (GET) não precisam de argumentos de transação adicionais.
    """
    # Chama o serviço de busca de todos os cargos
    return _handle_db_transaction(
        db,
        cargo_service.get_all_cargo_funcionario,
    )

# -------------------------------------------------------------------
# Endpoint: Atualização de Cargo (PUT)
# -------------------------------------------------------------------
@router.put(
    "/{cargo_id}",
    response_model=CargoRead,
    status_code=status.HTTP_200_OK,
    summary="Edita um cargo já existente"
)
def update_cargo_funcionario(
    # Verificação de permissão
    user_token: dict = Depends(check_permission(required_permission="cargo")),
    # ID do cargo a ser atualizado, obtido da URL (Path Parameter)
    cargo_id: int = Path(
        ...,
        description="ID único do cargo a ser editado",
        ge=1 # Garante que o ID seja maior ou igual a 1
    ),
    *, # O asterisco força os parâmetros subsequentes a serem passados por nome (keyword)
    # Dados de atualização, validados pelo Pydantic Schema (corpo da requisição)
    update_cargo: CargoUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza os dados de um cargo existente pelo seu ID.
    """
    # Chama o serviço de atualização dentro do gerenciador de transação
    return _handle_db_transaction(
        db,
        cargo_service.update_cargo_funcionario,
        cargo_id,
        update_cargo
    )

# -------------------------------------------------------------------
# Endpoint: Deleção de Cargo (DELETE)
# -------------------------------------------------------------------
@router.delete(
    "/{cargo_id}",
    status_code=status.HTTP_204_NO_CONTENT, # Indica sucesso sem retorno de corpo
    summary="Deleta um cargo do sistema"
)
def delete_cargo_funcionario(
    # Permissão específica para deleção
    user_token: dict = Depends(check_permission(required_permission="delete-cargo")),
    # ID do cargo a ser deletado
    cargo_id: int = Path(
        ...,
        description="ID único do cargo a ser excluído",
        ge=1
    ),
    db: Session = Depends(get_db)
):
    """
    Remove um cargo existente do sistema pelo seu ID.
    """
    # Chama o serviço de deleção dentro do gerenciador de transação
    _handle_db_transaction(
        db,
        cargo_service.delete_cargo_funcionario,
        cargo_id
    )
    # Retorna o status 204 No Content, que é o esperado para deleções bem-sucedidas
    return