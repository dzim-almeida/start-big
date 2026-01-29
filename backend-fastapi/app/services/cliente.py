# ---------------------------------------------------------------------------
# ARQUIVO: cliente_service.py
# MÓDULO: Regras de Negócio (Service Layer)
# DESCRIÇÃO: Orquestra validações, verificação de conflitos e persistência.
# ---------------------------------------------------------------------------

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Sequence, List

from app.db.models.cliente import Cliente as ClienteModel, ClientePF as ClientePFModel, ClientePJ as ClientePJModel
from app.schemas.cliente import ClienteUpdate, ClientePFCreate, ClientePFUpdate, ClientePJCreate
from app.db.crud import cliente as cliente_crud
from app.services import endereco as address_service
from app.core.enum import Gender, EntityType

# Definição de exceções padrão para reutilização
conflict_exce = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Cliente já cadastrado no sistema"
)

not_found_exce = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Cliente não encontrado no sistema"
)

validation_exce = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail=...
)

# Campos que exigem verificação de unicidade no banco
unique_fields = ["cpf", "cnpj", "rg", "ie"]

# Mapa de validadores mapeando campo -> função de busca no CRUD
validators = {
    "cpf": cliente_crud.get_cliente_by_cpf,
    "cnpj": cliente_crud.get_cliente_by_cnpj,
    "rg": cliente_crud.get_cliente_by_rg,
    "ie": cliente_crud.get_cliente_by_ie
}

# ===========================================================================
# LÓGICA DE CRIAÇÃO (CREATE)
# ===========================================================================

def create_cliente_pf(db: Session, cliente_pf_to_add: ClientePFCreate) -> ClientePFModel:
    """
    Aplica regras de negócio para criação de Pessoa Física.
    
    1. Verifica conflitos de dados únicos (CPF, RG, Email).
    2. Instancia o modelo ORM.
    3. Persiste o cliente.
    4. Processa e vincula os endereços.
    """
    validation_errors = []
    
    # Extrai dicionário excluindo endereços (tratados separadamente) e campos não setados
    cliente_data = cliente_pf_to_add.model_dump(exclude={"endereco"}, exclude_unset=True)

    # Loop de validação de unicidade
    for field in unique_fields:
        value = cliente_data.get(field)
        if value is not None:
            error = cliente_crud.verify_cliente_conflict(
                db=db, value=value, search_method=validators[field], search_name=field
            )
            if error:
                # Tratamento especial para cliente desativado
                if error == "disabled cliente":
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="cliente desabilitado com este CPF. Por favor, reative o cadastro."
                    )
                validation_errors.append({"campo": field, "mensagem": error})
    
    if validation_errors:
        validation_exce.detail = validation_errors
        raise validation_exce

    # Instanciação do Modelo
    cliente_pf_to_db = ClientePFModel(**cliente_data)
    
    # Persistência do Pai (Cliente)
    cliente_pf_in_db = cliente_crud.create_cliente(db, cliente_to_add=cliente_pf_to_db)

    # Persistência dos Filhos (Endereços)
    if cliente_pf_to_add.endereco:
        address_cliente_to_db = address_service.address_to_db(
            id_entity=cliente_pf_in_db.id,
            type_entity=EntityType.CLIENTE,
            address_data=cliente_pf_to_add.endereco
        )
    
        cliente_pf_in_db.endereco = address_cliente_to_db
    
    return cliente_pf_in_db


def create_cliente_pj(db: Session, cliente_pj_to_add: ClientePJCreate) -> ClientePJModel:
    """
    Aplica regras de negócio para criação de Pessoa Jurídica.
    Semelhante ao fluxo de PF, mas valida CNPJ/IE/Razão Social.
    """
    validation_errors = []

    cliente_data = cliente_pj_to_add.model_dump(exclude={"endereco"}, exclude_unset=True)

    for field in unique_fields:
        value = cliente_data.get(field)
        if value is not None:
            error = cliente_crud.verify_cliente_conflict(
                db=db, value=value, search_method=validators[field], search_name=field
            )
            if error:
                if error == "disabled cliente":
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="cliente desabilitado com este CNPJ. Por favor, reative o cadastro."
                    )
                validation_errors.append({"campo": field, "mensagem": error})
    
    if validation_errors:
        validation_exce.detail = validation_errors
        raise validation_exce

    new_cliente_pj_to_db = ClientePJModel(**cliente_data)

    new_cliente_pj_in_db = cliente_crud.create_cliente(db, cliente_to_add=new_cliente_pj_to_db)

    address_cliente_to_db = address_service.address_to_db(
        id_entity=new_cliente_pj_in_db.id,
        type_entity=EntityType.CLIENTE,
        address_data=cliente_pj_to_add.endereco
    )
    
    new_cliente_pj_in_db.endereco = address_cliente_to_db

    return new_cliente_pj_in_db

# ===========================================================================
# LÓGICA DE LEITURA (READ)
# ===========================================================================

def get_cliente_by_search(db: Session, search: str | None) -> Sequence[ClienteModel]: 
    """
    Intermediário para busca de clientes.
    Repassa a query string para o CRUD realizar a filtragem polimórfica.
    """
    return cliente_crud.get_cliente_by_search(db, search=search)

# ===========================================================================
# LÓGICA DE ATUALIZAÇÃO (UPDATE)
# ===========================================================================

def update_cliente_by_id(db: Session, cliente_id: int, cliente_to_update: ClienteUpdate) -> ClienteModel:
    """
    Atualiza dados de um cliente existente.
    Suporta atualização parcial (PATCH behavior via PUT).
    Gerencia a lógica complexa de atualização de lista de endereços.
    """
    validation_errors = []
    
    # Recupera o registro atual
    cliente_in_db = cliente_crud.get_cliente_by_id(db, cliente_id)
    if not cliente_in_db:
         raise not_found_exce
    
    data_to_update = cliente_to_update.model_dump(exclude_unset=True)

    # Validação de conflitos para campos que estão sendo alterados
    for field in unique_fields:
        value = data_to_update.get(field)
        if value is not None:
            error = cliente_crud.verify_cliente_conflict(
                db=db, cliente_id=cliente_id, value=value, search_method=validators[field], search_name=field
            )
            if error:
                validation_errors.append({"campo": field, "mensagem": error})

    if validation_errors:
        validation_exce.detail = validation_errors
        raise validation_exce
    
    # Atualização de Endereços (Delega para serviço específico)
    if "endereco" in data_to_update:
        updated_addresses = address_service.update_address_in_db(
            address_in_db=cliente_in_db.endereco,
            address_to_update=cliente_to_update.endereco,
            id_entity=cliente_in_db.id,
            type_entity=EntityType.CLIENTE
        )
        cliente_in_db.endereco = updated_addresses
        del data_to_update["endereco"]
    
    # Atualização de Campos Escalares
    for key, value in data_to_update.items():
        if key == "tipo":
            continue
            
        # Cast de Enum se necessário
        if key == "genero" and value is not None and isinstance(cliente_to_update, ClientePFUpdate):
            value = Gender(value)
            
        setattr(cliente_in_db, key, value)
    
    return cliente_crud.update_cliente_in_db(db, cliente_to_update=cliente_in_db)

# ===========================================================================
# LÓGICA DE STATUS (TOGGLE)
# ===========================================================================

def toggle_active_disable_cliente_by_id(db: Session, cliente_id: int) -> ClienteModel:
    """
    Inverte o status 'ativo' do cliente (True <-> False).
    """
    cliente_in_db = cliente_crud.get_cliente_by_id(db, cliente_id=cliente_id)

    if not cliente_in_db:
        raise not_found_exce
    
    cliente_in_db.ativo = not cliente_in_db.ativo

    return cliente_crud.update_cliente_in_db(db, cliente_to_update=cliente_in_db)