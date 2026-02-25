# ---------------------------------------------------------------------------
# ARQUIVO: services/ordem_servico_foto.py
# DESCRICAO: Lógica de negócio para upload e remoção de fotos de OS.
#
# Estrutura de armazenamento:
#   static/uploads/ordens-servico/{os_id}/{uuid}.{ext}
#
# Os arquivos são nomeados com UUID para evitar conflitos.
# A URL salva no banco é o caminho relativo ao diretório raiz do servidor.
# Fotos são acessíveis via: GET /static/uploads/ordens-servico/{os_id}/{arquivo}
# ---------------------------------------------------------------------------

import os
import shutil
import uuid

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.models.ordem_servico_foto import OrdemServicoFoto as OSFotoModel
from app.db.crud import ordem_servico as os_crud
from app.schemas.ordem_servico import OSFotoRead


# Diretório base de upload de fotos de OS (relativo à raiz do servidor)
UPLOAD_BASE_DIR = "static/uploads/ordens-servico"
os.makedirs(UPLOAD_BASE_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Exceções reutilizáveis
# ---------------------------------------------------------------------------

os_not_found_exce = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Ordem de Serviço não encontrada"
)

foto_not_found_exce = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Foto não encontrada"
)

file_delete_error_exce = HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="Erro ao remover o arquivo da foto do disco"
)


# ---------------------------------------------------------------------------
# Funções auxiliares de I/O
# ---------------------------------------------------------------------------

def save_foto_locally(image_file: UploadFile, os_id: int) -> str:
    """
    Salva o arquivo de imagem no disco com nome UUID para evitar conflitos.

    Retorna o caminho relativo do arquivo (usado como URL no banco).
    Estrutura: static/uploads/ordens-servico/{os_id}/{uuid}.{ext}
    """
    file_extension = os.path.splitext(image_file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"

    os_folder = os.path.join(UPLOAD_BASE_DIR, str(os_id))
    os.makedirs(os_folder, exist_ok=True)

    file_path = os.path.join(os_folder, unique_filename)

    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(image_file.file, f)
    finally:
        image_file.file.close()

    return f"{UPLOAD_BASE_DIR}/{os_id}/{unique_filename}"


def delete_foto_locally(file_path: str) -> bool:
    """
    Remove o arquivo de foto do disco.
    Tenta limpar o diretório do OS se ficar vazio após a remoção.

    Retorna True em caso de sucesso, False se o arquivo não existir.
    """
    if not os.path.exists(file_path):
        return False

    try:
        os.remove(file_path)
    except OSError as e:
        print(f"Erro ao deletar foto {file_path}: {e}")
        return False

    # Tenta remover o diretório da OS se estiver vazio
    os_folder = os.path.dirname(file_path)
    try:
        os.rmdir(os_folder)
    except OSError:
        pass  # Diretório não está vazio ou outro erro — mantém o diretório

    return True


# ---------------------------------------------------------------------------
# Funções de serviço
# ---------------------------------------------------------------------------

def upload_foto_os(db: Session, numero_os: str, image_file: UploadFile) -> OSFotoModel:
    """
    Faz o upload de uma foto de diagnóstico para uma OS.

    Salva o arquivo em disco e registra a referência no banco.
    Retorna o modelo da foto criada.
    """
    os_in_db = os_crud.get_ordem_servico_by_numero_os(db, numero_os=numero_os)
    if not os_in_db:
        raise os_not_found_exce

    foto_url = save_foto_locally(image_file=image_file, os_id=os_in_db.id)

    foto_to_db = OSFotoModel(
        ordem_servico_id=os_in_db.id,
        nome_arquivo=image_file.filename,
        url=foto_url,
    )

    return os_crud.create_os_foto(db, foto_to_add=foto_to_db)


def delete_foto_os(db: Session, numero_os: str, foto_id: int) -> None:
    """
    Remove uma foto de OS: deleta o arquivo físico e o registro no banco.

    Valida que a foto pertence à OS informada (segurança por ownership).
    Lança 404 se a OS ou a foto não existir e 500 se o arquivo não puder ser removido.
    """
    os_in_db = os_crud.get_ordem_servico_by_numero_os(db, numero_os=numero_os)
    if not os_in_db:
        raise os_not_found_exce

    foto_in_db = os_crud.get_os_foto_by_id(db, foto_id=foto_id)
    if not foto_in_db or foto_in_db.ordem_servico_id != os_in_db.id:
        raise foto_not_found_exce

    if not delete_foto_locally(file_path=foto_in_db.url):
        raise file_delete_error_exce

    os_crud.delete_os_foto(db, foto_to_delete=foto_in_db)
