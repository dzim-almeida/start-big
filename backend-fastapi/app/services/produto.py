# ---------------------------------------------------------------------------
# ARQUIVO: services/produto.py
# MÓDULO: Regras de Negócio (Service Layer)
# DESCRIÇÃO: Lógica para criação, atualização e controle de estado de produtos.
# ---------------------------------------------------------------------------

import os
import uuid
import shutil
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.orm import Session
from typing import Sequence, Optional

from app.schemas.produto import ProdutoCreate, ProdutoUpdate
from app.db.models.produto import Produto as ProdutoModel
from app.db.models.produto_fotos import ProdutoFoto as ProdutoFotoModel
from app.db.models.estoque import Estoque as EstoqueModel
from app.db.crud import produto as produto_crud

# Diretório base onde as imagens serão salvas
UPLOAD_BASE_DIR = "static/uploads/produtos"
# Garante que o diretório base exista
os.makedirs(UPLOAD_BASE_DIR, exist_ok=True)

# Exceções reutilizáveis
conflict_codigo_produto_exce = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail={
        "campo": "codigo_produto",
        "mensagem": "Código de produto já cadastrado no sistema"
    }
)

not_found_exce = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Produto não encontrado no sistema"
)

internal_error_exce = HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="Erro em cumprir a requisição. Tente novamente mais tarde."
)

# ===========================================================================
# LÓGICA DE SALVAMENTO FÍSICO
# ===========================================================================

def save_image_locally(image_file: UploadFile, produto_id: int) -> str:
    file_extension = os.path.splitext(image_file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"

    produto_folder = os.path.join(UPLOAD_BASE_DIR, str(produto_id))
    os.makedirs(produto_folder, exist_ok=True)
    file_path = os.path.join(produto_folder, unique_filename)

    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(image_file.file, f)
    finally:
        image_file.file.close()

    url_image_file = f"{UPLOAD_BASE_DIR}/{produto_id}/{unique_filename}"
    return url_image_file

def delete_image_locally(file_path: str) -> bool:
    if not os.path.exists(file_path):
        return False
    
    try:
        os.remove(file_path)
    except OSError as e_os:
        print(f"Erro ao deletar o arquivo {file_path}: {e_os}")
        return False
    
    image_folder = os.path.dirname(file_path)
    try:
        os.rmdir(image_folder)
        print(f"Diretório do produto removido: {image_folder}")
    except OSError as e_os:
        if "Directory not empty" in str(e_os):
             print(f"Diretório do produto {image_folder} não vazio, mantido.")
        else:
             print(f"Erro ao tentar remover o diretório {image_folder}: {e_os}")

    return True

# ===========================================================================
# LÓGICA DE CRIAÇÃO (CREATE)
# ===========================================================================

def create_produto(db: Session, produto_to_add: ProdutoCreate) -> ProdutoModel:
    """
    Orquestra a criação de um novo produto.
    
    1. Verifica unicidade do código.
    2. Separa dados de Produto e Estoque.
    3. Cria instâncias ORM e vincula.
    4. Persiste.
    """
    # Verifica duplicidade
    produto_in_db = produto_crud.get_produto_by_code(db, produto_to_add.codigo_produto)
    
    if produto_in_db and produto_in_db.ativo:
        raise conflict_codigo_produto_exce
    
    # Prepara dados (separa estoque do produto principal)
    produto_data = produto_to_add.model_dump(exclude={"estoque"})
    produto_to_db = ProdutoModel(**produto_data)

    estoque_data = produto_to_add.estoque.model_dump()
    estoque_for_produto = EstoqueModel(**estoque_data)

    # Vincula estoque ao produto (Relacionamento 1:1)
    produto_to_db.estoque = estoque_for_produto

    return produto_crud.create_produto(db, produto_to_add=produto_to_db)

def create_produto_image(db: Session, produto_id: int, image_file: UploadFile, primary_image: bool) -> ProdutoFotoModel:
    
    produto_in_db = produto_crud.get_produto_by_id(db, produto_id=produto_id)

    if not produto_in_db:
        raise not_found_exce
    
    image_url = save_image_locally(image_file=image_file, produto_id=produto_id)

    produto_image_to_db = ProdutoFotoModel(
        produto_id=produto_id,
        url=image_url,
        nome_arquivo=image_file.filename,
        principal=primary_image,
    )

    return produto_crud.create_produto_image(db, produto_image_to_db)

# ===========================================================================
# LÓGICA DE LEITURA (READ)
# ===========================================================================

def get_produto_by_search(db: Session, produto_search: str | None) -> Sequence[ProdutoModel]:
    """Intermediário para busca de produtos via CRUD."""
    return produto_crud.get_produto_by_search(db, search=produto_search)

# ===========================================================================
# LÓGICA DE ATUALIZAÇÃO (UPDATE)
# ===========================================================================

def update_produto_by_id(db: Session, produto_id: int, produto_to_update: ProdutoUpdate) -> ProdutoModel:
    """
    Atualiza produto e dados de estoque aninhados.
    """
    produto_in_db = produto_crud.get_produto_by_id(db, produto_id=produto_id)
    
    if not produto_in_db:
        raise not_found_exce
    
    data_to_update = produto_to_update.model_dump(exclude_unset=True)

    # Tratamento para atualização de Estoque (Tabela Filha)
    if "estoque" in data_to_update:
        storage_data_to_update = produto_to_update.estoque.model_dump(exclude_unset=True)
        
        # Atualiza atributos do objeto Estoque já existente na sessão
        for key, value in storage_data_to_update.items():
            setattr(produto_in_db.estoque, key, value)
        
        # Remove do dicionário principal para evitar erro de atribuição direta
        del data_to_update["estoque"]

    # Atualiza atributos do Produto (Tabela Pai)
    for key, value in data_to_update.items():
        setattr(produto_in_db, key, value)

    return produto_crud.update_produto(db, produto_in_db)

# ===========================================================================
# LÓGICA DE STATUS (TOGGLE)
# ===========================================================================

def toggle_active_disable_produto_by_id(db: Session, produto_id: int, new_produto_code: str | None) -> ProdutoModel:
    """
    Alterna status Ativo/Inativo.
    Se estiver reativando, verifica conflito de código e permite atualização.
    """
    produto_in_db = produto_crud.get_produto_by_id(db, produto_id=produto_id)
    
    if not produto_in_db:
        raise not_found_exce
    
    # Lógica de Reativação (Inativo -> Ativo)
    if not produto_in_db.ativo:
        
        # Define qual código validar (o novo sugerido ou o atual existente)
        codigo_to_verify = new_produto_code if new_produto_code else produto_in_db.codigo_produto
        
        # Busca conflitos
        produto_with_same_code_in_db = produto_crud.get_produto_by_code(db, produto_code=codigo_to_verify)

        # Se existe conflito e não é o mesmo produto
        if produto_with_same_code_in_db and produto_with_same_code_in_db.id != produto_in_db.id:
            conflict_codigo_produto_exce.detail["mensagem"] = f"Código '{codigo_to_verify}' já cadastrado. Envie um novo código."
            raise conflict_codigo_produto_exce
        
        # Se forneceu código novo e passou na validação, atualiza
        if new_produto_code:
            produto_in_db.codigo_produto = new_produto_code
                
    # Inverte o status
    produto_in_db.ativo = not produto_in_db.ativo

    return produto_crud.update_produto(db, produto_to_update=produto_in_db)

# ===========================================================================
# LÓGICA DE DELEÇÃO (DELETE)
# ===========================================================================

def delete_produto_image(db: Session, image_id: int):
    
    image_in_db = produto_crud.get_produto_image_by_id(db, image_id=image_id)

    if not image_in_db:
        raise not_found_exce
    
    file_path = image_in_db.url
    
    if not delete_image_locally(file_path=file_path):
        raise internal_error_exce
    
    return produto_crud.delete_produto_image(db, image_to_delete=image_in_db)