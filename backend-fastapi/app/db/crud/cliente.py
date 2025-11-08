# ---------------------------------------------------------------------------
# ARQUIVO: cliente.py (CRUD)
# DESCRIÇÃO: Este módulo contém as funções de CRUD (Create, Read, Update,
#            Delete) para interagir com os modelos de Cliente no banco de dados.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session, aliased
from sqlalchemy import select, or_
from typing import Sequence

from app.db.models.cliente import Cliente as ClienteModel, ClientePF as ClientePFModel, ClientePJ as ClientePJModel

def get_client_by_id(db: Session, id: int) -> ClienteModel | None:
    """
    Busca um cliente (base, PF ou PJ) pelo seu ID (chave primária).
    (Utiliza a sintaxe legada do .query())

    Args:
        db (Session): A sessão do banco de dados.
        id (int): O ID do cliente a ser buscado.

    Returns:
        ClienteModel | None: O objeto do cliente se encontrado, caso contrário None.
    """
    return db.query(ClienteModel).filter(ClienteModel.id == id).first()

def get_all_clients(db: Session) -> Sequence[ClienteModel]:
    """
    Busca TODOS os clientes cadastrados no banco de dados.

    Args:
        db (Session): A sessão do banco de dados.

    Returns:
        Sequence[ClienteModel]: Uma lista (sequência) de todos os clientes.
    """
    # Constrói a query: SELECT * FROM cliente
    stmt = select(ClienteModel)
    # Executa a query e retorna todos os resultados
    clients_in_db = db.scalars(stmt).all()
    return clients_in_db

def get_client_by_cpf(db: Session, cpf: str) -> ClientePFModel | None:
    """
    Busca um único cliente Pessoa Física no banco de dados pelo seu CPF.

    Args:
        db (Session): A sessão do banco de dados.
        cpf (str): O CPF do cliente a ser pesquisado.

    Returns:
        ClientePFModel | None: O objeto do cliente PF se encontrado, caso contrário None.
    """
    # A query é feita diretamente no modelo ClientePFModel para eficiência
    return db.query(ClientePFModel).filter(ClientePFModel.cpf == cpf).first()


def get_client_by_cnpj(db: Session, cnpj: str) -> ClientePJModel | None:
    """
    Busca um único cliente Pessoa Jurídica no banco de dados pelo seu CNPJ.

    Args:
        db (Session): A sessão do banco de dados.
        cnpj (str): O CNPJ do cliente a ser pesquisado.

    Returns:
        ClientePJModel | None: O objeto do cliente PJ se encontrado, caso contrário None.
    """
    # A query é feita diretamente no modelo ClientePJModel para eficiência
    return db.query(ClientePJModel).filter(ClientePJModel.cnpj == cnpj).first()


def get_client_by_search(db: Session, search: str) -> list[ClientePFModel | ClientePJModel]:
    """
    Busca polimórfica por clientes (PF ou PJ) que correspondam ao termo.
    Usa 'aliased' e 'outerjoin' explícito para evitar ambiguidade
    ao consultar múltiplas tabelas filhas.
    """
    
    # Cria aliases explícitos para as tabelas filhas
    pf_alias = aliased(ClientePFModel)
    pj_alias = aliased(ClientePJModel)

    # Define as condições de busca (OR) em ambas as tabelas aliadas
    conditions = or_(
        pf_alias.nome.startswith(search),
        pf_alias.cpf.startswith(search),
        pj_alias.razao_social.startswith(search),
        pj_alias.cnpj.startswith(search),
        pj_alias.nome_fantasia.startswith(search),
    )

    # Inicia a query a partir da classe base ClienteModel
    stmt = select(ClienteModel)
    
    # Adiciona os joins explícitos usando a 'onclause' (id == id)
    # Isso resolve o 'AmbiguousForeignKeysError'
    stmt = stmt.outerjoin(pf_alias, ClienteModel.id == pf_alias.id)
    stmt = stmt.outerjoin(pj_alias, ClienteModel.id == pj_alias.id)
    
    # Aplica o filtro 'WHERE' com as condições
    stmt = stmt.where(conditions)
    
    # Executa a query e retorna a lista de objetos (ClientePF ou ClientePJ)
    result = db.scalars(stmt).all()

    return result


def create_client_pf(db: Session, new_client: ClientePFModel) -> ClientePFModel:
    """
    Adiciona um novo cliente polimórfico (ClientePF) ao banco de dados.

    Esta função é usada para persistir um objeto cliente já construído
    (neste caso, um ClientePF, que também é um Cliente) e seus relacionamentos
    em cascata (como Endereços).

    Args:
        db (Session): A sessão do banco de dados.
        new_client (ClientePFModel): O objeto modelo (ClientePFModel)
                                     completo, pronto para ser salvo.

    Returns:
        ClientePFModel: O objeto do cliente recém-criado, atualizado
                        com os dados do banco (como o ID).
    """
    # Adiciona o objeto principal e seus filhos (em cascata) à sessão
    db.add(new_client)

    # Envia as instruções SQL para o banco para gerar o ID e chaves estrangeiras
    db.flush()

    # Atualiza a instância 'new_client' com os dados do banco (incluindo o ID)
    db.refresh(new_client)

    # Retorna o objeto persistido e atualizado
    return new_client

def create_client_pj(db: Session, new_client: ClientePJModel) -> ClientePJModel:
    """
    Adiciona um novo cliente polimórfico (ClientePJ) ao banco de dados.
    
    Args:
        db (Session): A sessão do banco de dados.
        new_client (ClientePJModel): O objeto modelo (ClientePJModel)
                                     completo, pronto para ser salvo.
    
    Returns:
        ClientePJModel: O objeto do cliente recém-criado, atualizado
                        com os dados do banco (como o ID).
    """
    # Adiciona o objeto principal e seus filhos (em cascata) à sessão
    db.add(new_client)

    # Envia as instruções SQL para o banco para gerar o ID e chaves estrangeiras
    db.flush()

    # Atualiza a instância 'new_client' com os dados do banco (incluindo o ID)
    db.refresh(new_client)

    # Retorna o objeto persistido e atualizado
    return new_client

def update_client_in_db(db: Session, update_client: ClienteModel) -> ClienteModel:
    """
    Persiste as alterações feitas em um objeto Cliente na sessão.
    (Usado pela camada de serviço após a modificação dos dados).

    Args:
        db (Session): A sessão do banco de dados.
        update_client (ClienteModel): O objeto Cliente modificado.

    Returns:
        ClienteModel: O objeto Cliente atualizado do banco.
    """
    # Envia os UPDATEs para o DB (mas não comita)
    db.flush()
    # Atualiza o objeto Python com dados do DB (ex: triggers)
    db.refresh(update_client)
    return update_client

def delete_client_by_id(db: Session, delete_cliet: ClienteModel) -> None:
    """
    Marca um cliente para exclusão na sessão do banco de dados.

    Args:
        db (Session): A sessão do banco de dados.
        delete_cliet (ClienteModel): O objeto a ser deletado.
    """
    # Marca o objeto para ser deletado
    db.delete(delete_cliet)
    # Envia o comando DELETE para o banco (mas não comita)
    db.flush()