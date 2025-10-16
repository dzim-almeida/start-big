# ---------------------------------------------------------------------------
# ARQUIVO: auth.py (endpoints)
# DESCRIÇÃO: Define os endpoints para autenticação (login e logout).
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.depends import get_token
from app.db.session import get_db
from app.schemas.auth import UsuarioLogin, UsuarioLoginResponse
from app.services import auth as auth_service

router = APIRouter()

@router.post("/login", response_model=UsuarioLoginResponse, status_code=status.HTTP_200_OK, summary="Realizar login e obter token de acesso")
def login_to_access_token(user_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Endpoint para autenticar um usuário via form data (username/password) e
    retornar um token de acesso.
    """
    # Converte os dados do formulário para o schema Pydantic esperado pelo serviço.
    user = UsuarioLogin(
        email=user_data.username,
        senha=user_data.password
    )
    # Chama o serviço de login para validar as credenciais e gerar o token.
    return auth_service.login_service(db, user)

@router.post("/logout", status_code=status.HTTP_200_OK, summary="Realizar logout e revogar o token")
def logout_to_revoke_token(token: dict = Depends(get_token), db: Session = Depends(get_db)):
    """
    Endpoint para invalidar o token de acesso atual do usuário.
    O token é adicionado a uma blocklist e não poderá mais ser usado.
    """
    # Chama o serviço de logout para registrar o 'jti' do token na blocklist.
    # A dependência 'get_token' já garante que o token é válido antes de chegar aqui.
    auth_service.logout_service(db, token)

    # Comita a transação para salvar permanentemente a revogação do token no banco.
    db.commit()

    return {"message": "Logout bem-sucedido"}