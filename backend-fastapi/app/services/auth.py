# ---------------------------------------------------------------------------
# ARQUIVO: auth.py (dentro da pasta services)
# DESCRIÇÃO: Módulo responsável pela lógica de negócio da autenticação,
#            como a validação de credenciais e a geração de tokens de acesso.
# ---------------------------------------------------------------------------

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Dict # Import adicionado para tipagem mais clara do retorno

# Importa o schema Pydantic para os dados de login.
from app.schemas.auth import UsuarioLogin
# Importa o models SQLAlchemy para os tokens revogados.
from app.db.models.token import TokenBlocklist
# Importa as funções de segurança para verificar senha e criar token.
from app.core.security import verify_password, create_access_token
# Importa a variável de EXPIRE_TOKEN
from app.core.config import settings
# Importa as funções de acesso ao banco de dados para usuários e tokens.
from app.db.crud import usuario as user_crud
from app.db.crud import token as token_crud


# =========================
# Serviço: Login
# =========================
def login_service(db: Session, user_data: UsuarioLogin) -> Dict[str, str | int]:
    """
    Valida as credenciais de um usuário e gera um token de acesso.

    Args:
        db (Session): A sessão do banco de dados.
        user_data (UsuarioLogin): Os dados de login (email e senha).

    Raises:
        HTTPException: Lança um erro 401 se as credenciais forem inválidas.

    Returns:
        dict: Um dicionário contendo o token de acesso e informações relacionadas.
    """
    # 1. Busca o usuário no banco de dados pelo e-mail fornecido.
    user = user_crud.get_user_by_email(db, email=user_data.email)

    # 2. Verifica se o usuário existe E se a senha fornecida corresponde ao hash salvo.
    if not user or not verify_password(user_data.senha, user.senha_hash):
        # Se a validação falhar, lança uma exceção de "Não Autorizado".
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos",
            # O header 'WWW-Authenticate' é uma boa prática para esquemas de autenticação Bearer.
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Prepara o payload (os dados) que serão incluídos dentro do token.
    data_to_token = {
        "sub": str(user.id),      # 'sub' (subject) é o padrão para identificar o dono do token.
        # Informações adicionais podem ser incluídas aqui, como 'empresa_id' ou 'cargos'.
    }

    # 4. Cria o token JWT usando a função de segurança.
    access_token = create_access_token(data=data_to_token)
    
    # 5. Retorna o token no formato esperado pelo padrão OAuth2.
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60) # Tempo em segundos
    }


# =========================
# Serviço: Logout
# =========================
def logout_service(db: Session, token: Dict[str, str | int]) -> None:
    """
    Prepara e solicita a adição de um token à blocklist.
    
    Args:
        db (Session): A sessão do banco de dados.
        token (dict): O payload do token JWT decodificado (contém 'jti' e 'exp').
    """
    # 1. Extrai o 'jti' (ID único do token) e 'exp' (timestamp de expiração) do payload.
    jti = token.get("jti")
    exp = token.get("exp")

    # 2. Converte o timestamp de expiração (Unix epoch) para um objeto datetime ciente do fuso horário.
    exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)

    # 3. Cria a instância do modelo SQLAlchemy para a blocklist.
    revoke_token = TokenBlocklist(
        jti=jti,
        exp=exp_datetime
    )

    # 4. Chama a função CRUD para adicionar o token à sessão do banco de dados.
    # O commit final será realizado na camada de endpoint/transação.
    token_crud.create_revoke_token(db, revoke_token)