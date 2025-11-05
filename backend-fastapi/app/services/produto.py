# ---------------------------------------------------------------------------
# ARQUIVO: services/produto.py
# DESCRIÇÃO: Camada de serviço com a lógica de negócio para Produtos,
#            incluindo a criação, busca, atualização e deleção
#            de Produtos e seus Estoques associados.
# ---------------------------------------------------------------------------

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Sequence # Importação para type hint de lista

# Importa os schemas Pydantic (Create para entrada, Read para saída)
from app.schemas.produto import ProdutoCreate, ProdutoUpdate
# Importa os modelos ORM (Produto e Estoque)
from app.db.models.produto import Produto as ProdutoModel
from app.db.models.estoque import Estoque as EstoqueModel
# Importa a camada de acesso a dados (CRUD)
from app.db.crud import produto as product_crud

# =========================
# Serviço: Criar Produto
# =========================
def create_product(db: Session, product_to_add: ProdutoCreate) -> ProdutoModel:
    """
    Serviço para criar um novo Produto e seu registro de Estoque associado.

    Recebe um schema 'ProdutoCreate' aninhado, valida os dados,
    cria as instâncias dos modelos 'ProdutoModel' e 'EstoqueModel',
    conecta-os, e os persiste no banco através da camada CRUD.

    Args:
        db (Session): A sessão do banco de dados.
        product_to_add (ProdutoCreate): O schema Pydantic com os dados do
                                     produto e do estoque aninhado.

    Raises:
        HTTPException: 409 (Conflict) se o 'codigo_produto' já existir.

    Returns:
        ProdutoModel: O objeto do produto recém-criado.
    """
    
    # 1. REGRA DE NEGÓCIO: Valida se o código do produto já existe
    existing_product = product_crud.get_product_by_code(db, product_to_add.codigo_produto)
    
    if existing_product:
        # Lança um erro de conflito se o código for duplicado
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Código já cadastrado")
    
    # 2. MAPEAMENTO: Cria a instância do modelo SQLAlchemy 'ProdutoModel'
    new_product_to_db = ProdutoModel(
        nome=product_to_add.nome,
        codigo_produto=product_to_add.codigo_produto,
        unidade_medida=product_to_add.unidade_medida,
        observacao=product_to_add.observacao,
        nota_fiscal=product_to_add.nota_fiscal,
        categoria=product_to_add.categoria,
        marca=product_to_add.marca,
        id_fornecedor=product_to_add.id_fornecedor
    )

    # 3. MAPEAMENTO: Extrai os dados de estoque do schema Pydantic aninhado
    new_product_storage = product_to_add.estoque

    # Cria a instância do modelo SQLAlchemy 'EstoqueModel'
    new_storage_for_product = EstoqueModel(
        quantidade=new_product_storage.quantidade,
        quantidade_ideal=new_product_storage.quantidade_ideal,
        quantidade_minima=new_product_storage.quantidade_minima,
        valor_entrada=new_product_storage.valor_entrada,
        valor_varejo=new_product_storage.valor_varejo,
        valor_atacado=new_product_storage.valor_atacado
    )

    # 4. CONEXÃO (GRAPH): Conecta os dois objetos em memória (relação 1-para-1)
    new_product_to_db.estoque = new_storage_for_product

    # 5. PERSISTÊNCIA: Passa o objeto Produto (que contém o Estoque) para o CRUD
    product_in_db = product_crud.create_product(db, new_product_to_db)

    # 6. RETORNO: Retorna o objeto persistido no banco
    return product_in_db

# =========================
# Serviço: Buscar Produtos
# =========================
def get_product_by_search(db: Session, search_product: str) -> list[ProdutoModel]:
    """
    Busca produtos usando a camada CRUD.
    Retorna a lista de produtos encontrada (pode ser vazia).

    Args:
        db (Session): A sessão do banco de dados.
        search_product (str): O termo a ser buscado.

    Returns:
        list[ProdutoModel]: Uma lista de objetos ProdutoModel.
    """
    # Delega a busca para a função do CRUD
    existing_products = product_crud.get_product_by_search(db, search_product)
    # Retorna a lista de produtos encontrada
    return existing_products

# =========================
# Serviço: Atualizar Produto
# =========================
def update_product_by_id(db: Session, id: int, product: ProdutoUpdate) -> ProdutoModel:
    """
    Atualiza um produto existente e/ou seu estoque associado pelo ID.
    Busca o produto, aplica atualizações parciais (patch) e retorna
    o objeto SQLAlchemy atualizado.
    """
    
    # 1. Busca o produto (e seu estoque, via relationship) pelo ID
    product_to_update = product_crud.get_product_by_id(db, id)
    
    # 2. Verifica se o produto foi encontrado
    if not product_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )
    
    # 3. Extrai apenas os dados enviados na requisição (para atualização parcial)
    update_product_data = product.model_dump(exclude_unset=True)

    # 4. Itera sobre os dados enviados (nível Produto)
    for key, value in update_product_data.items():
        
        # 5. Lógica de atualização aninhada para 'estoque'
        if key == "estoque" and update_product_data["estoque"] is not None:
            
            # Extrai os dados aninhados de estoque (do schema Pydantic 'product')
            update_storage_data = product.estoque.model_dump(exclude_unset=True)
            
            # Itera sobre os dados do estoque
            # (Aviso: 'key' e 'value' aqui sobrescrevem as do loop externo)
            for key, value in update_storage_data.items():
                # Aplica a atualização no objeto SQLAlchemy 'product_to_update.estoque'
                setattr(product_to_update.estoque, key, value)
        
        # (Aviso: Indentação incorreta, este 'else' está ligado ao 'if key == "estoque"')
        else:
            setattr(product_to_update, key, value)

    # 6. Chama o CRUD para persistir as alterações (flush + refresh)
    return product_crud.update_product(db, product_to_update)
    
# =========================
# Serviço: Deletar Produto
# =========================
def delete_product_by_id(db: Session, product_id: int) -> None:
    """
    Serviço para deletar um produto pelo seu ID.

    1. Busca o produto.
    2. Se encontrado, delega a exclusão para o CRUD.
    """
    # 1. Busca o produto existente pelo ID
    existing_product = product_crud.get_product_by_id(db, product_id)
    
    # 2. Verifica se o produto foi encontrado
    if not existing_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )
    
    # 3. Delega a exclusão para a camada CRUD
    return product_crud.delete_product(db, existing_product)