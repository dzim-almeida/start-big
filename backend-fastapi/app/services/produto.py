# ---------------------------------------------------------------------------
# ARQUIVO: services/produto.py
# DESCRIÇÃO: Camada de serviço com a lógica de negócio para Produtos,
#            incluindo a criação, busca, atualização e deleção
#            de Produtos e seus Estoques associados.
# ---------------------------------------------------------------------------

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Sequence, List, Optional # Adicionado Optional

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
    """
    
    # 1. REGRA DE NEGÓCIO: Valida se o código do produto já existe
    existing_product = product_crud.get_product_by_code(db, product_to_add.codigo_produto)
    
    if existing_product:
        # Lança um erro de conflito se o código for duplicado
        if not existing_product.ativo:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Produto desabilitado com este Código. Por favor, reative o cadastro."
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail= {
                "campo": "codigo_produto",
                "mensagem": "Código de produto já cadastrado"
            }
        )
    
    # 2. MAPEAMENTO: Cria a instância do modelo SQLAlchemy 'ProdutoModel'
    new_product_to_db = ProdutoModel(
        nome=product_to_add.nome,
        codigo_produto=product_to_add.codigo_produto,
        unidade_medida=product_to_add.unidade_medida,
        observacao=product_to_add.observacao,
        nota_fiscal=product_to_add.nota_fiscal,
        categoria=product_to_add.categoria,
        marca=product_to_add.marca,
        fornecedor_id=product_to_add.fornecedor_id
    )

    # 3. MAPEAMENTO e CONEXÃO (GRAPH): Estoque
    new_product_storage = product_to_add.estoque

    new_storage_for_product = EstoqueModel(
        quantidade=new_product_storage.quantidade,
        quantidade_ideal=new_product_storage.quantidade_ideal,
        quantidade_minima=new_product_storage.quantidade_minima,
        valor_entrada=new_product_storage.valor_entrada,
        valor_varejo=new_product_storage.valor_varejo,
        valor_atacado=new_product_storage.valor_atacado
    )

    new_product_to_db.estoque = new_storage_for_product

    # 4. PERSISTÊNCIA
    return product_crud.create_product(db, new_product_to_db)

# =========================
# Serviço: Buscar TODOS os Produtos
# =========================
def get_all_products(db: Session) -> Sequence[ProdutoModel]:
    """
    Busca TODOS os produtos cadastrados. (Apenas delega para o CRUD).
    """
    return product_crud.get_all_products(db)

# =========================
# Serviço: Buscar Produtos
# =========================
def get_product_by_search(db: Session, search_product: str) -> Sequence[ProdutoModel]: # Corrigido: Usando Sequence
    """
    Busca produtos usando a camada CRUD.
    """
    return product_crud.get_product_by_search(db, search_product)

# =========================
# Serviço: Atualizar Produto
# =========================
def update_product_by_id(db: Session, id: int, product: ProdutoUpdate) -> ProdutoModel:
    """
    Atualiza um produto existente e/ou seu estoque associado pelo ID.
    """
    
    # 1. Busca o produto
    product_to_update = product_crud.get_product_by_id(db, id)
    
    if not product_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )
    
    # 2. Extrai dados para atualização parcial
    update_product_data = product.model_dump(exclude_unset=True)

    # 3. Lógica de atualização aninhada para 'estoque'
    if "estoque" in update_product_data and update_product_data["estoque"] is not None:
        
        # Extrai os dados aninhados de estoque (do schema Pydantic 'product')
        # Correção: O product_to_update.estoque já existe.
        update_storage_data = product.estoque.model_dump(exclude_unset=True)
        
        # Itera sobre os dados do estoque e aplica ao objeto ORM
        for key, value in update_storage_data.items():
            # Aplica a atualização no objeto SQLAlchemy 'product_to_update.estoque'
            setattr(product_to_update.estoque, key, value)
        
        # Remove 'estoque' do dict principal para não tentar atualizar o atributo de relacionamento
        del update_product_data["estoque"]

    # 4. Itera sobre os dados restantes (nível Produto) e aplica
    # Correção: Este loop agora é executado independentemente do loop de 'estoque'.
    for key, value in update_product_data.items():
        setattr(product_to_update, key, value)

    # 5. Chama o CRUD para persistir as alterações
    return product_crud.update_product(db, product_to_update)
    
# =========================
# Serviço: Ativar Produto
# =========================
def active_product_by_id(db: Session, product_id: int, product_code: Optional[str]) -> ProdutoModel: # Corrigido retorno e tipagem
    """
    Serviço para ativar um produto pelo seu ID, opcionalmente redefinindo o código.
    """
    # 1. Busca o produto
    existing_product = product_crud.get_product_by_id(db, product_id)

    if not existing_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")
    
    # 2. Regras de negócio para o código
    if existing_product.codigo_produto is None and product_code is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código do produto é necessário para ativação, pois o campo está vazio."
        )
    elif existing_product.codigo_produto and product_code:
        # Se o produto JÁ tem código, e um NOVO código foi enviado na query, verifica conflito
        if existing_product.codigo_produto != product_code and product_crud.get_product_by_code(db, product_code):
             raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="O novo Código de produto fornecido já está em uso por outro produto ativo."
            )
        # Se for o mesmo código, ignora a atualização. Se for diferente e não tem conflito, aplica.
    
    # 3. Aplica modificações no objeto
    existing_product.ativo = True
    
    if product_code:
        existing_product.codigo_produto = product_code

    # 4. Delega a ativação para o CRUD e retorna o objeto
    return product_crud.active_product_by_id(db, existing_product)

# =========================
# Serviço: Desativar produto
# =========================
def disable_product_by_id(db: Session, product_id: int, delete_product_code: bool) -> ProdutoModel: # Corrigido retorno
    """
    Serviço para desativar um produto pelo seu ID (Soft Delete).
    """
    # 1. Busca o produto
    existing_product = product_crud.get_product_by_id(db, product_id)

    if not existing_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")
    
    # 2. Aplica modificações no objeto
    existing_product.ativo = False

    if delete_product_code:
        existing_product.codigo_produto = None # Atribui None se a flag for True

    # 3. Delega a desativação para o CRUD e retorna o objeto
    return product_crud.disable_product_by_id(db, existing_product)