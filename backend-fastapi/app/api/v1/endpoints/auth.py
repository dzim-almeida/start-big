# ---------------------------------------------------------------------------
# ARQUIVO: routers/auth.py
# MÓDULO: Interface de API (Router)
# DESCRIÇÃO: Define os endpoints públicos e protegidos para autenticação.
#            Gerencia o ciclo de vida do Token (emissão e revogação).
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.depends import get_token, _handle_db_transaction
from app.db.session import get_db
from app.schemas.auth import UsuarioLogin, UsuarioLoginResponse
from app.schemas.usuario import UsuarioRead
from app.services import auth as auth_service

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
        secure=False,   # True apenas em produção
        samesite="lax",
        max_age=1
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