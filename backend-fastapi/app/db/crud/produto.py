# ---------------------------------------------------------------------------
# ARQUIVO: crud/produto.py
# DESCRIÇÃO: Funções de CRUD (Create, Read, Update, Delete) para interagir
#            com a tabela de Produtos no banco de dados.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from typing import Sequence # Importado para type hint

from app.db.models.produto import Produto as ProdutoModel

# (Nota: A anotação de retorno '-> ProdutoModel' está inconsistente com
#  a implementação '.all()', que retorna uma lista/sequência)
def get_product_by_search(db: Session, search_product: str) -> ProdutoModel:
    """
    Busca produtos cujo nome ou código do produto comece com o termo de pesquisa.

    Args:
        db (Session): A sessão do banco de dados.
        search_product (str): O termo a ser buscado.

    Returns:
        (list[ProdutoModel]): Uma lista de objetos ProdutoModel encontrados.
                             (O type hint original é 'ProdutoModel')
    """
    # Define as condições de busca (OR) para nome ou código
    conditions = or_(
        ProdutoModel.nome.startswith(search_product),
        ProdutoModel.codigo_produto.startswith(search_product)
    )

    # Constrói a query de seleção com o filtro
    stmt = select(ProdutoModel).where(conditions)
    
    # Executa a query e retorna todos os resultados
    products = db.scalars(stmt).all()

    return products


def get_product_by_id(db: Session, product_id: int) -> ProdutoModel:
    """
    Busca um único produto pelo seu ID (chave primária).

    Args:
        db (Session): A sessão do banco de dados.
        product_id (int): O ID do produto a ser pesquisado.

    Returns:
        ProdutoModel | None: O objeto do produto se encontrado, caso contrário None.
    """
    # Constrói a query para buscar pelo ID
    stmt = select(ProdutoModel).where(ProdutoModel.id == product_id)
    # Executa e retorna o primeiro resultado (ou None)
    product = db.scalars(stmt).first()
    return product


def get_product_by_code(db: Session, product_code: str) -> ProdutoModel:
    """
    Busca um único produto pelo seu 'codigo_produto' exato.

    Args:
        db (Session): A sessão do banco de dados.
        product_code (str): O código exato do produto a ser pesquisado.

    Returns:
        ProdutoModel | None: O objeto do produto se encontrado, caso contrário None.
    """
    # Constrói a query para buscar pelo código do produto
    stmt = select(ProdutoModel).where(ProdutoModel.codigo_produto == product_code)
    # Executa e retorna o primeiro resultado (ou None)
    product_in_db = db.scalars(stmt).first()
    return product_in_db


def create_product(db: Session, product_to_add: ProdutoModel) -> ProdutoModel:
    """
    Adiciona um novo produto (e seu estoque associado em cascata)
    ao banco de dados.

    Args:
        db (Session): A sessão do banco de dados.
        product_to_add (ProdutoModel): O objeto modelo completo para salvar.

    Returns:
        ProdutoModel: O objeto do produto recém-criado e atualizado.
    """
    # Adiciona o objeto principal à sessão (o estoque vai junto por 'cascade')
    db.add(product_to_add)
    # Envia os INSERTs para o banco e obtém o ID gerado
    db.flush()
    # Atualiza o objeto Python com os dados do banco (incluindo o ID)
    db.refresh(product_to_add)
    # Retorna o objeto persistido
    return product_to_add


def update_product(db: Session, product_to_update: ProdutoModel) -> ProdutoModel:
    """
    Persiste as alterações feitas em um objeto Produto na sessão.
    O objeto já deve estar associado à sessão e ter sido modificado
    pela camada de serviço.

    Args:
        db (Session): A sessão do banco de dados.
        product_to_update (ProdutoModel): O objeto Produto modificado.

    Returns:
        ProdutoModel: O objeto Produto atualizado do banco.
    """
    # Nota: db.add() não é necessário; o objeto já está na sessão.
    # O flush() enviará os UPDATEs para as alterações detectadas.
    db.flush()
    # Recarrega o objeto do banco para garantir que esteja sincronizado.
    db.refresh(product_to_update)
    # Retorna o objeto atualizado.
    return(product_to_update)


def delete_product(db: Session, product_to_delete: ProdutoModel) -> None:
    """
    Marca um produto para exclusão na sessão do banco de dados.
    A exclusão efetiva ocorrerá no commit da transação
    realizado pela camada de endpoint.

    Args:
        db (Session): A sessão do banco de dados.
        product_to_delete (ProdutoModel): O objeto a ser deletado.
    """
    # Marca o objeto para ser deletado
    db.delete(product_to_delete)
    # Envia o comando DELETE para o banco (mas não comita)
    db.flush()