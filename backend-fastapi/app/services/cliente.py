# ---------------------------------------------------------------------------
# ARQUIVO: services/cliente.py
# DESCRIÇÃO: Camada de serviço com a lógica de negócio para Clientes.
#            Implementa a criação polimórfica de Clientes Pessoa Física
#            e Pessoa Jurídica, busca, atualização e deleção.
# ---------------------------------------------------------------------------

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

# Importa os modelos ORM necessários
from app.db.models.cliente import Cliente as ClienteModel, ClientePF as ClientePFModel, ClientePJ as ClientePJModel
from app.db.models.endereco import Endereco as EnderecoModel
# Importa os schemas Pydantic de entrada/atualização
from app.schemas.cliente import ClienteUpdate, ClientePFCreate, ClientePFUpdate, ClientePJCreate, ClientePJUpdate
# Importa a camada de acesso a dados (CRUD)
from app.db.crud import cliente as client_crud
# Importa os Enums para conversão de tipo
from app.core.enum import State, Gender


# =========================
# Serviço: Criar Cliente PF
# =========================
def create_client_pf_service(db: Session, new_client_pf: ClientePFCreate) -> ClientePFModel:
    """
    Serviço para criar um novo cliente Pessoa Física completo.

    Implementa a herança polimórfica:
    1. Valida regras de negócio (ex: CPF duplicado).
    2. Cria uma lista de objetos EnderecoModel.
    3. Cria UMA ÚNICA instância de ClientePFModel com todos os dados
       (base, específicos de PF e endereços).
    4. Passa o objeto completo para a camada CRUD para persistência.

    Args:
        db (Session): A sessão do banco de dados.
        new_client_pf (ClientePFCreate): Os dados validados do novo cliente PF.

    Raises:
        HTTPException: 409 (Conflict) se o CPF já existir.

    Returns:
        ClientePFModel: O objeto do cliente recém-criado, completo com IDs.
    """

    # 1. REGRA DE NEGÓCIO: Verificar se o CPF já existe
    existing_client = client_crud.get_client_by_cpf(db, new_client_pf.cpf)
    
    if existing_client:
        # Lança exceção se o CPF já estiver cadastrado
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
        ) for endereco in new_client_pf.endereco or [] # 'or []' trata o caso de lista de endereços ser nula/vazia
    ]   

    # 3. PREPARA O OBJETO PRINCIPAL (ClientePFModel)
    # Cria uma única instância da classe filha polimórfica
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

        # Conecta o relacionamento com a lista de endereços
        # O nome do atributo 'endereco' deve corresponder ao 'relationship' no modelo Cliente
        endereco = new_address_client_to_db
    )

    # 4. CHAMA A CAMADA CRUD
    # Passa o objeto completo para a função do CRUD específica para PF
    new_client_pf_in_db = client_crud.create_client_pf(db, new_client_pf_to_db)

    # 5. RETORNA O OBJETO PERSISTIDO
    # O CRUD (com db.refresh) garante que este objeto está completo
    return new_client_pf_in_db


# =========================
# Serviço: Criar Cliente PJ
# =========================
def create_client_pj_service(db: Session, new_client_pj: ClientePJCreate) -> ClientePJModel:
    """
    Serviço para criar um novo cliente Pessoa Jurídica completo.

    Implementa a herança polimórfica:
    1. Valida regras de negócio (ex: CNPJ duplicado).
    2. Cria uma lista de objetos EnderecoModel.
    3. Cria UMA ÚNICA instância de ClientePJModel com todos os dados
       (base, específicos de PJ e endereços).
    4. Passa o objeto completo para a camada CRUD para persistência.

    Args:
        db (Session): A sessão do banco de dados.
        new_client_pj (ClientePJCreate): Os dados validados do novo cliente PJ.

    Raises:
        HTTPException: 409 (Conflict) se o CNPJ já existir.

    Returns:
        ClientePJModel: O objeto do cliente recém-criado, completo com IDs.
    """

    # 1. REGRA DE NEGÓCIO: Verificar se o CNPJ já existe
    existing_client = client_crud.get_client_by_cnpj(db, new_client_pj.cnpj)
    
    if existing_client:
        # Lança exceção se o CNPJ já estiver cadastrado
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="CNPJ já cadastrado")

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
        ) for endereco in new_client_pj.endereco or [] # 'or []' trata o caso de lista de endereços ser nula/vazia
    ]   

    # 3. PREPARA O OBJETO PRINCIPAL (ClientePJModel)
    # Cria uma única instância da classe filha polimórfica
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

        # Conecta o relacionamento com a lista de endereços
        # O nome do atributo 'endereco' deve corresponder ao 'relationship' no modelo Cliente
        endereco = new_address_client_to_db
    )

    # 4. CHAMA A CAMADA CRUD
    # Passa o objeto completo para a função do CRUD específica para PJ
    new_client_pj_in_db = client_crud.create_client_pj(db, new_client_pj_to_db)

    # 5. RETORNA O OBJETO PERSISTIDO
    # O CRUD (com db.refresh) garante que este objeto está completo
    return new_client_pj_in_db


# =========================
# Serviço: Buscar Clientes
# =========================
# (Atenção: A assinatura de retorno 'ClienteModel' pode estar incorreta,
#  o CRUD retorna uma lista. Mantida conforme o original.)
def get_client_by_search(db: Session, search: str) -> ClienteModel:
    """
    Busca clientes (PF ou PJ) de forma polimórfica usando a camada CRUD.
    Retorna a lista de clientes encontrada (pode ser vazia).
    (Nota: O tipo de retorno na assinatura está como ClienteModel, mas
     a função retorna a lista 'existing_clients'.)
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
        
        # Tratamento especial para atualizar/substituir a lista de endereços
        if "endereco" in update_data and update_data["endereco"] is not None:

            # Limpa a coleção de endereços existente na memória
            # (Se cascade='delete-orphan', os antigos serão deletados no commit)
            update_client.endereco.clear()

            # Cria novas instâncias de EnderecoModel a partir dos dados do payload
            edit_address_client_to_db = [
                EnderecoModel(
                    logradouro=endereco.logradouro, # Acesso via ponto '.' pois 'endereco' aqui é Pydantic model
                    numero=endereco.numero,
                    complemento=endereco.complemento,
                    bairro=endereco.bairro,
                    cidade=endereco.cidade,
                    estado=State(endereco.estado), # Converte para Enum
                    cep=endereco.cep
                # Itera sobre a lista de objetos Pydantic Endereco dentro de 'client'
                ) for endereco in client.endereco or [] 
            ]

            # Atribui a nova lista de objetos EnderecoModel à relação
            update_client.endereco = edit_address_client_to_db

        # Chama o CRUD para persistir as alterações (flush + refresh)
        return client_crud.update_client_in_db(db, update_client)
    
    elif isinstance(client, ClientePJUpdate):
        # Lógica similar para Cliente PJ
        update_data = client.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            # Pula 'tipo' e 'endereco'
            if key not in ["tipo", "endereco"]:
                # Define o novo valor no objeto SQLAlchemy
                setattr(update_client, key, value)

        # Tratamento especial para atualizar/substituir a lista de endereços
        if "endereco" in update_data and update_data["endereco"] is not None:

                # Limpa a coleção de endereços existente na memória
                update_client.endereco.clear()

                # Cria novas instâncias de EnderecoModel a partir dos dados do payload
                edit_address_client_to_db = [
                    EnderecoModel(
                        logradouro=endereco.logradouro, # Acesso via ponto '.'
                        numero=endereco.numero,
                        complemento=endereco.complemento,
                        bairro=endereco.bairro,
                        cidade=endereco.cidade,
                        estado=State(endereco.estado), # Converte para Enum
                        cep=endereco.cep
                    # Itera sobre a lista de objetos Pydantic Endereco dentro de 'client'
                    ) for endereco in client.endereco or []
                ]

                # Atribui a nova lista de objetos EnderecoModel à relação
                update_client.endereco = edit_address_client_to_db

        # Chama o CRUD para persistir as alterações (flush + refresh)
        return client_crud.update_client_in_db(db, update_client)
    else:
        # Caso o tipo no payload não seja nem PF nem PJ (não deveria acontecer com a Union)
        raise HTTPException(status_code=400, detail="Tipo de cliente inválido recebido")

# =========================
# Serviço: Deletar Cliente - NOVO SERVIÇO
# =========================
def delete_client_by_id(db: Session, id: int) -> bool:
    """
    Serviço para deletar um cliente pelo seu ID.

    1. Busca o cliente.
    2. Se encontrado, delega a exclusão para o CRUD.
    3. Retorna True se a exclusão foi solicitada (não garante commit).

    Args:
        db (Session): A sessão do banco de dados.
        id (int): O ID do cliente a ser deletado.

    Raises:
        HTTPException: 404 (Not Found) se o cliente não for encontrado.

    Returns:
        bool: Retorna True indicando que a operação de deleção foi chamada no CRUD.
              (A confirmação final depende do commit no endpoint).
    """
    # 1. Busca o cliente existente pelo ID
    existing_client = client_crud.get_client_by_id(db, id)

    # 2. Verifica se o cliente foi encontrado
    if not existing_client:
        # Lança erro 404 se não encontrado
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")

    # 3. Delega a exclusão para a camada CRUD
    # O CRUD marcará o objeto para deleção e fará flush
    client_crud.delete_client_by_id(db, existing_client)
    
    # Retorna True para indicar sucesso na chamada do serviço
    # (O commit final é responsabilidade do endpoint)
    return True