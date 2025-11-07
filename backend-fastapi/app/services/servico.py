# ---------------------------------------------------------------------------
# ARQUIVO: services/servico.py
# DESCRIÇÃO: Camada de Lógica de Negócio (Serviços) para
#            operações relacionadas a Serviços.
# ---------------------------------------------------------------------------

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Sequence

# Schemas Pydantic (para validação de entrada)
from app.schemas.servico import ServicoCreate, ServicoUpdate
# Modelo SQLAlchemy (para mapeamento do DB)
from app.db.models.servico import Servico as ServicoModel
# Camada CRUD (para acesso direto ao DB)
from app.db.crud import servico as service_crud

# =========================
# SERVIÇO: Criar Serviço
# =========================
def create_service(db: Session, service: ServicoCreate) -> ServicoModel:
    """
    Regras de negócio para criar um novo serviço.

    1. Verifica se já existe um serviço com a mesma descrição.
    2. Se não existir, mapeia o schema (Pydantic) para o modelo (SQLAlchemy).
    3. Delega a criação para a camada CRUD.

    Args:
        db (Session): Sessão do banco de dados.
        service (ServicoCreate): Dados do serviço validados pelo Pydantic.

    Raises:
        HTTPException (409): Se a descrição do serviço já existir.

    Returns:
        ServicoModel: O novo serviço criado e salvo no banco.
    """
    
    # 1. Verifica duplicidade (regra de negócio)
    service_in_db = service_crud.get_service_by_description(db, service.descricao)

    if service_in_db:
        # ** CORREÇÃO CRÍTICA **:
        # Você deve usar 'raise' para lançar a exceção e parar a execução.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Serviço com descrição já existente."
        )

    # 2. Mapeia o schema Pydantic para o modelo SQLAlchemy
    service_to_db = ServicoModel(
        descricao=service.descricao,
        valor=service.valor
    )

    # 3. Delega a criação para a camada CRUD
    new_service_in_db = service_crud.create_service(db, service_to_db)
    return new_service_in_db

# =========================
# SERVIÇO: Buscar Serviços (Search)
# =========================
def get_service_by_search(db: Session, search: str) -> Sequence[ServicoModel]:
    """
    Regras de negócio para buscar serviços.
    (Neste caso, apenas delega a chamada para o CRUD).
    """
    services_in_db = service_crud.get_service_by_search(db, search)
    return services_in_db

# =========================
# SERVIÇO: Atualizar Serviço
# =========================
def update_service(db: Session, id: int, service: ServicoUpdate) -> ServicoModel:
    """
    Regras de negócio para atualizar um serviço.

    1. Busca o serviço existente pelo ID.
    2. Se não encontrar, lança um erro 404.
    3. Mapeia dinamicamente os campos do schema de atualização
       (ignora campos que não foram enviados).
    4. Delega a atualização para a camada CRUD.

    Args:
        db (Session): Sessão do banco de dados.
        id (int): ID do serviço a ser atualizado.
        service (ServicoUpdate): Dados parciais (ou completos) de atualização.

    Raises:
        HTTPException (404): Se o serviço não for encontrado.

    Returns:
        ServicoModel: O serviço após a atualização.
    """
    
    # 1. Busca o serviço
    service_in_db = service_crud.get_service_by_id(db, id)
    
    # 2. Verifica se existe
    if not service_in_db:
        # ** CORREÇÃO CRÍTICA **: Adicionado 'raise'
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Serviço não encontrado."
        )

    # 3. Obtém um dicionário apenas com os campos que foram enviados na requisição
    update_data = service.model_dump(exclude_unset=True)

    # Atualiza dinamicamente os atributos do objeto SQLAlchemy
    for key, value in update_data.items():
        setattr(service_in_db, key, value)

    # 4. Delega para o CRUD (que fará o flush/refresh)
    return service_crud.update_service(db, service_in_db)

# =========================
# SERVIÇO: Deletar Serviço
# =========================
def delete_service(db: Session, id: int) -> None:
    """
    Regras de negócio para deletar um serviço.

    1. Busca o serviço existente pelo ID.
    2. Se não encontrar, lança um erro 404.
    3. Delega a exclusão para a camada CRUD.

    Args:
        db (Session): Sessão do banco de dados.
        id (int): ID do serviço a ser deletado.

    Raises:
        HTTPException (404): Se o serviço não for encontrado.
    """
    
    # 1. Busca o serviço
    service_in_db = service_crud.get_service_by_id(db, id)
    
    # 2. Verifica se existe
    if not service_in_db:
        # ** CORREÇÃO CRÍTICA **: Adicionado 'raise'
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Serviço não encontrado."
        )
    
    # 3. Delega para o CRUD (que fará o delete/flush)
    return service_crud.delete_service(db, service_in_db)