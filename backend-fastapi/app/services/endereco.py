# ---------------------------------------------------------------------------
# ARQUIVO: services/endereco.py
# DESCRIÇÃO: Camada de serviço com a lógica de negócio para Endereços.
#            Contém funções utilitárias para criação e atualização
#            de endereços polimórficos.
# ---------------------------------------------------------------------------
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.endereco import Endereco, EnderecoUpdate # Importa os schemas Pydantic
from app.db.models.endereco import Endereco as EnderecoModel # Importa o modelo SQLAlchemy
from app.core.enum import State, EntityType # Importa os Enums necessários
from app.db.crud import endereco as address_crud

def address_to_db(id_entity: int, type_entity: EntityType, address_client: list[Endereco]) -> list[EnderecoModel]:
    """
    Converte uma lista de schemas Pydantic 'Endereco' em uma lista
    de modelos SQLAlchemy 'EnderecoModel', vinculando-os a uma entidade.

    Args:
        id_entity (int): O ID da entidade (ex: Cliente.id) à qual os endereços pertencem.
        type_entity (EntityType): O tipo da entidade (ex: EntityType.CLIENTE).
        address_client (list[Endereco]): A lista de objetos schema Pydantic de endereço.

    Returns:
        list[EnderecoModel]: Uma lista de objetos modelo SQLAlchemy, prontos
                             para serem adicionados à sessão do banco de dados.
    """
    # Itera sobre a lista de schemas Pydantic (address_client)
    # 'or []' é uma proteção para caso a lista de entrada seja None
    new_address_client_to_db = [
        EnderecoModel(
            id_entidade=id_entity,
            tipo_entidade=type_entity,
            logradouro=address.logradouro,
            numero=address.numero,
            complemento=address.complemento,
            bairro=address.bairro,
            cidade=address.cidade,
            estado=State(address.estado), # Converte a string do schema para o Enum do modelo
            cep=address.cep,
        ) for address in address_client or []
    ]
    # Retorna a lista de modelos SQLAlchemy
    return new_address_client_to_db

def update_address_in_db(address_in_db: list[EnderecoModel], address_update: list[EnderecoUpdate], id_entity: int, type_entity: EntityType) -> list[EnderecoModel]:
    """
    Atualiza uma lista de objetos EnderecoModel (do banco) com dados
    de uma lista de schemas EnderecoUpdate (do payload).

    Esta função implementa uma lógica de "find-and-update" baseada no ID.
    (Nota: Não lida com a criação de novos ou deleção de antigos,
     apenas atualiza os existentes que são passados.)

    Args:
        address_in_db (list[EnderecoModel]): A lista de endereços
                                             existentes no banco (objetos SQLAlchemy).
        address_update (list[EnderecoUpdate]): A lista de dados de atualização
                                               (objetos Pydantic).

    Returns:
        list[EnderecoModel]: A lista de objetos SQLAlchemy 'address_in_db'
                             com os atributos modificados.
    """
    # Itera sobre a lista de objetos de atualização do Pydantic
    for address in address_update:
        # Converte o objeto Pydantic em um dicionário, excluindo campos não enviados
        address_data = address.model_dump(exclude_unset=True)
        # Garante que temos um ID para fazer a correspondência
        if address_data["id"] is not None:
            # Itera sobre a lista de objetos do banco
            for db_address in address_in_db:
                # Encontra o endereço correspondente pelo ID
                if db_address.id == address_data.get("id"):
                    # Itera sobre os campos enviados no payload de atualização
                    for key, value in address_data.items():
                        # Atualiza o atributo no objeto SQLAlchemy
                        setattr(db_address, key, value)
        elif address_data["id"] is None:
            new_address = address_to_db(id_entity, type_entity, [address])
            address_in_db.append(new_address[0])
    # Retorna a lista de objetos do banco, agora modificada
    return address_in_db

def delete_address_in_db(db: Session, address_id: int, entity_id: int, entity_type: EntityType):
    """
    Serviço para deletar um Endereço pelo seu ID de forma segura.

    Implementa a lógica de negócio:
    1. Busca o endereço pelo ID.
    2. Verifica se o endereço foi encontrado (404).
    3. Verifica se o endereço pertence à entidade correta (403).
    4. Delega a exclusão para o CRUD.
    """
    # 1. Busca o endereço existente no banco
    address_in_db = address_crud.get_address_by_id(db, address_id)
    
    # 2. Verifica se o endereço foi encontrado
    if not address_in_db:
        # Lança erro 404 se não encontrado
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endereço não encontrado."
        )
        
    # 3. Verifica se o endereço pertence à entidade fornecida (Regra de Segurança)
    if (address_in_db.id_entidade != entity_id or address_in_db.tipo_entidade != entity_type):
        # Lança erro 403 (Proibido) se o endereço não pertencer
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Endereço não pertece à entidade fornecida."
        )
        
    # 4. Delega a exclusão para a camada CRUD
    address_crud.delete_address_by_id(db, address_in_db)