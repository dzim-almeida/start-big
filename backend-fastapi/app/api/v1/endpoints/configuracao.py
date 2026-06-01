from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.depends import get_current_active_user, _handle_db_transaction
from app.db.session import get_db
from app.schemas.configuracao_clientes import ConfiguracaoClientesRead, ConfiguracaoClientesUpdate
from app.services import configuracao_clientes as configuracao_service

router = APIRouter()


@router.get(
    "/clientes",
    response_model=ConfiguracaoClientesRead,
    status_code=status.HTTP_200_OK,
    summary="Buscar configurações de clientes",
)
def get_configuracao_clientes(
    usuario_token: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    empresa_id = int(usuario_token.get("empresa_id"))
    return _handle_db_transaction(
        db,
        configuracao_service.get_or_create_configuracao_clientes,
        empresa_id,
    )


@router.put(
    "/clientes",
    response_model=ConfiguracaoClientesRead,
    status_code=status.HTTP_200_OK,
    summary="Atualizar configurações de clientes",
)
def update_configuracao_clientes(
    data: ConfiguracaoClientesUpdate,
    usuario_token: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    empresa_id = int(usuario_token.get("empresa_id"))
    return _handle_db_transaction(
        db,
        configuracao_service.update_configuracao_clientes,
        empresa_id,
        data,
    )
