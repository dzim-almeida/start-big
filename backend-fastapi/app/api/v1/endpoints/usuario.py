# Endpoint de Usuários

from fastapi import APIRouter, Depends, HTTPException, status  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.schemas.usuario import UsuarioCreate, UsuarioRead # Importa os modelos Pydantic
from app.db.session import get_db  # Função para obter a sessão do banco de dados
from app.services import usuario as usuario_service  # Importa o serviço de criação de usuário

router = APIRouter()

@router.post("/", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED, summary="Criar um novo usuário")
def criar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    return usuario_service.create_usuario_admin_service(db, usuario)
   