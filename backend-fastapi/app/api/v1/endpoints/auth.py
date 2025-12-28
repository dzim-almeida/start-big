# ---------------------------------------------------------------------------
# ARQUIVO: routers/auth.py
# MÓDULO: Interface de API (Router)
# DESCRIÇÃO: Define os endpoints públicos e protegidos para autenticação.
#            Gerencia o ciclo de vida do Token (emissão e revogação).
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.depends import get_token
from app.db.session import get_db
from app.schemas.auth import UsuarioLogin, UsuarioLoginResponse
from app.services import auth as auth_service

router = APIRouter()

# ===========================================================================
# EMISSÃO DE TOKEN (LOGIN)
# ===========================================================================

@router.post(
    "/login",
    response_model=UsuarioLoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Login para receber Token",
    description="Recebe email e senha (OAuth2 Form), valida credenciais e retorna o Token JWT."
)
def login_to_access_token(
    # login_usuario: OAuth2PasswordRequestForm = Depends(),
    usuario: UsuarioLogin,
    db: Session = Depends(get_db)
):
    """
    Realiza a autenticação do usuário.

    Converte o formulário padrão OAuth2 (username/password) para o schema interno
    e delega a verificação de hash e geração de JWT para o serviço.

    Args:
        login_usuario (OAuth2PasswordRequestForm): Dados do formulário (username=email).
        db (Session): Sessão do banco de dados.

    Returns:
        UsuarioLoginResponse: Objeto contendo o access_token e o token_type.
    """
    # Mapeia o campo 'username' do form-data para o campo 'email' do nosso schema
    # usuario = UsuarioLogin(
    #     email=login_usuario.username,
    #     senha=login_usuario.password
    # )

    return auth_service.login(db, login_usuario=usuario)


# ===========================================================================
# REVOGAÇÃO DE TOKEN (LOGOUT)
# ===========================================================================

@router.post(
    "/logout", 
    status_code=status.HTTP_200_OK, 
    summary="Realizar logout e revogar o token"
)
def logout_to_revoke_token(
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
    auth_service.logout_service(db, token)

    # Persiste a revogação no banco imediatamente
    db.commit()

    return {"message": "Logout bem-sucedido"}