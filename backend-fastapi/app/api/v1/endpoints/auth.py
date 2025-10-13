# Endpoint de Login

from fastapi import APIRouter, Depends, HTTPException, status  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.schemas.auth import UsuarioLogin, UsuarioLoginResponse
from app.db.session import get_db  # Função para obter a sessão do banco de dados
from app.services import login as login_service
router = APIRouter()

@router.post("/", response_model=UsuarioLoginResponse, summary="Realizar login e obter token de acesso")
def login_para_acessar_token(usuario: UsuarioLogin, db: Session = Depends(get_db)):
    return login_service.login_service(db, usuario)

