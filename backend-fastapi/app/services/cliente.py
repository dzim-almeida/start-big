# ---------------------------------------------------------------------------
# ARQUIVO: services/cliente.py
# DESCRIÇÃO: Camada de serviço com a lógica de negócio para Clientes.
#            Implementa a criação polimórfica de Clientes Pessoa Física
#            e Pessoa Jurídica, busca, atualização e deleção.
# ---------------------------------------------------------------------------

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Sequence # Importação para type hint de lista

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

    Implementa a herança polimórfica:
    1. Valida regras de negócio (ex: CPF duplicado).
    2. Cria a instância de ClientePFModel (sem endereços).
    3. Persiste o cliente no banco (para obter o ID).
    4. Chama o serviço de endereço para criar e vincular os endereços.
    5. Retorna o cliente completo.
    """

    # 1. REGRA DE NEGÓCIO: Verificar se o CPF já existe
    existing_client = client_crud.get_client_by_cpf(db, new_client_pf.cpf)
    
    if existing_client:
        # Lança exceção se o CPF já estiver cadastrado
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="CPF já cadastrado")
    
    # 2. PREPARA O OBJETO PRINCIPAL (ClientePFModel)
    # Cria a instância (sem endereços, pois o ID ainda não existe)
    new_client_pf_to_db = ClientePFModel(
        # Campos herdados de 'Cliente'
        email=new_client_pf.email,
        contato=new_client_pf.contato,
        observacoes=new_client_pf.observacoes,

        # Campos específicos de 'ClientePF'
        nome=new_client_pf.nome,
        cpf=new_client_pf.cpf,
        rg=new_client_pf.rg,
        genero=Gender(new_client_pf.genero) if new_client_pf.genero else None, # Converte para Enum
        data_nascimento=new_client_pf.data_nascimento,
    )
    
    # 3. CHAMA A CAMADA CRUD (para obter o ID)
    # Persiste o cliente PF (add, flush, refresh)
    new_client_pf_in_db = client_crud.create_client_pf(db, new_client_pf_to_db)

    # 4. PREPARA E VINCULA OS ENDEREÇOS
    # Chama o serviço de endereço para criar as instâncias de EnderecoModel
    # passando o ID recém-criado e o tipo da entidade.
    new_address_client_to_db = address_service.address_to_db(
        new_client_pf_in_db.id, # O ID obtido do passo 3
        EntityType.CLIENTE,
        new_client_pf.endereco # A lista de schemas Pydantic de endereço
    )
    
    # Vincula a lista de modelos de endereço ao cliente (em memória)
    new_client_pf_in_db.endereco = new_address_client_to_db
    
    # 5. RETORNA O OBJETO PERSISTIDO
    # O objeto já está completo e será comitado pelo endpoint
    return new_client_pf_in_db


# =========================
# Serviço: Criar Cliente PJ
# =========================
def create_client_pj(db: Session, new_client_pj: ClientePJCreate) -> ClientePJModel:
    """
    Serviço para criar um novo cliente Pessoa Jurídica completo.

    Fluxo idêntico ao de PF:
    1. Valida regras de negócio (ex: CNPJ duplicado).
    2. Cria a instância de ClientePJModel (sem endereços).
    3. Persiste o cliente no banco (para obter o ID).
    4. Chama o serviço de endereço para criar e vincular os endereços.
    5. Retorna o cliente completo.
    """

    # 1. REGRA DE NEGÓCIO: Verificar se o CNPJ já existe
    existing_client = client_crud.get_client_by_cnpj(db, new_client_pj.cnpj)
    
    if existing_client:
        # Lança exceção se o CNPJ já estiver cadastrado
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="CNPJ já cadastrado")

    # 2. PREPARA O OBJETO PRINCIPAL (ClientePJModel)
    new_client_pj_to_db = ClientePJModel(
        # Campos herdados de 'Cliente'
        email=new_client_pj.email,
        contato=new_client_pj.contato,
        observacoes=new_client_pj.observacoes,

        # Campos específicos de 'ClientePJ'
        razao_social=new_client_pj.razao_social,
        cnpj=new_client_pj.cnpj,
        nome_fantasia=new_client_pj.nome_fantasia,
        ie=new_client_pj.ie,
        responsavel=new_client_pj.responsavel,
    )

    # 3. CHAMA A CAMADA CRUD (para obter o ID)
    new_client_pj_in_db = client_crud.create_client_pj(db, new_client_pj_to_db)

    # 4. PREPARA E VINCULA OS ENDEREÇOS
    # Chama o serviço de endereço reutilizado
    new_address_client_to_db = address_service.address_to_db(
        new_client_pj_in_db.id,
        EntityType.CLIENTE,
        new_client_pj.endereco
    )
    
    # Vincula a lista de modelos de endereço ao cliente
    new_client_pj_in_db.endereco = new_address_client_to_db

    # 5. RETORNA O OBJETO PERSISTIDO
    return new_client_pj_in_db


# =========================
# Serviço: Buscar Clientes
# =========================
# (Nota: O tipo de retorno 'ClienteModel' está inconsistente com
#  a implementação do CRUD, que retorna uma lista)
def get_client_by_search(db: Session, search: str) -> ClienteModel:
    """
    Busca clientes (PF ou PJ) de forma polimórfica usando a camada CRUD.
    Retorna a lista de clientes encontrada (pode ser vazia).
    """
    # Delega a busca para a função do CRUD que executa a query polimórfica
    existing_clients = client_crud.get_client_by_search(db, search)
    
    # Retorna a lista de clientes encontrada (pode ser vazia)
    return existing_clients

# =========================
# Serviço: Atualizar Cliente
# =========================
def update_client_by_id(db: Session, id: int, client: ClienteUpdate) -> ClienteModel:
    """
    Atualiza um cliente existente (PF ou PJ) pelo ID.
    Busca o cliente, aplica atualizações parciais (incluindo endereços)
    e retorna o objeto SQLAlchemy atualizado.
    """
    
    # 1. Busca o cliente existente no banco pelo ID
    update_client = client_crud.get_client_by_id(db, id)

    # 2. Verifica se o cliente foi encontrado
    if not update_client:
         # Lança erro 404 se não encontrado
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")
    
    # 3. Verifica o tipo do payload recebido (PF ou PJ) usando isinstance
    if isinstance(client, ClientePFUpdate):
        # Extrai apenas os dados enviados na requisição (para atualização parcial)
        update_data = client.model_dump(exclude_unset=True)
        # Atualiza os campos simples do objeto SQLAlchemy
        for key, value in update_data.items():
            # Pula 'tipo' e 'endereco' (tratado separadamente)
            if key not in ["tipo", "endereco"]:
                # Converte Enum de Gênero, se presente
                if key == "genero" and value is not None:
                    value = Gender(value)
                # Define o novo valor no objeto SQLAlchemy
                setattr(update_client, key, value)
        
        # 4. Tratamento especial para atualizar/substituir a lista de endereços
        if "endereco" in update_data and update_data["endereco"] is not None:
            # Chama o serviço de endereço para lidar com a atualização da lista
            updated_addresses = address_service.update_address_in_db(
                update_client.endereco, # Lista de endereços do banco
                client.endereco,        # Lista de dados de atualização do schema
                update_client.id,
                EntityType.CLIENTE         
            )
            update_client.endereco = updated_addresses

        # 5. Chama o CRUD para persistir as alterações (flush + refresh)
        return client_crud.update_client_in_db(db, update_client)
    
    elif isinstance(client, ClientePJUpdate):
        # Lógica similar para Cliente PJ
        update_data = client.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            # Pula 'tipo' e 'endereco'
            if key not in ["tipo", "endereco"]:
                # Define o novo valor no objeto SQLAlchemy
                setattr(update_client, key, value)

        # 4. Tratamento especial para atualizar/substituir a lista de endereços
        if "endereco" in update_data and update_data["endereco"] is not None:
            # Chama o serviço de endereço para lidar com a atualização da lista
            updated_addresses = address_service.update_address_in_db(
                update_client.endereco, # Lista de endereços do banco
                client.endereco,         # Lista de dados de atualização do schema
                update_client.id,
                EntityType.CLIENTE
            )
            update_client.endereco = updated_addresses

        # 5. Chama o CRUD para persistir as alterações (flush + refresh)
        return client_crud.update_client_in_db(db, update_client)
    else:
        # Caso o tipo no payload não seja nem PF nem PJ (não deveria acontecer com a Union)
        raise HTTPException(status_code=400, detail="Tipo de cliente inválido recebido")

# =========================
# Serviço: Deletar Cliente
# =========================
def delete_client_by_id(db: Session, id: int) -> bool:
    """
    Serviço para deletar um cliente pelo seu ID.

    1. Busca o cliente.
    2. Se encontrado, delega a exclusão para o CRUD.
    3. Retorna True se a exclusão foi solicitada.
    """
    # 1. Busca o cliente existente pelo ID
    existing_client = client_crud.get_client_by_id(db, id)

    # 2. Verifica se o cliente foi encontrado
    if not existing_client:
        # Lança erro 404 se não encontrado
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")

    # 3. Delega a exclusão para a camada CRUD
    return client_crud.delete_client_by_id(db, existing_client)