# ---------------------------------------------------------------------------
# ARQUIVO: routers/auth.py
# MÓDULO: Interface de API (Router)
# DESCRIÇÃO: Define os endpoints públicos e protegidos para autenticação.
#            Gerencia o ciclo de vida do Token (emissão e revogação).
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.depends import get_token, _handle_db_transaction
from app.db.session import get_db
from app.schemas.auth import UsuarioLogin, SetupCreate, StatusResponse
from app.schemas.usuario import UsuarioRead
from app.services import auth as auth_service
from app.services import setup as setup_service
from app.db.crud import usuario as usuario_crud

router = APIRouter()

# ===========================================================================
# EMISSÃO DE TOKEN COOKIES (LOGIN)
# ===========================================================================

@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    summary="Login seguro via HttpOnly Cookie"
)
def login_to_acess_cookie(
    response: Response,
    usuario_credentials: UsuarioLogin,
    db: Session = Depends(get_db)
):

    token_value = auth_service.login(db, login_usuario=usuario_credentials)

    response.set_cookie(
        key="access_token", 
        value=token_value,
        httponly=True,  # JS não pode ler
        secure=not settings.DEBUG,
        samesite="Lax",
        expires=6400
    )

    return {"message": "Login bem-sucedido!"}


# ===========================================================================
# REVOGAÇÃO DE TOKEN (LOGOUT)
# ===========================================================================

@router.post(
    "/logout", 
    status_code=status.HTTP_200_OK, 
    summary="Realizar logout, revogar o token e limpar cookie"
)
def logout_to_revoke_token(
    response: Response,
    token: dict = Depends(get_token), 
    db: Session = Depends(get_db)
):
    """
    Invalida o token de acesso atual do usuário.

    O identificador do token (JTI) é adicionado a uma blocklist no banco de dados,
    impedindo que ele seja utilizado novamente para autenticação, mesmo que
    ainda esteja dentro do tempo de expiração.

    Args:
        token (dict): Payload do token atual (extraído via dependência get_token).
        db (Session): Sessão do banco de dados.
    """
    # Chama o serviço de logout para registrar o 'jti' do token na blocklist.
    _handle_db_transaction(
        db,
        auth_service.logout_service,
        token
    )

    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax"
    )

    return {"message": "Logout bem-sucedido"}


# ===========================================================================
# STATUS DO SISTEMA (PÚBLICO)
# ===========================================================================

@router.get(
    "/status",
    response_model=StatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Verifica se o sistema foi inicializado"
)
def get_system_status(db: Session = Depends(get_db)):
    """
    Endpoint público que verifica se existe um usuário Master no sistema.
    Usado pelo frontend para decidir se deve redirecionar para o setup inicial.
    """
    master = usuario_crud.get_usuario_master(db)
    return StatusResponse(inicializado=master is not None)


# ===========================================================================
# SETUP INICIAL (PÚBLICO)
# ===========================================================================

@router.post(
    "/setup",
    status_code=status.HTTP_201_CREATED,
    summary="Setup inicial do sistema"
)
def setup_inicial(
    response: Response,
    setup_data: SetupCreate,
    db: Session = Depends(get_db),
):
    """
    Endpoint público para o setup inicial do sistema.
    Cria atomicamente: Empresa + Endereço + Usuário Master + Cargo Master + Funcionário.
    Retorna cookie de autenticação para login automático.
    """
    token_value = _handle_db_transaction(
        db,
        setup_service.setup_sistema,
        setup_data,
    )

    response.set_cookie(
        key="access_token",
        value=token_value,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="Lax",
        expires=6400,
    )

    return {"message": "Setup concluído com sucesso!"}