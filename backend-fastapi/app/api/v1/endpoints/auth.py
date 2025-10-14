# Endpoint de Login

from fastapi import APIRouter, Depends, status # type: ignore
from sqlalchemy.orm import Session

from app.schemas.auth import UsuarioLogin, UsuarioLoginResponse
from app.services import auth as auth_service
from app.db.session import get_db

router = APIRouter()

@router.post("/", response_model=UsuarioLoginResponse, status_code=status.HTTP_200_OK, summary="Realizar login e obter token de acesso")
def login_para_acessar_token(usuario: UsuarioLogin, db: Session = Depends(get_db)):
    return auth_service.login_service(db, usuario)

