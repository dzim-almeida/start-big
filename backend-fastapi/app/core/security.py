# Arquivo para segurança, como hashing de senhas e verificação

from fastapi import HTTPException, Depends, status

import bcrypt # type: ignore

from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError # type: ignore
from app.core.config import settings
import uuid

def verify_senha(senha: str, senha_hash: str) -> bool:
    senha_bytes = senha.encode('utf-8')
    senha_hash_bytes = senha_hash.encode('utf-8')
    # Verifica se a senha fornecida corresponde ao hash armazenado
    return bcrypt.checkpw(senha_bytes, senha_hash_bytes)

def generate_senha_hash(senha: str) -> str:
    # Gera um hash seguro para a senha fornecida
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')

def create_acesso_token(dados: dict) -> str:

    # Cria um token JWT com os dados fornecidos
    to_encode = dados.copy()

    # Adiciona jti (JWT ID) para rastreamento/revogação
    to_encode.update({"jti": str(uuid.uuid4())})

    # Adiciona tempo para expiração
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    # Gera o token JWT usando a chave secreta e o algoritmo especificado
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_dados_token(token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        dados_token = jwt.decode(token, settings.SECRET_KEY, algorithms=settings.ALGORITHM)
        usuario_id = dados_token.get("sub")
        if usuario_id is None:
            raise credentials_exception
        return dados_token
    except JWTError:
        raise credentials_exception