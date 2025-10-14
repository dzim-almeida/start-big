# Endpoint de Usuários

from fastapi import APIRouter, Depends, status  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.schemas.usuario import UsuarioCreate, UsuarioRead # Importa os modelos Pydantic
from app.db.session import get_db  # Função para obter a sessão do banco de dados
from app.services import usuario as usuario_service
from app.core.depends import get_token

router = APIRouter()

@router.post("/", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED, summary="Criar um novo usuário")
def criar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    return usuario_service.create_usuario_admin_service(db, usuario)
   
@router.get("/me", response_model=UsuarioRead, summary="Retornar o usuário")
def buscar_usuario(token: dict = Depends(get_token), db: Session = Depends(get_db)):
    return usuario_service.get_usuario_by_id(db, int(token.get("sub")))