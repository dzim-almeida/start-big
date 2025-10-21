# ---------------------------------------------------------------------------
# ARQUIVO: services/cliente.py
# DESCRIÇÃO: Camada de serviço com a lógica de negócio para Clientes.
#            Implementa a criação polimórfica de Clientes Pessoa Física.
# ---------------------------------------------------------------------------

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

# Importa os modelos ORM necessários
from app.db.models.cliente import Cliente as ClienteModel, ClientePF as ClientePFModel
from app.db.models.endereco import Endereco as EnderecoModel
# Importa o schema Pydantic de entrada
from app.schemas.cliente import ClientePFCreate
# Importa a camada de acesso a dados (CRUD)
from app.db.crud import cliente as client_crud
# Importa os Enums para conversão de tipo
from app.core.enum import State, Gender


def create_client_service(db: Session, data_client: ClientePFCreate) -> ClienteModel:
    """
    Serviço para criar um novo cliente Pessoa Física completo.

    Esta função implementa a herança polimórfica:
    1. Valida regras de negócio (ex: CPF duplicado).
    2. Cria uma lista de objetos EnderecoModel.
    3. Cria UMA ÚNICA instância de ClientePFModel com todos os dados
       (base, específicos de PF e endereços).
    4. Passa o objeto completo para a camada CRUD para persistência.

    Args:
        db (Session): A sessão do banco de dados.
        data_client (ClientePFCreate): Os dados validados do novo cliente.

    Raises:
        HTTPException: 409 (Conflict) se o CPF já existir.

    Returns:
        ClienteModel: O objeto do cliente recém-criado (polimorficamente
                      carregado como ClientePFModel), completo com IDs.
    """

    # 1. REGRA DE NEGÓCIO: Verificar se o CPF já existe
    existing_client = client_crud.get_client_by_cpf(db, data_client.cpf)
    
    if existing_client:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="CPF já cadastrado")

    # 2. PREPARA OS OBJETOS DE ENDEREÇO (FILHOS)
    # Cria uma lista de EnderecoModel a partir dos dados do schema
    new_address_client_to_db = [
        EnderecoModel(
            logradouro=endereco.logradouro,
            numero=endereco.numero,
            complemento=endereco.complemento,
            bairro=endereco.bairro,
            cidade=endereco.cidade,
            estado=State(endereco.estado), # Converte a string do schema para o Enum do modelo
            cep=endereco.cep
        ) for endereco in data_client.endereco or [] # 'or []' trata o caso de lista de endereços ser nula/vazia
    ]   


    # 3. PREPARA O OBJETO PRINCIPAL (ClientePFModel)
    # Cria uma única instância da classe filha polimórfica
    new_client_pf_to_db = ClientePFModel(

        # Campos herdados de 'Cliente'
        email=data_client.email,
        contato=data_client.contato,
        observacoes=data_client.observacoes,

        # Campos específicos de 'ClientePF'
        nome=data_client.nome,
        cpf=data_client.cpf,
        rg=data_client.rg,
        genero=Gender(data_client.genero) if data_client.genero else None, # Converte para Enum
        data_nascimento=data_client.data_nascimento,

        # Conecta o relacionamento com a lista de endereços
        endereco = new_address_client_to_db
    )

    # 4. CHAMA A CAMADA CRUD
    # Passa o objeto completo para a função do CRUD
    new_client_in_db = client_crud.create_client_base(db, new_client_pf_to_db)

    # 5. RETORNA O OBJETO PERSISTIDO
    # O CRUD (com db.refresh) garante que este objeto está completo
    return new_client_in_db