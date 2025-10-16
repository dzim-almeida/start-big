# Endpoint de Usuários

from fastapi import APIRouter, Depends, status  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.schemas.usuario import UsuarioCreate, UsuarioRead # Importa os modelos Pydantic
from app.db.session import get_db  # Função para obter a sessão do banco de dados
from app.services import usuario as user_service
from app.core.depends import get_token

router = APIRouter()

@router.post("/", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED, summary="Criar um novo usuário")
def create_user(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    return user_service.create_user_admin_service(db, usuario)
   
@router.get("/me", response_model=UsuarioRead, summary="Retornar o usuário")
def get_user(token: dict = Depends(get_token), db: Session = Depends(get_db)):
    return user_service.get_user_by_id(db, int(token.get("sub")))