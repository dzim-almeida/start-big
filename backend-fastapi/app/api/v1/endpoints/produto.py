# ---------------------------------------------------------------------------
# ARQUIVO: endpoints/produto.py
# DESCRIÇÃO: Define os endpoints (rotas) da API para operações CRUD
#            relacionadas a Produtos (Criar, Buscar, Atualizar, Deletar),
#            incluindo uploads de fotos.
#            Rotas: /produtos, /produtos/{id}, /produtos/{id}/fotos, etc.
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, status, HTTPException, Query, Path, UploadFile, File, Form, Response
from sqlalchemy.orm import Session
from typing import Sequence, List, Optional

# Importa os schemas Pydantic de entrada (Create/Update) e saída (Read)
from app.schemas.produto import ProdutoCreate, ProdutoRead, ProdutoUpdate
from app.schemas.produto_fotos import ProdutoFotoRead

# Importa as dependências de autenticação e sessão (Injeção de Dependência)
from app.core.depends import get_token, _handle_db_transaction
from app.db.session import get_db
# Importa a camada de serviço que contém a lógica de negócio
from app.services import produto as product_service
from app.services import produto_fotos as product_image_service

# Cria um roteador específico. Assume que a URL base é /produtos
router = APIRouter()

# =========================
# Endpoint: Criar Produto (POST)
# Rota: POST /produtos
# =========================
@router.post(
    "/",
    response_model=ProdutoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo produto e associa um registro de estoque"
)
def create_product(
    product: ProdutoCreate,
    token: dict = Depends(get_token), # Injeção de dependência: Autenticação
    db: Session = Depends(get_db) # Injeção de dependência: Sessão de BD
):
    """
    Cria um novo Produto, incluindo seu registro de Estoque inicial.
    Utiliza a função auxiliar para gerenciar a transação.
    """
    return _handle_db_transaction(
        db,
        product_service.create_product,
        product
    )
    
# =========================
# Endpoint: Buscar TODOS os Produtos (Sem Paginação)
# Rota: GET /produtos/all
# =========================
@router.get(
    "/all", # Padrão mais legível que '/a'
    response_model=Sequence[ProdutoRead],
    status_code=status.HTTP_200_OK,
    summary="Retorna todos os produtos cadastrados (rota de utilidade)"
)
def get_all_products(
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Busca e retorna a lista completa de produtos.
    """
    # A busca (READ) não requer transação/commit/rollback
    return product_service.get_all_products(db)

# =========================
# Endpoint: Buscar Produtos (Search)
# Rota: GET /produtos/
# =========================
@router.get(
    "/",
    response_model=List[ProdutoRead],
    status_code=status.HTTP_200_OK,
    summary="Buscar produtos por nome ou código"
)
def get_product_by_search(
    # Uso de Query(...) com '...' (obrigatório) e metadados de documentação
    buscar: str = Query(
        ...,
        min_length=1,
        max_length=255,
        description="Entrada deve ser nome ou código do produto."
    ),
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Busca produtos pelo nome ou código.
    Retorna uma lista de produtos ou uma lista vazia.
    """
    # A busca (READ) não requer transação/commit/rollback
    return product_service.get_product_by_search(db, buscar)

# =========================
# Endpoint: Atualizar Produto (PUT)
# Rota: PUT /produtos/{id}
# =========================
@router.put(
    "/{id}",
    response_model=ProdutoRead,
    status_code=status.HTTP_200_OK,
    summary="Atualiza um produto e/ou seu estoque pelo ID"
)
def put_product_by_id(
    id: int = Path(..., description="ID do produto a ser editado", ge=1), # Validação de Path
    *,
    edit_product: ProdutoUpdate,
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Atualiza um produto existente (e/ou seu estoque) pelo ID.
    """
    return _handle_db_transaction(
        db,
        product_service.update_product_by_id,
        id,
        edit_product
    )
    
# =========================
# Endpoint: Ativar Produto (Update Lógico)
# Rota: PUT /produtos/ativa/{id}
# =========================
@router.put(
    "/ativa/{id}",
    response_model=ProdutoRead,
    status_code=status.HTTP_200_OK,
    summary="Ativa um produto logicamente no BD"
)
def active_product_by_id(
    id: int = Path(..., description="ID do produto a ser ativado", ge=1),
    # Uso de Optional[str] com Query(None, ...) para campo opcional na URL
    codigo_produto: Optional[str] = Query(
        None, 
        description="Novo código do produto a ser ativado (opcional)"
    ), 
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Ativa um produto existente pelo seu ID, permitindo a redefinição de seu código.
    """
    # A lógica de ativação/atualização de código é executada atomicamente
    return _handle_db_transaction(
        db,
        product_service.active_product_by_id,
        id,
        codigo_produto
    )

# =========================
# Endpoint: Desativar Produto (Update Lógico)
# Rota: PUT /produtos/desativa/{id}
# =========================
@router.put(
    "/desativa/{id}",
    status_code=status.HTTP_204_NO_CONTENT, # Padrão RESTful para deleção/desativação sem corpo de resposta
    summary="Desativa um produto logicamente no BD (Soft Delete)"
)
def disable_product_by_id(
    id: int = Path(..., description="ID do produto a ser desativado", ge=1),
    # Parâmetro booleano obrigatório na Query String
    deletar_codigo: bool = Query(..., description="Define se o código do produto desativado deve ser removido."),
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Desativa um produto existente pelo seu ID.
    O parâmetro `deletar_codigo` controla se o código do produto deve ser removido.
    Retorna 204 No Content.
    """
    # Executa o serviço e garante o rollback em caso de falha
    _handle_db_transaction(
        db,
        product_service.disable_product_by_id,
        id,
        deletar_codigo
    )
    # Retorna Response vazia 204 NO CONTENT
    return Response(status_code=status.HTTP_204_NO_CONTENT)
    
# =========================
# Endpoint: Upload de Foto
# Rota: POST /produtos/{product_id}/fotos
# =========================
@router.post(
    "/{product_id}/fotos",
    response_model=ProdutoFotoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Faz upload de uma imagem e associa ao produto"
)
def upload_product_image(
    product_id: int = Path(..., description="ID do produto a receber a foto."),
    # Uso de File e Form para requisições multipart/form-data (upload de arquivo)
    file: UploadFile = File(..., description="O arquivo de imagem a ser carregado."),
    principal: bool = Form(False, description="Define se esta é a foto principal do produto."),
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Realiza o upload de uma foto, associando-a a um produto existente.
    A requisição deve ser enviada no formato multipart/form-data.
    """
    # A lógica de serviço deve salvar o arquivo e persistir os metadados
    return _handle_db_transaction(
        db,
        product_image_service.create_product_image,
        product_id, 
        file, 
        principal
    )
    
# =========================
# Endpoint: Deletar Foto Específica
# Rota: DELETE /produtos/fotos/{image_id}
# =========================
@router.delete(
    "/fotos/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT, # Padrão RESTful para deleção
    summary="Deleta uma imagem específica do produto"
)
def delete_product_image(
    image_id: int = Path(..., description="ID único da imagem a ser deletada"),
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Deleta uma foto específica do produto pelo seu ID,
    incluindo a exclusão do arquivo físico (lógica no serviço).
    Retorna 204 No Content.
    """
    # Executa o serviço e garante o rollback em caso de falha
    _handle_db_transaction(
        db,
        product_image_service.delete_product_image,
        image_id
    )
    # Retorna Response vazia 204 NO CONTENT
    return Response(status_code=status.HTTP_204_NO_CONTENT)