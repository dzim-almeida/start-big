# Endpoint de Login

from fastapi import APIRouter, Depends, status # type: ignore
from sqlalchemy.orm import Session

from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.auth import UsuarioLogin, UsuarioLoginResponse
from app.services import auth as auth_service
from app.db.session import get_db
from app.core.depends import get_token

router = APIRouter()

# @router.post("/login", response_model=UsuarioLoginResponse, status_code=status.HTTP_200_OK, summary="Realizar login e obter token de acesso")
# def login_para_acessar_token(user_data: UsuarioLogin, db: Session = Depends(get_db)):
#     return auth_service.login_service(db, user_data)

@router.post("/login", response_model=UsuarioLoginResponse, status_code=status.HTTP_200_OK, summary="Realizar login e obter token de acesso")
def login_to_access_token(user_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = UsuarioLogin(
        email=user_data.username,
        senha=user_data.password
    )
    return auth_service.login_service(db, user)

@router.post("/logout", status_code=status.HTTP_200_OK, summary="Realizar logout e revogar o token")
def logout_to_revoke_token(token: dict = Depends(get_token), db: Session = Depends(get_db)):
    auth_service.logout_service(db, token)
    db.commit()
    return {"message": "Logout bem-sucedido"}