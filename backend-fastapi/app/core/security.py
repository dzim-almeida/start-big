# ---------------------------------------------------------------------------
# ARQUIVO: security.py
# DESCRIÇÃO: Contém funções utilitárias para operações de segurança, como
#            geração e verificação de senhas e tokens JWT.
# ---------------------------------------------------------------------------

import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import HTTPException, status
from jose import jwt, JWTError

from app.core.config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se uma senha em texto plano corresponde a um hash de senha.

    Args:
        plain_password (str): A senha enviada pelo usuário.
        hashed_password (str): A senha armazenada no banco de dados (hash).

    Returns:
        bool: True se a senha for válida, False caso contrário.
    """
    password_bytes = plain_password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_password_bytes)

def hash_password(password: str) -> str:
    """
    Gera um hash seguro para uma senha em texto plano usando bcrypt.

    Args:
        password (str): A senha a ser "hasheada".

    Returns:
        str: O hash da senha, pronto para ser armazenado no banco de dados.
    """
    password_bytes = password.encode('utf-8')
    # O salt é gerado e incluído no hash final. Rounds=12 é um bom custo-benefício.
    hashed_bytes = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12))
    return hashed_bytes.decode('utf-8')

def create_access_token(data: dict) -> str:
    """
    Cria um token de acesso JWT (JSON Web Token).

    Args:
        data (dict): Os dados a serem incluídos no "payload" do token (ex: id do usuário).

    Returns:
        str: O token JWT codificado como uma string.
    """
    to_encode = data.copy()

    # Adiciona um ID único ao token (JTI - JWT ID), útil para revogação de tokens.
    to_encode.update({"jti": str(uuid.uuid4())})

    # Define o tempo de expiração do token a partir das configurações.
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    # Codifica o token usando a chave secreta e o algoritmo definidos nas configurações.
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token_data(token: str) -> dict:
    """
    Decodifica e valida um token JWT, retornando seu payload se for válido.

    Args:
        token (str): O token JWT recebido na requisição.

    Raises:
        HTTPException: Lança uma exceção 401 Unauthorized se o token for
                       inválido, expirado ou se o payload estiver malformado.

    Returns:
        dict: O payload (dados) do token decodificado.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # O campo 'sub' (subject) é o padrão para identificar o dono do token.
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        return payload
        
    except JWTError:
        # Se ocorrer qualquer erro na decodificação, o token é inválido.
        raise credentials_exception