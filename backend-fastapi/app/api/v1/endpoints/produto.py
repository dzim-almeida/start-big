# ---------------------------------------------------------------------------
# ARQUIVO: endpoints/produto.py
# DESCRIÇÃO: Define os endpoints (rotas) da API para operações CRUD
#            relacionadas a Produtos (Criar, Buscar, Atualizar, Deletar).
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, status, HTTPException, Query, Path
from sqlalchemy.orm import Session

# Importa os schemas Pydantic de entrada (Create/Update) e saída (Read)
from app.schemas.produto import ProdutoCreate, ProdutoRead, ProdutoUpdate

# Importa as dependências de autenticação e sessão
from app.core.depends import get_token
from app.db.session import get_db
# Importa a camada de serviço que contém a lógica de negócio
from app.services import produto as product_service

# Cria um roteador específico para este módulo
router = APIRouter()

# =========================
# Endpoint: Criar Produto
# =========================
@router.post(
    "/",
    response_model=ProdutoRead, # Define o schema da resposta (provavelmente aninhado)
    status_code=status.HTTP_201_CREATED, # Define o status code de sucesso
    summary="Cria novos produtos" # Descrição para documentação
)
def create_product(
    product: ProdutoCreate, # Valida o corpo da requisição com o schema
    token: dict = Depends(get_token), # Garante autenticação
    db: Session = Depends(get_db) # Injeta a sessão do banco
):
    """
    Endpoint para criar um novo Produto e seu registro de Estoque associado.

    Recebe um payload aninhado (Produto + Estoque) e gerencia
    a transação do banco de dados (commit/rollback).
    """
    try:
        # 1. TENTA EXECUTAR A LÓGICA DE NEGÓCIO
        # Delega a criação (Produto + Estoque) para a camada de serviço
        new_product = product_service.create_product_service(db, product)

        # 2. CAMINHO FELIZ: Se o serviço foi concluído sem erros,
        #    salva permanentemente o Produto e o Estoque no banco.
        db.commit()

        # 3. Retorna o novo produto criado
        return new_product

    except HTTPException as http_exec:
        # 4A. CAMINHO TRISTE (Erro de Negócio):
        # Captura erros de negócio (ex: 409 Conflict, código duplicado)
        print(f"Erro de negócio: {http_exec.detail}")
        db.rollback()  # Desfaz a transação
        raise http_exec  # Relança o erro HTTP para o cliente

    except Exception as e:
        # 4B. CAMINHO TRISTE (Erro Inesperado):
        # Captura qualquer outro erro
        print(f"Erro inesperado ao criar produto: {e}")
        db.rollback()  # Desfaz a transação
        raise HTTPException( # Retorna um erro 500 genérico
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro interno no servidor."
        )
    
# =========================
# Endpoint: Buscar Produtos
# =========================
@router.get(
    "/",
    response_model=list[ProdutoRead], # A resposta é uma lista de produtos
    status_code=status.HTTP_200_OK,
    summary="Buscar produtos por nome ou codigo"
)
def get_product_by_search(
    # Define 'buscar' como um parâmetro de query (ex: /produtos/?buscar=...)
    buscar: str = Query(
        ..., # Indica que o parâmetro é obrigatório
        min_length=1,
        max_length=255,
        description="Entrada deve ser nome ou codigo do produto"
    ),
    token: dict = Depends(get_token), # Garante autenticação
    db: Session = Depends(get_db) # Injeta a sessão do banco
):
    """
    Endpoint para buscar produtos pelo nome ou código.
    Retorna uma lista de produtos ou uma lista vazia.
    """
    # Delega a lógica de busca para o serviço
    products = product_service.get_product_by_search(db, buscar)
    # Retorna a lista de resultados
    return products

# =========================
# Endpoint: Atualizar Produto (PUT)
# =========================
@router.put(
    "/{id}", # Recebe o ID do produto na URL
    response_model=ProdutoRead, # Retorna o produto atualizado
    status_code=status.HTTP_200_OK,
    summary="Edita um produto existente atraves do ID"
)
def put_product_by_id(
    # Extrai o ID da URL, valida se é um inteiro >= 1
    id: int = Path(
        ...,
        description="ID do produto a ser editado",
        ge=1
    ),
    *, # Força os parâmetros seguintes a serem nomeados (keyword-only)
    
    # Valida o corpo da requisição (JSON) com o schema de atualização
    edit_product: ProdutoUpdate,
    
    token: dict = Depends(get_token), # Garante autenticação
    db: Session = Depends(get_db) # Injeta a sessão do banco
):
    """
    Endpoint para atualizar um produto existente (e/ou seu estoque) pelo ID.
    Gerencia a transação (commit/rollback).
    """
    try:
        # Delega a lógica de atualização para o serviço
        edited_product = product_service.update_product_by_id(db, id, edit_product)
        
        # Comita a transação se o serviço foi bem-sucedido
        db.commit()
        
        # Retorna o produto atualizado
        return(edited_product)

    except HTTPException as http_exec:
        # Captura erros de negócio (ex: 404 Not Found)
        print(f"Erro de negocio: {http_exec.detail}")
        # NOTA DE FORMATAÇÃO: db.rollback() está faltando parênteses
        db.rollback
        raise http_exec

    except Exception as e:
        # Captura erros inesperados
        print(f"Erro inesperado ao criar produto: {e}") # Nota: Mensagem de erro copiada (deveria ser 'atualizar')
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro interno no servidor."
        )
    
# =========================
# Endpoint: Deletar Produto (DELETE)
# =========================
@router.delete(
    "/{id}",
    status_code=status.HTTP_200_OK,
    summary="Exclui um produto pelo id"
)
def delete_product_by_id(
    # Extrai o ID da URL, valida se é um inteiro >= 1
    id: int = Path(
        ...,
        description="ID do produto a ser excluido",
        ge=1
    ),
    token: dict = Depends(get_token), # Garante autenticação
    db: Session = Depends(get_db) # Injeta a sessão do banco
):
    """
    Endpoint para deletar um produto existente pelo seu ID.
    Gerencia a transação (commit/rollback).
    """
    try:
        # Delega a lógica de deleção para o serviço
        product_service.delete_product_by_id(db, id)
        
        # Comita a transação se o serviço foi bem-sucedido
        db.commit()
        
        # Retorna uma mensagem de sucesso
        return {"response": "Produto excluído com sucesso!"}

    except HTTPException as http_exec:
        # Captura erros de negócio (ex: 404 Not Found)
        print(f"Erro de negocio: {http_exec.detail}")
        db.rollback()  # Desfaz a transação
        raise http_exec  # Relança o erro HTTP

    except Exception as e:
        # Captura erros inesperados
        print(f"Erro inesperado ao excluir produto: {e}")
        db.rollback()  # Desfaz a transação
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro interno no servidor."
        )