# Endpoint de Login

from fastapi import APIRouter, Depends, HTTPException, status  # type: ignore
from fastapi.security import OAuth2PasswordRequestForm  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.db.session import get_db  # Função para obter a sessão do banco de dados
from app.services import login as login_service
router = APIRouter()

@router.post("/", summary="Realizar login e obter token de acesso")
def login_para_acessar_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return login_service.login_service(db, form_data)

