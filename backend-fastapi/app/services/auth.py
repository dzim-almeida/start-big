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
from app.core.config import settings
from app.services import usuario
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
    usuario_in_db = usuario.get_usuario_by_email(db, login_usuario.email)

    # 2. Validação de Credenciais (REGRA 4: Segurança/Robustez)
    # A verificação de `usuario_in_db` deve ocorrer antes de tentar acessar `usuario_in_db.senha_hash`
    if not usuario_in_db or not verify_password(login_usuario.senha, usuario_in_db.senha_hash):
        raise UNAUTHORIZED_EXCE
    
    # 3. Definição de Cargo e Permissões (Lógica de Negócio)
    position_name = "Master"
    permission = {"all": True} # Default para Master
    
    if not usuario_in_db.is_master:
        # Assumindo que a relação 'funcionario' está carregada no modelo ORM (lazy loading)
        # É uma boa prática usar `is not None` para checar Optional/None.
        if usuario_in_db.funcionario is not None and usuario_in_db.funcionario.cargo is not None:
            position_name = usuario_in_db.funcionario.cargo.nome
            # Garante que `permissoes` seja um dicionário, mesmo que seja None no banco.
            permission = usuario_in_db.funcionario.cargo.permissoes or {}
        else:
            position_name = "Sem cargo"
            permission = {}

    # 4. Criação do Payload (Claims)
    data_to_token = {
        "sub": str(usuario_in_db.id),
        "empresa_id": usuario_in_db.empresa_id, # Já é Optional[int] no modelo
        "ativo": usuario_in_db.ativo,
        "is_master": usuario_in_db.is_master,
        "cargo": position_name,
        "permissoes": permission
    }

    # 5. Geração do Token
    access_token = create_access_token(data=data_to_token)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    }

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