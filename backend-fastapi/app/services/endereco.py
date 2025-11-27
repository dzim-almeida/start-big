# ---------------------------------------------------------------------------
# ARQUIVO: services/endereco.py
# DESCRIÇÃO: Camada de serviço com a lógica de negócio para Endereços.
#            Contém funções utilitárias para criação e atualização
#            de endereços polimórficos, usados por outras entidades (Empresa, Funcionario).
# ---------------------------------------------------------------------------
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.schemas.endereco import Endereco, EnderecoUpdate # Importa os schemas Pydantic
from app.db.models.endereco import Endereco as EnderecoModel # Importa o modelo SQLAlchemy
from app.core.enum import State, EntityType # Importa os Enums necessários
from app.db.crud import endereco as address_crud

# =========================
# Função Utilitária: Converter Schema Pydantic para Modelo ORM
# =========================
def address_to_db(id_entity: int, type_entity: EntityType, address_data: List[Endereco]) -> List[EnderecoModel]:
    """
    Converte uma lista de schemas Pydantic 'Endereco' em uma lista
    de modelos SQLAlchemy 'EnderecoModel', vinculando-os a uma entidade.

    Args:
        id_entity (int): O ID da entidade (ex: Empresa.id) à qual os endereços pertencem.
        type_entity (EntityType): O tipo da entidade (ex: EntityType.EMPRESA).
        address_data (list[Endereco]): A lista de objetos schema Pydantic de endereço.

    Returns:
        list[EnderecoModel]: Uma lista de objetos modelo SQLAlchemy, prontos
                             para serem adicionados à sessão do banco de dados.
    """
    # Cria uma lista de modelos SQLAlchemy através de uma list comprehension
    new_address_data_to_db = [
        EnderecoModel(
            id_entidade=id_entity,
            tipo_entidade=type_entity,
            logradouro=address.logradouro,
            numero=address.numero,
            complemento=address.complemento,
            bairro=address.bairro,
            cidade=address.cidade,
            # Converte a string do schema para o Enum do modelo
            estado=State(address.estado), 
            cep=address.cep,
        ) for address in address_data or []
    ]
    # Retorna a lista de modelos SQLAlchemy
    return new_address_data_to_db


# =========================
# Função Utilitária: Atualizar Endereço Existente
# =========================
def update_address_in_db(address_in_db: List[EnderecoModel], address_update: List[EnderecoUpdate], id_entity: int, type_entity: EntityType) -> List[EnderecoModel]:
    """
    Atualiza uma lista de objetos EnderecoModel (do banco) com dados
    de uma lista de schemas EnderecoUpdate (do payload).

    Implementa a lógica de:
    1. Atualização: Se o objeto de atualização tiver um ID, ele é encontrado e atualizado.
    2. Criação: Se o objeto de atualização NÃO tiver um ID, um novo endereço é criado
                e anexado à lista existente (`address_in_db`).

    Args:
        address_in_db (list[EnderecoModel]): A lista de endereços existentes no banco (ORM).
        address_update (list[EnderecoUpdate]): A lista de dados de atualização (Pydantic).
        id_entity (int): ID da entidade pai para novos endereços.
        type_entity (EntityType): Tipo da entidade pai para novos endereços.

    Returns:
        list[EnderecoModel]: A lista de objetos SQLAlchemy com as alterações (incluindo novos).
    """
    # 1. Itera sobre a lista de objetos de atualização do Pydantic
    for address in address_update:
        # Converte o objeto Pydantic em um dicionário, excluindo campos não enviados
        address_data = address.model_dump(exclude_unset=True)
        
        # 2. LÓGICA DE ATUALIZAÇÃO: Se o ID existir (atualização de um endereço existente)
        if address_data.get("id") is not None:
            # Encontra o endereço correspondente na lista do banco
            db_address = next((addr for addr in address_in_db if addr.id == address_data.get("id")), None)
            
            if db_address:
                # Itera sobre os campos enviados e atualiza o objeto SQLAlchemy
                for key, value in address_data.items():
                    setattr(db_address, key, value)
        
        # 3. LÓGICA DE CRIAÇÃO: Se o ID for None (criação de novo endereço)
        elif address_data.get("id") is None:
            # Reutiliza a função de mapeamento para criar o novo modelo ORM
            # (Enviamos a lista de 1 elemento [address] e pegamos o [0])
            new_address = address_to_db(id_entity, type_entity, [address])
            # Anexa o novo endereço à lista que será persistida
            address_in_db.append(new_address[0])
            
    # Retorna a lista de objetos do banco, agora modificada e potencialmente maior
    return address_in_db


# =========================
# Serviço: Deletar Endereço
# =========================
def delete_address_in_db(db: Session, address_id: int, entity_id: int, entity_type: EntityType) -> None:
    """
    Serviço para deletar um Endereço pelo seu ID de forma segura.

    Implementa a lógica de negócio:
    1. Busca o endereço pelo ID.
    2. Verifica se o endereço foi encontrado (404).
    3. Verifica se o endereço pertence à entidade correta (403 - Segurança).
    4. Delega a exclusão para o CRUD.
    """
    # 1. Busca o endereço existente no banco
    address_in_db = address_crud.get_address_by_id(db, address_id)
    
    # 2. Verifica se o endereço foi encontrado (Regra de Validação)
    if not address_in_db:
        # Lança erro 404 se não encontrado
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endereço não encontrado."
        )
        
    # 3. Verifica se o endereço pertence à entidade fornecida (Regra de Segurança/Negócio)
    if (address_in_db.id_entidade != entity_id or address_in_db.tipo_entidade != entity_type):
        # Lança erro 403 (Proibido) se o endereço não pertencer ao pai correto
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Endereço não pertence à entidade fornecida."
        )
        
    # 4. Delega a exclusão para a camada CRUD
    address_crud.delete_address_by_id(db, address_in_db)