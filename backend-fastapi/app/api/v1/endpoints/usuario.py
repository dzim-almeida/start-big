# Endpoint de Usuários

from fastapi import APIRouter, Depends, HTTPException, status  # type: ignore
from sqlalchemy.orm import Session  # type: ignore
from datetime import datetime

from app.db.models.usuario import Usuario as UsuarioModel  # Importa o modelo SQLAlchemy
from app.schemas.usuario import UsuarioCreate, UsuarioRead # Importa os modelos Pydantic
from app.db.session import get_db  # Função para obter a sessão do banco de dados
from app.core.security import gerar_senha_hash  # Funções de segurança
from app.core.enum import TipoUsuario

router = APIRouter()

@router.post("/", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED, summary="Criar um novo usuário")
def criar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    # Verifica se o email já existe
    usuario_existente = db.query(UsuarioModel).filter(UsuarioModel.email == usuario.email).first()
    if usuario_existente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email já cadastrado")

    senha_hash = gerar_senha_hash(usuario.senha)

    novo_usuario = UsuarioModel(
        tipo=TipoUsuario(usuario.tipo),
        nome=usuario.nome,
        email=usuario.email,
        senha_hash=senha_hash,
        criado_em=datetime.now()
    )

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    return novo_usuario
