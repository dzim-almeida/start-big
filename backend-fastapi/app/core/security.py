# ---------------------------------------------------------------------------
# ARQUIVO: security.py
# DESCRIÇÃO: Contém funções utilitárias para operações de segurança, como
#            geração e verificação de senhas e tokens JWT.
# ---------------------------------------------------------------------------

import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict # Import adicionado

import bcrypt
from fastapi import HTTPException, status
from jose import jwt, JWTError

from app.core.config import settings

# =========================
# Funções de Hash de Senha (bcrypt)
# =========================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se uma senha em texto plano corresponde a um hash de senha (bcrypt).
    """
    password_bytes = plain_password.encode('utf-8')
    # O hash de bcrypt já contém o salt.
    hashed_password_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_password_bytes)

def hash_password(password: str) -> str:
    """
    Gera um hash seguro para uma senha em texto plano usando bcrypt.
    """
    password_bytes = password.encode('utf-8')
    # Gera o salt e o hash. Rounds=12 é um bom custo-benefício.
    hashed_bytes = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12))
    # O retorno é decodificado para string (armazenável no BD)
    return hashed_bytes.decode('utf-8')

# =========================
# Funções de Token JWT (jose)
# =========================

def create_access_token(data: Dict[str, str]) -> str:
    """
    Cria um token de acesso JWT (JSON Web Token), incluindo JTI e EXP.
    """
    to_encode = data.copy()

    # Adiciona um ID único ao token (JTI - JWT ID), útil para blocklist/revogação.
    to_encode.update({"jti": str(uuid.uuid4())})

    # Define o tempo de expiração do token.
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    # Codifica o token
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def verify_token_data(token: str) -> Dict[str, str | int]:
    """
    Decodifica e valida um token JWT, verificando assinatura e expiração.

    Raises:
        HTTPException: Se o token for inválido, expirado ou malformado.
    
    Returns:
        dict: O payload (dados) do token decodificado.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decodifica o token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        # Verifica a presença do 'sub' (ID do usuário)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        return payload
        
    except JWTError:
        # Erro genérico de JWT (expirado, assinatura inválida, etc.)
        raise credentials_exception