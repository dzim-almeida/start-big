# ---------------------------------------------------------------------------
# ARQUIVO: cliente.py (CRUD)
# DESCRIÇÃO: Este módulo contém as funções de CRUD (Create, Read, Update,
#            Delete) para interagir com os modelos de Cliente no banco de dados.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session

from app.db.models.cliente import ClientePF as ClientePFModel, ClientePJ as ClientePJModel


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