# ---------------------------------------------------------------------------
# ARQUIVO: services/cliente.py
# DESCRIÇÃO: Camada de serviço com a lógica de negócio para Clientes.
#            Implementa a criação polimórfica de Clientes Pessoa Física
#            e Pessoa Jurídica, busca, atualização e deleção.
# ---------------------------------------------------------------------------

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Sequence, List

# Importa os modelos ORM necessários
from app.db.models.cliente import Cliente as ClienteModel, ClientePF as ClientePFModel, ClientePJ as ClientePJModel
# Importa os schemas Pydantic de entrada/atualização
from app.schemas.cliente import ClienteUpdate, ClientePFCreate, ClientePFUpdate, ClientePJCreate, ClientePJUpdate
# Importa a camada de acesso a dados (CRUD)
from app.db.crud import cliente as client_crud
# Importa o serviço de endereço para reutilização da lógica
from app.services import endereco as address_service
# Importa os Enums para conversão de tipo
from app.core.enum import Gender, EntityType


# =========================
# Serviço: Criar Cliente PF
# =========================
def create_client_pf(db: Session, new_client_pf: ClientePFCreate) -> ClientePFModel:
    """
    Serviço para criar um novo cliente Pessoa Física completo.
    """

    validation_errors = []

    # 1. Validações de Conflito (CPF, Email, RG)
    error_cpf = client_crud.verify_client_conflict(
        db, new_client_pf.cpf, client_crud.get_client_by_cpf, "CPF"
    )
    if error_cpf:
        if error_cpf == "disabled client":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cliente desabilitado com este CPF. Por favor, reative o cadastro."
            )
        validation_errors.append({"campo": "cpf", "mensagem": error_cpf})

    error_email = client_crud.verify_client_conflict(
        db, new_client_pf.email, client_crud.get_client_by_email, "Email"
    )
    if error_email:
        validation_errors.append({"campo": "email", "mensagem": error_email})

    error_rg = client_crud.verify_client_conflict(
        db, new_client_pf.rg, client_crud.get_client_by_rg, "RG"
    )
    if error_rg:
        validation_errors.append({"campo": "rg", "mensagem": error_rg})
    
    if validation_errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, # Alterado para 422
            detail=validation_errors
        )

    # 2. PREPARA O OBJETO PRINCIPAL (ClientePFModel)
    new_client_pf_to_db = ClientePFModel(
        email=new_client_pf.email,
        contato=new_client_pf.contato,
        observacoes=new_client_pf.observacoes,
        nome=new_client_pf.nome,
        cpf=new_client_pf.cpf,
        rg=new_client_pf.rg,
        # Conversão de Enum
        genero=Gender(new_client_pf.genero) if new_client_pf.genero else None, 
        data_nascimento=new_client_pf.data_nascimento,
    )
    
    # 3. CHAMA A CAMADA CRUD (para obter o ID)
    new_client_pf_in_db = client_crud.create_client_pf(db, new_client_pf_to_db)

    # 4. PREPARA E VINCULA OS ENDEREÇOS
    new_address_client_to_db = address_service.address_to_db(
        new_client_pf_in_db.id,
        EntityType.CLIENTE,
        new_client_pf.endereco
    )
    
    new_client_pf_in_db.endereco = new_address_client_to_db
    
    # 5. RETORNA O OBJETO PERSISTIDO
    return new_client_pf_in_db


# =========================
# Serviço: Criar Cliente PJ
# =========================
def create_client_pj(db: Session, new_client_pj: ClientePJCreate) -> ClientePJModel:
    """
    Serviço para criar um novo cliente Pessoa Jurídica completo.
    """

    validation_errors = []

    # 1. Validações de Conflito (CNPJ, IE)
    error_cnpj = client_crud.verify_client_conflict(
        db, new_client_pj.cnpj, client_crud.get_client_by_cnpj, "CNPJ"
    )
    if error_cnpj:
        if error_cnpj == "disabled client":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cliente desabilitado com este CNPJ. Por favor, reative o cadastro."
            )
        validation_errors.append({"campo": "cnpj", "mensagem": error_cnpj})

    error_ie = client_crud.verify_client_conflict(
        db, new_client_pj.ie, client_crud.get_client_by_ie, "Inscrição Estadual"
    )
    if error_ie:
        validation_errors.append({"campo": "ie", "mensagem": error_ie})
    
    if validation_errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, # Alterado para 422
            detail=validation_errors
        )

    # 2. PREPARA O OBJETO PRINCIPAL (ClientePJModel)
    new_client_pj_to_db = ClientePJModel(
        email=new_client_pj.email,
        contato=new_client_pj.contato,
        observacoes=new_client_pj.observacoes,
        razao_social=new_client_pj.razao_social,
        cnpj=new_client_pj.cnpj,
        nome_fantasia=new_client_pj.nome_fantasia,
        ie=new_client_pj.ie,
        responsavel=new_client_pj.responsavel,
    )

    # 3. CHAMA A CAMADA CRUD (para obter o ID)
    new_client_pj_in_db = client_crud.create_client_pj(db, new_client_pj_to_db)

    # 4. PREPARA E VINCULA OS ENDEREÇOS
    new_address_client_to_db = address_service.address_to_db(
        new_client_pj_in_db.id,
        EntityType.CLIENTE,
        new_client_pj.endereco
    )
    
    new_client_pj_in_db.endereco = new_address_client_to_db

    # 5. RETORNA O OBJETO PERSISTIDO
    return new_client_pj_in_db

# =========================
# Serviço: Buscar TODOS os Clientes
# =========================
def get_all_clients(db: Session) -> Sequence[ClienteModel]:
    """
    Busca TODOS os clientes cadastrados. (Apenas delega para o CRUD).
    """
    return client_crud.get_all_clients(db)

# =========================
# Serviço: Buscar Clientes
# =========================
def get_client_by_search(db: Session, search: str) -> Sequence[ClienteModel]: # Corrigido retorno
    """
    Busca clientes (PF ou PJ) de forma polimórfica usando a camada CRUD.
    """
    return client_crud.get_client_by_search(db, search)

# =========================
# Serviço: Atualizar Cliente
# =========================
def update_client_by_id(db: Session, id: int, client: ClienteUpdate) -> ClienteModel:
    """
    Atualiza um cliente existente (PF ou PJ) pelo ID.
    """
    
    # 1. Busca o cliente existente no banco pelo ID
    update_client = client_crud.get_client_by_id(db, id)

    if not update_client:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")
    
    # 2. Extrai apenas os dados enviados na requisição (para atualização parcial)
    update_data = client.model_dump(exclude_unset=True)
    
    # 3. Tratamento especial para atualizar/substituir a lista de endereços
    if "endereco" in update_data and update_data["endereco"] is not None:
        updated_addresses = address_service.update_address_in_db(
            update_client.endereco,
            client.endereco,
            update_client.id,
            EntityType.CLIENTE
        )
        update_client.endereco = updated_addresses
        # Remove 'endereco' do dict principal para evitar a atualização de relacionamento
        del update_data["endereco"]
    
    # 4. Itera sobre os dados restantes (simples) e atualiza o objeto SQLAlchemy
    for key, value in update_data.items():
        # Pula 'tipo' (não deve ser atualizado)
        if key == "tipo":
            continue
            
        # Converte Enum de Gênero, se for um ClientePF e o campo existir
        if key == "genero" and value is not None and isinstance(client, ClientePFUpdate):
            value = Gender(value)
            
        # Define o novo valor no objeto SQLAlchemy
        setattr(update_client, key, value)
    
    # 5. Chama o CRUD para persistir as alterações
    return client_crud.update_client_in_db(db, update_client)

# =========================
# Serviço: Ativar Cliente
# =========================
def active_client_by_id(db: Session, client_id: int) -> ClienteModel: # Corrigido retorno
    """
    Serviço para ativar um cliente pelo seu ID.
    """
    # 1. Busca o cliente
    existing_client = client_crud.get_client_by_id(db, client_id)

    if not existing_client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")
    
    # 2. Atualiza o objeto em memória
    existing_client.ativo = True

    # 3. Delega a ativação para o CRUD e retorna o objeto
    return client_crud.active_client_by_id(db, existing_client)

# =========================
# Serviço: Desativar Cliente
# =========================
def disable_client_by_id(db: Session, client_id: int) -> ClienteModel: # Corrigido retorno
    """
    Serviço para desativar um cliente pelo seu ID.
    """
    # 1. Busca o cliente
    existing_client = client_crud.get_client_by_id(db, client_id)

    if not existing_client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")
    
    # 2. Atualiza o objeto em memória
    existing_client.ativo = False

    # 3. Delega a desativação para o CRUD e retorna o objeto
    return client_crud.disable_client_by_id(db, existing_client)