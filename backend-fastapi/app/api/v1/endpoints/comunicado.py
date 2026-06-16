from fastapi import APIRouter, Depends, status, Path
from sqlalchemy.orm import Session

from app.core.depends import get_current_active_user, _handle_db_transaction
from app.db.session import get_db
from app.schemas.comunicado import ComunicadoCreate, ComunicadoRead
from app.services import comunicado as comunicado_service

router = APIRouter()


@router.get(
    "/",
    response_model=list[ComunicadoRead],
    status_code=status.HTTP_200_OK,
    summary="Listar comunicados da empresa",
)
def listar_comunicados(
    usuario_token: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    empresa_id = int(usuario_token.get("empresa_id"))
    funcionario_id = int(usuario_token.get("funcionario_id", 0))
    return comunicado_service.listar_comunicados(db, empresa_id, funcionario_id)


@router.post(
    "/",
    response_model=ComunicadoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Criar comunicado (master/gerente)",
)
def criar_comunicado(
    data: ComunicadoCreate,
    usuario_token: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    empresa_id = int(usuario_token.get("empresa_id"))
    funcionario_id = int(usuario_token.get("funcionario_id", 0))
    return _handle_db_transaction(
        db, comunicado_service.criar_comunicado, empresa_id, funcionario_id, data
    )


@router.put(
    "/{comunicado_id}/ler",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Marcar comunicado como lido",
)
def marcar_lido(
    comunicado_id: int = Path(..., ge=1),
    usuario_token: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    empresa_id = int(usuario_token.get("empresa_id"))
    funcionario_id = int(usuario_token.get("funcionario_id", 0))
    _handle_db_transaction(
        db, comunicado_service.marcar_lido, comunicado_id, empresa_id, funcionario_id
    )
