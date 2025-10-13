# Serviço de Login

from fastapi import HTTPException, status  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.schemas.auth import UsuarioLogin
from app.db.crud import usuario as usuario_crud
from app.core import security  # Funções de segurança (hash de senha, criação de token)

def login_service(db: Session, usuario: UsuarioLogin) -> dict:
    usuario_existente = usuario_crud.get_usuario_by_email(db, email=usuario.email)
    if not usuario_existente or not security.verify_senha(usuario.senha, usuario_existente.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    dados_para_token = {
        "sub": str(usuario_existente.id),
        "roles": str(usuario_existente.tipo),
    }

    acesso_token = security.create_acesso_token(dados=dados_para_token)
    return {"access_token": acesso_token, "token_type": "bearer", "expires_in": 900}
