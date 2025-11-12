# ---------------------------------------------------------------------------
# ARQUIVO: endpoints/produto.py
# DESCRIÇÃO: Define os endpoints (rotas) da API para operações CRUD
#            relacionadas a Produtos (Criar, Buscar, Atualizar, Deletar),
#            incluindo uploads de fotos.
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, status, HTTPException, Query, Path, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Sequence, Optional

# Importa os schemas Pydantic de entrada (Create/Update) e saída (Read)
from app.schemas.produto import ProdutoCreate, ProdutoRead, ProdutoUpdate
from app.schemas.produto_fotos import ProdutoFotoRead

# Importa as dependências de autenticação e sessão
from app.core.depends import get_token
from app.db.session import get_db
# Importa a camada de serviço que contém a lógica de negócio
from app.services import produto as product_service
from app.services import produto_fotos as product_image_service

# Cria um roteador específico para este módulo
router = APIRouter()

# =========================
# Endpoint: Criar Produto (POST)
# =========================
@router.post(
    "/",
    response_model=ProdutoRead, # Define o schema da resposta (geralmente incluindo o estoque)
    status_code=status.HTTP_201_CREATED, # Define o status code de sucesso
    summary="Cria novos produtos"
)
def create_product(
    product: ProdutoCreate, # Valida o corpo da requisição com o schema Pydantic
    token: dict = Depends(get_token), # Garante autenticação via token
    db: Session = Depends(get_db) # Injeta a sessão do banco de dados
):
    """
    Endpoint para criar um novo Produto e seu registro de Estoque associado.

    Recebe um payload aninhado (Produto + Estoque) e gerencia
    a transação do banco de dados (commit/rollback).
    """
    try:
        # 1. TENTA EXECUTAR A LÓGICA DE NEGÓCIO
        # Delega a criação (Produto + Estoque) para a camada de serviço
        new_product = product_service.create_product(db, product)

        # 2. CAMINHO FELIZ: Se o serviço foi concluído sem erros,
        #    salva permanentemente o Produto e o Estoque no banco.
        db.commit()

        # 3. Retorna o novo produto criado (com o status 201)
        return new_product

    except HTTPException as http_exce:
        # 4A. CAMINHO TRISTE (Erro de Negócio):
        # Captura erros de negócio (ex: 409 Conflict, código duplicado)
        print(f"Erro de negócio: {http_exce.detail}")
        db.rollback()  # Desfaz a transação para restaurar o estado anterior
        raise http_exce  # Relança o erro HTTP para o cliente

    except Exception as e:
        # 4B. CAMINHO TRISTE (Erro Inesperado):
        # Captura qualquer outro erro que não seja HTTPException
        print(f"Erro inesperado ao criar produto: {e}")
        db.rollback()  # Desfaz a transação
        raise HTTPException( # Retorna um erro 500 genérico
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro interno no servidor."
        )
    
# =========================
# Endpoint: Buscar TODOS os Produtos (GET /a)
# =========================
@router.get(
    "/a",
    response_model=Sequence[ProdutoRead], # A resposta é uma lista (Sequence) de produtos
    status_code=status.HTTP_200_OK,
    summary="Retorna todos os produtos cadastrados"
)
def get_all_products(
    token: dict = Depends(get_token), # Garante autenticação
    db: Session = Depends(get_db) # Injeta a sessão do banco
):
    """
    Endpoint para buscar TODOS os produtos cadastrados no sistema.
    (Nota: Rota de utilidade, idealmente deve ter paginação para produção)
    """
    # Delega a busca para a camada de serviço
    products_in_db = product_service.get_all_products(db)
    # Retorna a lista de produtos
    return products_in_db

# =========================
# Endpoint: Buscar Produtos (Search GET /)
# =========================
@router.get(
    "/",
    response_model=list[ProdutoRead], # A resposta é uma lista de produtos
    status_code=status.HTTP_200_OK,
    summary="Buscar produtos por nome ou código"
)
def get_product_by_search(
    # Define 'buscar' como um parâmetro de query (ex: /produtos/?buscar=...)
    buscar: str = Query(
        ..., # Indica que o parâmetro é obrigatório
        min_length=1,
        max_length=255,
        description="Entrada deve ser nome ou código do produto"
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
    summary="Edita um produto existente através do ID"
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
        return edited_product # Removido parênteses desnecessários do return

    except HTTPException as http_exce:
        # Captura erros de negócio (ex: 404 Not Found)
        print(f"Erro de negócio: {http_exce.detail}")
        db.rollback() # Desfaz a transação
        raise http_exce

    except Exception as e:
        # Captura erros inesperados
        print(f"Erro inesperado ao atualizar produto: {e}")
        db.rollback() # Desfaz a transação
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro interno no servidor."
        )
    
# =========================
# Endpoint: Deletar Produto (DELETE)
# =========================
@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT, # Define o status de sucesso (sem conteúdo de resposta)
    summary="Exclui um produto pelo id"
)
def delete_product_by_id(
    # Extrai o ID da URL, valida se é um inteiro >= 1
    id: int = Path(
        ...,
        description="ID do produto a ser excluído",
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

    except HTTPException as http_exce:
        # Captura erros de negócio (ex: 404 Not Found)
        print(f"Erro de negócio: {http_exce.detail}")
        db.rollback()  # Desfaz a transação
        raise http_exce  # Relança o erro HTTP

    except Exception as e:
        # Captura erros inesperados
        print(f"Erro inesperado ao excluir produto: {e}")
        db.rollback()  # Desfaz a transação
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro interno no servidor."
        )
    
# =========================
# Endpoint: Upload de Foto (POST /fotos)
# =========================
@router.post(
    "/{product_id}/fotos",
    response_model=ProdutoFotoRead, # Retorna os metadados da foto recém-criada
    status_code=status.HTTP_201_CREATED,
    summary="Cria imagens para o produto."
)
def upload_product_image(
    # Extrai o ID do produto da URL (Path Parameter)
    product_id: int = Path(
        ...,
        description="ID do produto a receber a foto."
    ),
    # Recebe o arquivo binário (UploadFile) do corpo da requisição (multipart/form-data)
    file: UploadFile = File(
        ...,
        description="O arquivo de imagem a ser carregado."
    ),
    # Recebe o campo 'principal' do corpo da requisição (Form/multipart)
    principal: bool = Form(
        False,
        description="Define se esta é a foto principal do produto."
    ),
    # Injeta a dependência de autenticação
    token: dict = Depends(get_token),
    # Injeta a dependência da sessão do banco de dados
    db: Session = Depends(get_db)
):
    """
    Endpoint para realizar o upload de uma foto, associando-a a um produto existente.
    A requisição deve ser enviada no formato multipart/form-data.
    Gerencia a transação (commit/rollback).
    """
    try:
        # 1. TENTA EXECUTAR A LÓGICA DE NEGÓCIO
        # Delega a lógica de upload e registro dos metadados da foto
        # para a camada de serviço (product_image_service)
        new_image_metadata = product_image_service.create_product_image(
            db, product_id, file, principal
        )
        
        # 2. Comita a transação (salvando o registro no BD)
        db.commit()
        
        # 3. Retorna os metadados persistidos
        return new_image_metadata

    except HTTPException as http_exce:
        # Erros de negócio (404, 400, etc.)
        db.rollback() # Desfaz o registro, caso tenha sido criado antes do erro
        raise http_exce
    
    except Exception as e:
        # Erros inesperados (500)
        print(f"Erro inesperado ao processar upload: {e}")
        db.rollback() # Desfaz a transação
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao processar upload: {e}"
        )
    
# =========================
# Endpoint: Deletar Foto Específica (DELETE /fotos/{image_id})
# =========================
@router.delete(
    "/fotos/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deleta uma imagem específica do produto."
)
def delete_product_image(
    # Extrai o ID da imagem da URL (Path Parameter)
    image_id: int = Path(
        ...,
        description="ID único da imagem a ser deletada",
    ),
    token: dict = Depends(get_token), # Garante autenticação
    db: Session = Depends(get_db) # Injeta a sessão do banco
):
    """
    Endpoint para deletar uma foto específica do produto pelo seu ID.
    Implementa o tratamento de rollback para garantir a integridade da transação.
    """
    try:
        # 1. TENTA EXECUTAR A LÓGICA DE NEGÓCIO
        # Delega a lógica de deleção (que deve incluir a exclusão do arquivo físico)
        product_image_service.delete_product_image(db, image_id)
        
        # 2. CAMINHO FELIZ: Comita a transação
        db.commit()

    except HTTPException as http_exce:
        # 3A. CAMINHO TRISTE (Erro de Negócio):
        # Captura erros de negócio (ex: 404 Not Found da imagem)
        print(f"Erro de negócio: {http_exce.detail}")
        db.rollback()  # Desfaz a transação
        raise http_exce

    except Exception as e:
        # 3B. CAMINHO TRISTE (Erro Inesperado):
        # Captura qualquer outro erro (ex: falha de I/O ao deletar o arquivo)
        print(f"Erro inesperado ao excluir foto: {e}")
        db.rollback()  # Desfaz a transação
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro interno no servidor ao tentar excluir a foto."
        )