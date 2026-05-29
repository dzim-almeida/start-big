# ---------------------------------------------------------------------------
# ARQUIVO: app/services/auth_service.py
# DESCRIÇÃO: Lógica de Login e Logout, geração e revogação de tokens.
# ---------------------------------------------------------------------------

from typing import Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.schemas.auth import UsuarioLogin
from app.core.security import verify_password, create_access_token
from app.services import usuario as usuario_service
from app.db.crud import token as token_crud
from app.db.models.token import TokenBlocklist

# ---------------------------------------------------------------------------
# EXCEÇÃO PADRONIZADA
# ---------------------------------------------------------------------------

UNAUTHORIZED_EXCE = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Email ou senha incorretos",
    headers={"WWW-Authenticate": "Bearer"},
)

# ---------------------------------------------------------------------------
# FUNÇÕES DE SERVIÇO
# ---------------------------------------------------------------------------

def login(db: Session, login_usuario: UsuarioLogin) -> Dict[str, Any]:
    """
    Autentica o usuário, verifica a senha e gera o token de acesso (JWT).

    Args:
        db (Session): Sessão do banco de dados.
        login_usuario (UsuarioLogin): DTO com email e senha em texto plano.

    Raises:
        HTTPException 401 UNAUTHORIZED: Se o e-mail ou a senha estiverem incorretos.

    Returns:
        Dict[str, Any]: Dicionário contendo o access_token, token_type e expires_in.
    """
    # 1. Busca Usuário
    usuario_in_db = usuario_service.get_usuario_by_email(db, login_usuario.email)

    # 2. Validação de Credenciais (REGRA 4: Segurança/Robustez)
    # A verificação de `usuario_in_db` deve ocorrer antes de tentar acessar `usuario_in_db.senha_hash`
    if not usuario_in_db or not verify_password(login_usuario.senha, usuario_in_db.senha_hash):
        raise UNAUTHORIZED_EXCE
    

    # 4. Criação do Payload (Claims)
    token_data = {
        "sub": str(usuario_in_db.id),
    }

    # 5. Geração do Token
    access_token = create_access_token(data=token_data)

    return access_token

def logout_service(db: Session, token: Dict[str, Any]) -> None:
    """
    Revoga o token JWT, adicionando seu JTI (ID) à Blocklist.

    Args:
        db (Session): Sessão do banco de dados.
        token (Dict[str, Any]): O payload decodificado do token, contendo 'jti' (ID) e 'exp' (expiração).

    Returns:
        None: A operação é concluída ou falha silenciosamente.
    """
    jti = token.get("jti")
    exp = token.get("exp")
    
    if jti and exp:
        # Converte o timestamp de expiração (UTC) para datetime
        exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)
        
        # Cria o modelo para persistência
        revoke_token = TokenBlocklist(jti=jti, exp=exp_datetime)
        
        # Persiste a revogação (o CRUD deve fazer o flush/commit)
        token_crud.create_revoke_token(db, revoke_token)