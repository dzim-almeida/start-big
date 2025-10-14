# Serviço para operações relacionadas a usuários

from fastapi import HTTPException, status  # type: ignore
from sqlalchemy.orm import Session  # type: ignore
from datetime import datetime

from app.db.models.usuario import Usuario as UsuarioModel  # Importa o modelo SQLAlchemy
from app.schemas.usuario import UsuarioCreate  # Importa o modelo Pydantic
from app.core import security  # Função para gerar hash de senha
from app.core.enum import TipoUsuario  # Importa o enum de tipos de usuário
from app.db.crud import usuario as usuario_crud  # Função CRUD para criar usuário

def get_usuario_by_id(db: Session, usuario_id: int) -> UsuarioModel:
    usuario_existente = usuario_crud.get_usuario_by_id(db, usuario_id)
    if not usuario_existente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    return usuario_existente

# Função para criar um usuário admin
def create_usuario_admin_service(db: Session, novo_usuario: UsuarioCreate):
    # Verifica se o email já existe
    usuario_existente = usuario_crud.get_usuario_by_email(db, novo_usuario.email)
    if usuario_existente:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email já cadastrado")

    senha_hash = security.generate_senha_hash(novo_usuario.senha)

    novo_usuario = UsuarioModel(
        tipo=TipoUsuario.ADMIN,
        nome=novo_usuario.nome,
        email=novo_usuario.email,
        senha_hash=senha_hash,
        data_criacao=datetime.now()
    )

    return usuario_crud.create_usuario_db(db, novo_usuario)