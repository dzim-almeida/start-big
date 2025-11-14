# ---------------------------------------------------------------------------
# ARQUIVO: crud/produto.py
# DESCRIÇÃO: Funções de CRUD (Create, Read, Update, Delete) para interagir
#            com a tabela de Produtos no banco de dados (Repository Layer).
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from sqlalchemy import select, or_, and_
from typing import Sequence, Optional # Adicionado Optional para clareza

from app.db.models.produto import Produto as ProdutoModel

# =========================
# Funções de Leitura (Read)
# =========================

def get_product_by_search(db: Session, search_product: str) -> Sequence[ProdutoModel]:
    """
    Busca produtos ativos cujo nome ou código do produto comece com o termo de pesquisa.

    Args:
        db (Session): A sessão do banco de dados.
        search_product (str): O termo a ser buscado.

    Returns:
        Sequence[ProdutoModel]: Uma sequência de objetos ProdutoModel encontrados.
    """
    # Define as condições de busca (OR) para nome ou código
    conditions = or_(
        # Usando .ilike com '%' para pesquisa case-insensitive que começa com o termo
        ProdutoModel.nome.ilike(f"{search_product}%"),
        ProdutoModel.codigo_produto.startswith(search_product)
    )

    # Constrói a query de seleção com o filtro AND para garantir que esteja ativo E corresponda à busca
    stmt = select(ProdutoModel).where(
        and_(
            ProdutoModel.ativo == True,
            conditions
        )
    )
    
    # Executa a query e retorna todos os resultados
    products = db.scalars(stmt).all()

    return products


def get_product_by_id(db: Session, product_id: int) -> ProdutoModel | None: # Corrigido: Inclui '| None'
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

def get_all_products(db: Session) -> Sequence[ProdutoModel]:
    """
    Busca TODOS os produtos ativos cadastrados no banco de dados.

    Args:
        db (Session): A sessão do banco de dados.

    Returns:
        Sequence[ProdutoModel]: Uma lista (sequência) de todos os produtos ativos.
    """
    # Constrói a query: SELECT * FROM produto WHERE ativo = True
    stmt = select(ProdutoModel).where(ProdutoModel.ativo == True)
    # Executa a query e retorna todos os resultados
    products_in_db = db.scalars(stmt).all()
    return products_in_db


def get_product_by_code(db: Session, product_code: str) -> ProdutoModel | None: # Corrigido: Inclui '| None'
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


# =========================
# Função de Criação (Create)
# =========================

def create_product(db: Session, product_to_add: ProdutoModel) -> ProdutoModel:
    """
    Adiciona um novo produto (e seu estoque associado em cascata)
    ao banco de dados.
    """
    # Adiciona o objeto principal à sessão (o estoque vai junto por 'cascade')
    db.add(product_to_add)
    # Envia os INSERTs para o banco e obtém o ID gerado
    db.flush()
    # Atualiza o objeto Python com os dados do banco (incluindo o ID)
    db.refresh(product_to_add)
    # Retorna o objeto persistido
    return product_to_add


# =========================
# Função de Atualização (Update)
# =========================

def update_product(db: Session, product_to_update: ProdutoModel) -> ProdutoModel:
    """
    Persiste as alterações feitas em um objeto Produto na sessão.
    O objeto já deve estar associado à sessão e ter sido modificado
    pela camada de serviço.
    """
    # O objeto já está rastreado pela sessão. db.flush() envia os UPDATEs detectados.
    db.flush()
    # Recarrega o objeto do banco para garantir que esteja sincronizado (ex: triggers).
    db.refresh(product_to_update)
    # Retorna o objeto atualizado.
    return product_to_update # Retorno formatado para consistência


# =========================
# Funções de Status (Ativar/Desativar)
# =========================

def active_product_by_id(db: Session, active_product: ProdutoModel) -> ProdutoModel: # Corrigido: Deve retornar o objeto atualizado
    """
    Persiste o status de ativação (ativo=True) para o produto na sessão.
    """
    # A modificação (active_product.ativo = True) é feita na camada de serviço.
    db.flush()
    db.refresh(active_product)
    return active_product # Retorna o objeto atualizado

def disable_product_by_id(db: Session, disable_product: ProdutoModel) -> ProdutoModel: # Corrigido: Deve retornar o objeto atualizado
    """
    Persiste o status de desativação (ativo=False) para o produto na sessão (Soft Delete).
    """
    # A modificação (disable_product.ativo = False) é feita na camada de serviço.
    db.flush()
    db.refresh(disable_product)
    return disable_product # Retorna o objeto atualizado