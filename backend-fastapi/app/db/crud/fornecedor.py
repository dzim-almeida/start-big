# ---------------------------------------------------------------------------
# ARQUIVO: crud/fornecedor.py
# DESCRIÇÃO: Funções de CRUD (Create, Read, Update, Delete) para interagir
#            com a tabela de Fornecedores no banco de dados.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from typing import Sequence # Importação sugerida para type hints

from app.db.models.fornecedor import Fornecedor as FornecedorModel

# =========================
# Funções de Leitura (Read)
# =========================

def get_supplier_by_id(db: Session, supplier_id: int) -> FornecedorModel:
    """
    Busca um único fornecedor pelo seu ID (chave primária).

    Args:
        db (Session): A sessão do banco de dados.
        supplier_id (int): O ID do fornecedor a ser pesquisado.

    Returns:
        FornecedorModel | None: O objeto do fornecedor se encontrado,
                                caso contrário None.
    """
    # Constrói a query para buscar pelo ID
    stmt = select(FornecedorModel).where(FornecedorModel.id == supplier_id)
    # Executa e retorna o primeiro resultado (ou None)
    supplier_in_db = db.scalars(stmt).first()
    return supplier_in_db

def get_all_suppliers(db: Session) -> Sequence[FornecedorModel]:
    """
    Busca TODOS os fornecedores cadastrados no banco de dados.

    Args:
        db (Session): A sessão do banco de dados.

    Returns:
        Sequence[FornecedorModel]: Uma lista (sequência) de todos os fornecedores.
    """
    # Constrói a query: SELECT * FROM fornecedor
    stmt = select(FornecedorModel)
    # Executa a query e retorna todos os resultados
    suppliers_in_db = db.scalars(stmt).all()
    return suppliers_in_db

def get_supplier_by_cnpj(db: Session, supplier_cnpj: str) -> FornecedorModel:
    """
    Busca um único fornecedor pelo seu 'cnpj' exato.

    Args:
        db (Session): A sessão do banco de dados.
        supplier_cnpj (str): O CNPJ exato do fornecedor a ser pesquisado.

    Returns:
        FornecedorModel | None: O objeto do fornecedor se encontrado,
                                caso contrário None.
    """
    # Constrói a query para buscar pelo CNPJ
    stmt = select(FornecedorModel).where(FornecedorModel.cnpj == supplier_cnpj)
    # Executa e retorna o primeiro resultado (ou None)
    supplier_in_db = db.scalars(stmt).first()
    return supplier_in_db


# (Nota: A anotação de retorno '-> FornecedorModel' está inconsistente com
#  a implementação '.all()', que retorna uma lista/sequência)
def get_supplier_by_search(db: Session, supplier_search: str) -> Sequence[FornecedorModel]:
    """
    Busca fornecedores cujo nome, nome fantasia ou CNPJ comece
    com o termo de pesquisa.

    Args:
        db (Session): A sessão do banco de dados.
        supplier_search (str): O termo a ser buscado.

    Returns:
        (list[FornecedorModel]): Uma lista de objetos FornecedorModel encontrados.
                                 (O type hint original é 'FornecedorModel')
    """
    # Define as condições de busca (OR)
    conditions = or_(
        FornecedorModel.nome.startswith(supplier_search),
        FornecedorModel.nome_fantasia.startswith(supplier_search),
        FornecedorModel.cnpj.startswith(supplier_search)
    )

    # Constrói a query de seleção com o filtro
    stmt = select(FornecedorModel).where(conditions)
    # Executa a query e retorna todos os resultados
    suppliers_in_db = db.scalars(stmt).all()
    return suppliers_in_db

# =========================
# Função de Criação (Create)
# =========================

def create_supplier(db: Session, supplier_to_add: FornecedorModel) -> FornecedorModel:
    """
    Adiciona um novo fornecedor (e seus endereços associados em cascata)
    ao banco de dados.

    Args:
        db (Session): A sessão do banco de dados.
        supplier_to_add (FornecedorModel): O objeto modelo completo para salvar.

    Returns:
        FornecedorModel: O objeto do fornecedor recém-criado e atualizado.
    """
    # Adiciona o objeto principal à sessão (endereços vão junto por 'cascade')
    db.add(supplier_to_add)
    # Envia os INSERTs para o banco e obtém o ID gerado
    db.flush()
    # Atualiza o objeto Python com os dados do banco (incluindo o ID)
    db.refresh(supplier_to_add)
    # Retorna o objeto persistido
    return supplier_to_add

# =========================
# Função de Atualização (Update)
# =========================

def update_supplier(db: Session, supplier_to_update: FornecedorModel) -> FornecedorModel:
    """
    Persiste as alterações feitas em um objeto Fornecedor na sessão.
    O objeto já deve estar associado à sessão e ter sido modificado
    pela camada de serviço.

    Args:
        db (Session): A sessão do banco de dados.
        supplier_to_update (FornecedorModel): O objeto Fornecedor modificado.

    Returns:
        FornecedorModel: O objeto Fornecedor atualizado do banco.
    """
    # Nota: db.add() não é necessário; o objeto já está na sessão.
    # O flush() enviará os UPDATEs para as alterações detectadas.
    db.flush()
    # Recarrega o objeto do banco para garantir que esteja sincronizado.
    db.refresh(supplier_to_update)
    # Retorna o objeto atualizado.
    return supplier_to_update

# =========================
# Função de Deleção (Delete)
# =========================

def delete_supplier(db: Session, supplier_to_delete: FornecedorModel) -> None:
    """
    Marca um fornecedor para exclusão na sessão do banco de dados.
    A exclusão efetiva ocorrerá no commit da transação
    realizado pela camada de endpoint.

    Args:
        db (Session): A sessão do banco de dados.
        supplier_to_delete (FornecedorModel): O objeto a ser deletado.
    """
    # Marca o objeto para ser deletado
    db.delete(supplier_to_delete)
    # Envia o comando DELETE para o banco (mas não comita)
    db.flush()