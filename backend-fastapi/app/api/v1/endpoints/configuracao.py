from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.depends import get_current_active_user, _handle_db_transaction
from app.db.session import get_db
from app.schemas.configuracao_clientes import ConfiguracaoClientesRead, ConfiguracaoClientesUpdate
from app.schemas.configuracao_produtos import ConfiguracaoProdutosRead, ConfiguracaoProdutosUpdate
from app.schemas.configuracao_os import ConfiguracaoOSRead, ConfiguracaoOSUpdate
from app.services import configuracao_clientes as configuracao_clientes_service
from app.services import configuracao_produtos as configuracao_produtos_service
from app.services import configuracao_os as configuracao_os_service

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
        configuracao_clientes_service.get_or_create_configuracao_clientes,
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
        configuracao_clientes_service.update_configuracao_clientes,
        empresa_id,
        data,
    )


@router.get(
    "/produtos",
    response_model=ConfiguracaoProdutosRead,
    status_code=status.HTTP_200_OK,
    summary="Buscar configurações de produtos e estoque",
)
def get_configuracao_produtos(
    usuario_token: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    empresa_id = int(usuario_token.get("empresa_id"))
    return _handle_db_transaction(
        db,
        configuracao_produtos_service.get_or_create_configuracao_produtos,
        empresa_id,
    )


@router.put(
    "/produtos",
    response_model=ConfiguracaoProdutosRead,
    status_code=status.HTTP_200_OK,
    summary="Atualizar configurações de produtos e estoque",
)
def update_configuracao_produtos(
    data: ConfiguracaoProdutosUpdate,
    usuario_token: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    empresa_id = int(usuario_token.get("empresa_id"))
    return _handle_db_transaction(
        db,
        configuracao_produtos_service.update_configuracao_produtos,
        empresa_id,
        data,
    )


@router.get(
    "/os",
    response_model=ConfiguracaoOSRead,
    status_code=status.HTTP_200_OK,
    summary="Buscar configurações de ordens de serviço",
)
def get_configuracao_os(
    usuario_token: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    empresa_id = int(usuario_token.get("empresa_id"))
    return _handle_db_transaction(
        db,
        configuracao_os_service.get_or_create_configuracao_os,
        empresa_id,
    )


@router.put(
    "/os",
    response_model=ConfiguracaoOSRead,
    status_code=status.HTTP_200_OK,
    summary="Atualizar configurações de ordens de serviço",
)
def update_configuracao_os(
    data: ConfiguracaoOSUpdate,
    usuario_token: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    empresa_id = int(usuario_token.get("empresa_id"))
    return _handle_db_transaction(
        db,
        configuracao_os_service.update_configuracao_os_service,
        empresa_id,
        data,
    )
