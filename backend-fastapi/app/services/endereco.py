# ---------------------------------------------------------------------------
# ARQUIVO: services/endereco.py
# DESCRIÇÃO: Camada de serviço com a lógica de negócio para Endereços.
#            (Atualmente contém uma função utilitária para conversão)
# ---------------------------------------------------------------------------

from app.schemas.endereco import Endereco # Importa o schema Pydantic 'Endereco'
from app.db.models.endereco import Endereco as EnderecoModel # Importa o modelo SQLAlchemy 'EnderecoModel'
from app.core.enum import State, EntityType # Importa os Enums necessários

def address_client_to_db(id_entity: int, type_entity: EntityType, address_client: list[Endereco]) -> list[EnderecoModel]:
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