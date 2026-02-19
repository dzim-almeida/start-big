# ---------------------------------------------------------------------------
# ARQUIVO: endpoints/ordem_servico_foto.py
# DESCRICAO: Gerencia fotos de diagnostico das Ordens de Servico.
# ---------------------------------------------------------------------------

import os
import uuid
from fastapi import APIRouter, Depends, status, Path, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.core.depends import check_permission, _handle_db_transaction
from app.db.session import get_db
from app.schemas.ordem_servico import OrdemServicoFotoRead
from app.db.models.ordem_servico_foto import OrdemServicoFoto as OSFotoModel
from app.db.crud import ordem_servico as os_crud

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "uploads", "os_fotos")


def _save_foto(db: Session, os_id: int, nome_arquivo: str, url: str) -> OSFotoModel:
    """Salva registro da foto no banco."""
    # Verifica se a OS existe
    os_in_db = os_crud.get_ordem_servico_by_id(db, os_id)
    if not os_in_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ordem de Servico nao encontrada"
        )

    foto = OSFotoModel(
        ordem_servico_id=os_id,
        nome_arquivo=nome_arquivo,
        url=url,
    )
    return os_crud.create_os_foto(db, foto)


def _delete_foto(db: Session, foto_id: int) -> dict:
    """Remove uma foto do banco e do disco."""
    foto = os_crud.get_os_foto_by_id(db, foto_id)
    if not foto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foto nao encontrada"
        )

    # Remove arquivo do disco se existir
    if foto.url and os.path.exists(foto.url):
        os.remove(foto.url)

    os_crud.delete_os_foto(db, foto)
    return {"detail": "Foto removida com sucesso"}


@router.post(
    "/{os_id}",
    response_model=OrdemServicoFotoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload de Foto",
    description="Envia uma foto de diagnostico para uma OS."
)
async def upload_foto(
    user_token: dict = Depends(check_permission(required_permission="servico")),
    os_id: int = Path(..., ge=1, description="ID da OS"),
    *,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Garante que o diretorio existe
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Gera nome unico para o arquivo
    ext = os.path.splitext(file.filename or "foto.jpg")[1]
    unique_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    # Salva arquivo no disco
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Salva registro no banco
    return _handle_db_transaction(
        db, _save_foto, os_id, file.filename or "foto.jpg", file_path
    )


@router.delete(
    "/{foto_id}",
    status_code=status.HTTP_200_OK,
    summary="Deletar Foto",
    description="Remove uma foto de diagnostico."
)
def delete_foto(
    user_token: dict = Depends(check_permission(required_permission="servico")),
    foto_id: int = Path(..., ge=1, description="ID da foto"),
    *,
    db: Session = Depends(get_db)
):
    return _handle_db_transaction(db, _delete_foto, foto_id)
