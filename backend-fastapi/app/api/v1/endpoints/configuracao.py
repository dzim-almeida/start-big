from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.depends import check_permission, get_current_active_user, _handle_db_transaction
from app.db.session import get_db
from app.schemas.configuracao_clientes import ConfiguracaoClientesRead, ConfiguracaoClientesUpdate
from app.schemas.configuracao_produtos import ConfiguracaoProdutosRead, ConfiguracaoProdutosUpdate
from app.schemas.configuracao_os import ConfiguracaoOSRead, ConfiguracaoOSUpdate
from app.schemas.configuracao_vendas import ConfiguracaoVendasRead, ConfiguracaoVendasUpdate
from app.schemas.configuracao_seguranca import ConfiguracaoSegurancaRead, ConfiguracaoSegurancaUpdate, VerificarPinPayload
from app.services import configuracao_clientes as configuracao_clientes_service
from app.services import configuracao_produtos as configuracao_produtos_service
from app.services import configuracao_os as configuracao_os_service
from app.services import configuracao_vendas as configuracao_vendas_service
from app.services import configuracao_seguranca as configuracao_seguranca_service
from app.schemas.configuracao_marcenaria import (
    ConfiguracaoMarcenariaCompleta,
    ConfiguracaoMarcenariaPublica,
    ConfiguracaoMarcenariaUpdate,
)
from app.services import configuracao_marcenaria as configuracao_marcenaria_service
from app.services.marcenaria.permissoes import PERMISSOES_GERIR_CUSTOS, pode_ver_custos_marcenaria

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


@router.get(
    "/vendas",
    response_model=ConfiguracaoVendasRead,
    status_code=status.HTTP_200_OK,
    summary="Buscar configurações de regras de vendas",
)
def get_configuracao_vendas(
    usuario_token: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    empresa_id = int(usuario_token.get("empresa_id"))
    return _handle_db_transaction(
        db,
        configuracao_vendas_service.get_or_create_configuracao_vendas,
        empresa_id,
    )


@router.put(
    "/vendas",
    response_model=ConfiguracaoVendasRead,
    status_code=status.HTTP_200_OK,
    summary="Atualizar configurações de regras de vendas",
)
def update_configuracao_vendas(
    data: ConfiguracaoVendasUpdate,
    usuario_token: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    empresa_id = int(usuario_token.get("empresa_id"))
    return _handle_db_transaction(
        db,
        configuracao_vendas_service.update_configuracao_vendas,
        empresa_id,
        data,
    )


@router.get(
    "/seguranca",
    response_model=ConfiguracaoSegurancaRead,
    status_code=status.HTTP_200_OK,
    summary="Buscar configurações de segurança e aprovações",
)
def get_configuracao_seguranca(
    usuario_token: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    empresa_id = int(usuario_token.get("empresa_id"))
    return _handle_db_transaction(
        db,
        configuracao_seguranca_service.get_or_create_configuracao_seguranca,
        empresa_id,
    )


@router.put(
    "/seguranca",
    response_model=ConfiguracaoSegurancaRead,
    status_code=status.HTTP_200_OK,
    summary="Atualizar configurações de segurança e aprovações",
)
def update_configuracao_seguranca(
    data: ConfiguracaoSegurancaUpdate,
    usuario_token: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    empresa_id = int(usuario_token.get("empresa_id"))
    return _handle_db_transaction(
        db,
        configuracao_seguranca_service.update_configuracao_seguranca,
        empresa_id,
        data,
    )


@router.post(
    "/seguranca/verificar-pin",
    status_code=status.HTTP_200_OK,
    summary="Verificar PIN do gerente",
)
def verificar_pin_seguranca(
    payload: VerificarPinPayload,
    usuario_token: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    empresa_id = int(usuario_token.get("empresa_id"))
    configuracao_seguranca_service.verificar_pin_gerente(db, empresa_id, payload.pin)
    return {"ok": True}


# ===========================================================================
# MARCENARIA (Spec 04A) — parametros padrao do orcamento tecnico
# ===========================================================================

@router.get(
    "/marcenaria",
    response_model=ConfiguracaoMarcenariaCompleta | ConfiguracaoMarcenariaPublica,
    status_code=status.HTTP_200_OK,
    summary="Parâmetros do orçamento de marcenaria",
    description=(
        "Qualquer usuário logado lê validade, prazo, etapas e checklist. Markup, perda, "
        "custo/hora e RT só vêm para quem tem 'view_custos_marcenaria' (ou master/'all'); "
        "`inclui_custos` diz qual dos dois formatos veio. 404 fora da marcenaria."
    ),
)
def get_configuracao_marcenaria(
    usuario_token: dict = Depends(get_current_active_user),       # qualquer usuario logado (D9)
    db: Session = Depends(get_db),
):
    empresa_id = int(usuario_token.get("empresa_id"))
    config = _handle_db_transaction(db, configuracao_marcenaria_service.obter_configuracao, empresa_id)
    # Recorte por permissao: sem view_custos, so os campos sem custo (D9). Os
    # campos de custo NAO aparecem (nem como null) na resposta publica.
    if pode_ver_custos_marcenaria(usuario_token):
        return ConfiguracaoMarcenariaCompleta.model_validate(config)
    return ConfiguracaoMarcenariaPublica.model_validate(config)


@router.put(
    "/marcenaria",
    response_model=ConfiguracaoMarcenariaCompleta,
    status_code=status.HTTP_200_OK,
    summary="Atualizar parâmetros do orçamento de marcenaria",
    description="Exige 'manage_custos_marcenaria' (D10). Corpo parcial: só os campos enviados mudam.",
)
def update_configuracao_marcenaria(
    data: ConfiguracaoMarcenariaUpdate,
    # A permissao e conferida ANTES do segmento: sem ela, 403 em qualquer segmento.
    usuario_token: dict = Depends(check_permission(required_permission=PERMISSOES_GERIR_CUSTOS)),
    db: Session = Depends(get_db),
):
    empresa_id = int(usuario_token.get("empresa_id"))
    config = _handle_db_transaction(
        db,
        configuracao_marcenaria_service.atualizar_configuracao,
        empresa_id,
        data,
    )
    return ConfiguracaoMarcenariaCompleta.model_validate(config)
