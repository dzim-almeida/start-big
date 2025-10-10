# Serviço de Login

from fastapi import HTTPException, status  # type: ignore
from fastapi.security import OAuth2PasswordRequestForm  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.db.models.usuario import Usuario as UsuarioModel  # Modelo de usuário
from app.db.crud import usuario as usuario_crud
from app.core import security  # Funções de segurança (hash de senha, criação de token)

def login_service(db: Session, form_data: OAuth2PasswordRequestForm) -> dict:
    usuario_existente = usuario_crud.get_usuario_by_email(db, email=form_data.username)
    if not usuario_existente or not security.verify_senha(form_data.password, usuario_existente.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    acesso_token = security.create_acesso_token(dados={"sub": usuario_existente.email, "tipo": usuario_existente.tipo.value})
    return {"access_token": acesso_token, "token_type": "bearer"}
