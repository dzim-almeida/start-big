# ---------------------------------------------------------------------------
# ARQUIVO: services/funcionario_service.py
# MÓDULO: Regras de Negócio (Service Layer)
# DESCRIÇÃO: Orquestra a criação complexa de Funcionário + Usuário + Endereço.
# ---------------------------------------------------------------------------

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Sequence

from app.schemas.funcionario import FuncionarioCreate, FuncionarioUpdate
from app.db.models.funcionario import Funcionario as FuncionarioModel
from app.db.crud import funcionario as funcionario_crud
from app.services import usuario as usuario_service
from app.services import endereco as endereco_service
from app.core.enum import EntityType

# Exceções Padronizadas
conflict_funcionario_exce = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Funcionário já cadastrado no sistema"
)

not_found_exce = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Funcionário não encontrado no sistema"
)

validation_exce = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Erro de validação de dados únicos"
)

# Configuração de validadores de unicidade
unique_fields = ["cpf", "email", "rg", "cnh", "carteira_trabalho"]
validators = {
    "cpf": funcionario_crud.get_funcionario_by_cpf,
    "email": funcionario_crud.get_funcionario_by_email,
    "rg": funcionario_crud.get_funcionario_by_rg,
    "cnh": funcionario_crud.get_funcionario_by_cnh,
    "carteira_trabalho": funcionario_crud.get_funcionario_by_ctps
}

# ===========================================================================
# LÓGICA DE CRIAÇÃO (CREATE)
# ===========================================================================

def create_funcionario(db: Session, empresa_id: int, funcionario_to_add: FuncionarioCreate) -> FuncionarioModel:
    """
    Realiza o cadastro completo (Onboarding).
    
    Processo Atômico:
    1. Valida unicidade de documentos (CPF, RG, etc).
    2. Cria o Usuário de acesso (Login/Senha).
    3. Cria o Funcionário vinculado ao Usuário e Empresa.
    4. Salva os Endereços vinculados ao Funcionário.
    """
    validation_errors = []

    # Separa dados do funcionário dos dados aninhados
    funcionario_data = funcionario_to_add.model_dump(exclude={"usuario", "endereco"}, exclude_unset=True)

    # 1. Validação de Conflitos
    for field in unique_fields:
        value = funcionario_data.get(field)
        if value is not None:
            error = funcionario_crud.verify_funcionario_conflict(
                db, value, validators[field], field
            )
            if error:
                if error == "disabled funcionario":
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Funcionário desabilitado com este {field.upper()}. Reative o cadastro existente."
                    )
                validation_errors.append({"campo": field, "mensagem": error})
    
    if validation_errors:
        validation_exce.detail = validation_errors
        raise validation_exce
    
    # 2. Criação do Usuário (Delegate)
    usuario_to_add = funcionario_to_add.usuario
    usuario_in_db = usuario_service.create_usuario(
        db,
        usuario_to_add=usuario_to_add,
        empresa_id=empresa_id
    )

    # 3. Criação do Funcionário
    funcionario_to_db = FuncionarioModel(
        **funcionario_data,
        usuario_id=usuario_in_db.id, # Foreign Key
        empresa_id=empresa_id
    )
    funcionario_in_db = funcionario_crud.create_funcionario(db, funcionario_to_add=funcionario_to_db)

    # 4. Vinculação de Endereços
    if funcionario_to_add.endereco:
        endereco_funcionario_to_db = endereco_service.address_to_db(
            id_entity=funcionario_in_db.id,
            type_entity=EntityType.FUNCIONARIO, 
            address_data=funcionario_to_add.endereco
        )
        funcionario_in_db.endereco = endereco_funcionario_to_db
    
    return funcionario_in_db

# ===========================================================================
# LÓGICA DE LEITURA (READ)
# ===========================================================================

def get_funcionario_by_search(db: Session, search: str | None) -> Sequence[FuncionarioModel]:
    """Delega busca para o CRUD."""
    return funcionario_crud.get_funcionario_by_search(db, search=search)

# ===========================================================================
# LÓGICA DE ATUALIZAÇÃO (UPDATE)
# ===========================================================================

def update_funcionario_by_id(db: Session, funcionario_id: int, funcionario_to_update: FuncionarioUpdate) -> FuncionarioModel:
    """Atualiza dados cadastrais e endereços."""
    
    funcionario_in_db = funcionario_crud.get_funcionario_by_id(db, funcionario_id=funcionario_id)
    if not funcionario_in_db:
         raise not_found_exce
    
    funcionario_data_to_update = funcionario_to_update.model_dump(exclude_unset=True)
    
    # Atualização de Endereços (Delegate)
    if "endereco" in funcionario_data_to_update and funcionario_data_to_update["endereco"] is not None:
        updated_enderecos = endereco_service.update_address_in_db(
            address_in_db=funcionario_in_db.endereco,
            address_to_update=funcionario_to_update.endereco,
            id_entity=funcionario_in_db.id,
            type_entity=EntityType.FUNCIONARIO
        )
        funcionario_in_db.endereco = updated_enderecos
        del funcionario_data_to_update["endereco"]
    
    # Atualização de Campos Simples
    for key, value in funcionario_data_to_update.items():
        setattr(funcionario_in_db, key, value)
    
    return funcionario_crud.update_funcionario_in_db(db, funcionario_to_update=funcionario_in_db)

def update_cargo_funcionario(db: Session, funcionario_id: int, cargo_id: int) -> FuncionarioModel:
    """Atualiza apenas a FK de cargo."""
    funcionario_in_db = funcionario_crud.get_funcionario_by_id(db, funcionario_id)
    if not funcionario_in_db:
        raise not_found_exce
    
    funcionario_in_db.cargo_id = cargo_id
    return funcionario_crud.update_funcionario_in_db(db, funcionario_to_update=funcionario_in_db)

# ===========================================================================
# LÓGICA DE STATUS (TOGGLE)
# ===========================================================================

def toggle_active_disable_funcionario_by_id(db: Session, funcionario_id: int) -> FuncionarioModel:
    """
    Soft Delete/Undelete.
    IMPORTANTE: Sincroniza o status do Usuário com o do Funcionário.
    Se o funcionário é desativado, o login (Usuário) também é bloqueado.
    """
    funcionario_in_db = funcionario_crud.get_funcionario_by_id(db, funcionario_id=funcionario_id)

    if not funcionario_in_db:
        raise not_found_exce
    
    # Inverte status
    novo_status = not funcionario_in_db.ativo
    funcionario_in_db.ativo = novo_status
    
    # Cascata para o Usuário
    if funcionario_in_db.usuario:
        funcionario_in_db.usuario.ativo = novo_status

    return funcionario_crud.update_funcionario_in_db(db, funcionario_to_update=funcionario_in_db)