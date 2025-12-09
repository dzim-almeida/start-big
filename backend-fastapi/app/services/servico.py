# ---------------------------------------------------------------------------
# ARQUIVO: servicos/servico.py
# MÓDULO: Regras de Negócio (Service Layer)
# DESCRIÇÃO: Orquestra validações, verificação de conflitos e persistência
#            para operações relacionadas a Serviços.
# ---------------------------------------------------------------------------

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Sequence

# Schemas Pydantic (para validação de entrada)
from app.schemas.servico import ServicoCreate, ServicoUpdate
# Modelo SQLAlchemy (para mapeamento do DB)
from app.db.models.servico import Servico as ServicoModel
# Camada CRUD (para acesso direto ao DB)
from app.db.crud import servico as servico_crud

# Definição de exceções padrão para reutilização
not_found_exce = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Serviço não encontrado no sistema"
)

conflict_exce = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Serviço já cadastrado no sistema"
)

# ===========================================================================
# LÓGICA DE CRIAÇÃO (CREATE)
# ===========================================================================

def create_servico(db: Session, servico_to_add: ServicoCreate) -> ServicoModel:
    """
    Aplica regras de negócio para criação de um Serviço.
    
    1. Verifica conflito de unicidade (Descrição).
    2. Instancia o modelo ORM.
    3. Persiste o serviço através do CRUD.
    """
    # Verifica se já existe serviço com a mesma descrição
    servico_in_db = servico_crud.get_servico_by_description(db, description_to_search=servico_to_add.descricao)
    if servico_in_db:
        raise conflict_exce

    # Prepara os dados ignorando campos não definidos
    servico_data = servico_to_add.model_dump(exclude_unset=True)

    servico_to_db = ServicoModel(**servico_data)

    return servico_crud.create_servico(db, servico_to_add=servico_to_db)


# ===========================================================================
# LÓGICA DE LEITURA (READ)
# ===========================================================================

def get_servico_by_search(db: Session, search: str | None) -> Sequence[ServicoModel]:
    """
    Intermediário para busca de serviços.
    Repassa a query string para o CRUD realizar a filtragem.
    """
    return servico_crud.get_servico_by_search(db, search=search)


# ===========================================================================
# LÓGICA DE ATUALIZAÇÃO (UPDATE)
# ===========================================================================

def update_servico_by_id(db: Session, servico_id: int, servico_to_update: ServicoUpdate) -> ServicoModel:
    """
    Atualiza dados de um serviço existente.
    
    1. Verifica se o serviço existe.
    2. Garante que a nova descrição (se houver) não gere conflito com outro serviço.
    3. Atualiza dinamicamente os atributos do objeto.
    """
    # 1. Busca o serviço atual
    servico_in_db = servico_crud.get_servico_by_id(db, servico_id=servico_id)
    if not servico_in_db:
       raise not_found_exce
    
    # 2. Verifica conflito de descrição (caso esteja sendo alterada)
    # Nota: Idealmente, verificar se o ID encontrado não é o próprio serviço sendo editado
    if servico_to_update.descricao:
        potential_conflict = servico_crud.get_servico_by_description(db, servico_to_update.descricao)
        if potential_conflict and potential_conflict.id != servico_id:
             raise conflict_exce

    data_update = servico_to_update.model_dump(exclude_unset=True)

    # 3. Atualiza dinamicamente os atributos do objeto SQLAlchemy
    for key, value in data_update.items():
        setattr(servico_in_db, key, value)

    # 4. Delega para o CRUD
    return servico_crud.update_servico(db, servico_in_db)


# ===========================================================================
# LÓGICA DE STATUS (TOGGLE)
# ===========================================================================

def toggle_active_disable_servico_by_id(db: Session, servico_id: int) -> ServicoModel:
    """
    Inverte o status 'ativo' do serviço (True <-> False).
    Útil para soft-delete ou reativação.
    """
    servico_in_db = servico_crud.get_servico_by_id(db, servico_id=servico_id)
    if not servico_in_db:
        raise not_found_exce
    
    servico_in_db.ativo = not servico_in_db.ativo

    return servico_crud.update_servico(db, servico_to_update=servico_in_db)