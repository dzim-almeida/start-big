# Arquivo para criação e validação do JWT

from fastapi import HTTPException, Depends, status  # type: ignore
from sqlalchemy.orm import Session  # type: ignore
from fastapi.security import OAuth2PasswordBearer

from app.core import security
from app.db.crud import usuario as usuario_crud
from app.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/")

def get_token(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    dados_token = security.verify_dados_token(token)
    usuario_existente = usuario_crud.get_usuario_by_id(db, dados_token.get("sub"))
    if not usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário do token não encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return dados_token

    