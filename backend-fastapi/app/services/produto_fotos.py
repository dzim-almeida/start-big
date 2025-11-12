# ---------------------------------------------------------------------------
# ARQUIVO: app/services/produto_fotos.py (Presumido)
# DESCRIÇÃO: Camada de Serviço para a lógica de negócio (uploads, deleção,
#            e I/O de arquivos) de fotos de produto.
# ---------------------------------------------------------------------------

import os
import uuid
import shutil
from datetime import datetime
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.orm import Session
from app.db.models.produto_fotos import ProdutoFoto as ProdutoFotoModel
# Importa as funções de CRUD (Repositório) para o registro de metadados
from app.db.crud import produto_fotos as product_image_crud
# Importa as funções de CRUD (Repositório) para buscar o produto pai
from app.db.crud import produto as product_crud

# Diretório base onde as imagens serão salvas
UPLOAD_BASE_DIR = "static/uploads/produtos"
# Garante que o diretório base exista
os.makedirs(UPLOAD_BASE_DIR, exist_ok=True)

# =========================
# Função: Salvar Arquivo Fisicamente
# =========================
def save_file_locally(file: UploadFile, product_id: int) -> str:
    """
    Salva o arquivo de imagem no sistema de arquivos local.
    Cria uma pasta para o produto e gera um nome de arquivo único (UUID).
    Retorna a URL/caminho relativo de acesso.
    """
    # 1. Gera nome único
    file_extesion = os.path.splitext(file.filename)[1] # Extrai a extensão
    unique_filename = f"{uuid.uuid4()}{file_extesion}" # Cria UUID + extensão

    # 2. Define o caminho da pasta
    product_folder = os.path.join(UPLOAD_BASE_DIR, str(product_id))
    os.makedirs(product_folder, exist_ok=True) # Cria a pasta específica do produto (se não existir)
    file_path = os.path.join(product_folder, unique_filename) # Caminho completo do arquivo

    try:
        # 3. Salva o arquivo
        with open(file_path, "wb") as f:
            # Usa shutil.copyfileobj para lidar eficientemente com o arquivo binário do UploadFile
            shutil.copyfileobj(file.file, f)
    finally:
        # Garante que o stream de arquivo do FastAPI seja fechado
        file.file.close()

    # 4. Retorna o caminho de acesso (URL) que será salvo no DB
    url = f"{UPLOAD_BASE_DIR}/{product_id}/{unique_filename}"
    return url

# =========================
# Função: Deletar Arquivo Fisicamente
# =========================
def delete_file_locally(file_path: str) -> bool:
    """
    Deleta o arquivo físico do sistema de arquivos.
    Tenta remover a pasta do produto se ela ficar vazia.
    """
    # 1. Verifica se o arquivo existe
    if not os.path.exists(file_path):
        return False # Arquivo não encontrado (pode ser considerado um sucesso em deleção)
    
    # 2. Deleta o arquivo
    try:
        os.remove(file_path)
    except OSError as e:
        print(f"Erro ao deletar o arquivo {file_path}: {e}")
        return False # Falha ao deletar o arquivo
        
    # 3. Tenta remover a pasta-mãe (limpeza)
    image_folder = os.path.dirname(file_path)
    try:
        # Tenta remover o diretório. 
        # rmdir só remove se o diretório estiver **completamente vazio**.
        os.rmdir(image_folder)
        # Se chegou aqui, a pasta estava vazia e foi removida.
        print(f"Diretório do produto removido: {image_folder}")
    except OSError as e:
        # rmdir falha (levanta OSError) se o diretório não estiver vazio, 
        # ou se houver outro problema (ex: permissão). 
        if "Directory not empty" in str(e):
             print(f"Diretório do produto {image_folder} não vazio, mantido.")
        else:
             print(f"Erro ao tentar remover o diretório {image_folder}: {e}")
             
    return True # Arquivo deletado com sucesso

# =========================
# Serviço: Criar Foto do Produto (Upload)
# =========================
def create_product_image(db: Session, product_id: int, file: UploadFile, primary: bool) -> ProdutoFotoModel:
    """
    Orquestra o upload da imagem e o registro de seus metadados no banco de dados.
    """
    # 1. Validação: Verifica se o produto existe
    product_in_db = product_crud.get_product_by_id(db, product_id)
    
    if not product_in_db:
        # Lança erro 404 para o endpoint
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado."
        )
    
    # 2. I/O: Salva o arquivo fisicamente
    image_url = save_file_locally(file, product_id)

    # 3. Cria o objeto do Modelo ORM
    new_image_to_db = ProdutoFotoModel(
        produto_id=product_id,
        url=image_url,
        nome_arquivo=file.filename, # Salva o nome original do arquivo (útil para o usuário)
        principal=primary,
        data_upload=datetime.now()
    )

    # 4. Repositório: Salva os metadados no BD
    image_in_db = product_image_crud.create_product_image(db, new_image_to_db)
    # O commit será feito no endpoint
    return image_in_db

# =========================
# Serviço: Deletar Foto do Produto
# =========================
def delete_product_image(db: Session, image_id: int) -> None:
    """
    Orquestra a exclusão dos metadados e do arquivo físico.
    """
    # 1. Repositório: Busca o registro no DB
    image_in_db = product_image_crud.get_product_image_by_id(db, image_id)
    
    if not image_in_db:
        # Lança erro 404 se o registro não existir
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Imagem não encontrada."
        )
    
    # 2. I/O: Deleta o arquivo físico (usa a URL como caminho)
    if not delete_file_locally(image_in_db.url):
        # Lança erro se a exclusão física falhar (403 FORBIDDEN - permissão, etc.)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Falha ao deletar o arquivo físico no servidor." # Adicionado detalhe para melhor contexto do erro
        )
    
    # 3. Repositório: Deleta o registro de metadados no BD
    # O valor de retorno da função CRUD deve ser None, conforme o endpoint espera
    return product_image_crud.delete_product_image(db, image_in_db)