# ---------------------------------------------------------------------------
# ARQUIVO: depends.py
# DESCRIÇÃO: Define dependências reutilizáveis para os endpoints da API.
# ---------------------------------------------------------------------------

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import verify_token_data
from app.db.crud import token as token_crud
from app.db.crud import usuario as user_crud
from app.db.models.usuario import Usuario as UsuarioModel
from app.db.session import get_db

# Define o esquema de autenticação OAuth2.
# O 'tokenUrl' aponta para o endpoint de login que fornecerá o token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_token(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> dict:
    """
    Dependência para validar um token e obter seu payload.

    Fluxo de execução:
    1. Extrai e decodifica o token JWT da requisição.
    2. Verifica se o 'jti' (ID do token) está na blocklist de tokens revogados.
       Se estiver, nega o acesso (HTTP 401).
    3. Busca o usuário no banco de dados com base no 'sub' (ID do usuário) do token.
       Se o usuário não existir, nega o acesso (HTTP 401).
    4. Retorna o payload (dicionário de dados) do token se tudo for válido.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Valida a assinatura e a expiração do token, e obtém seus dados (payload).
    token_data = verify_token_data(token)

    # Extrai o identificador único (jti) do token.
    token_jti = token_data.get("jti")

    # VERIFICAÇÃO DA BLOCKLIST: Checa se o token foi revogado (logout).
    revoke_token = token_crud.get_revoke_token(db, token_jti)

    # Se o token for encontrado na blocklist, ele é inválido.
    if revoke_token:
        raise credentials_exception

    # Extrai o ID do usuário ('sub') do payload do token.
    user_id = token_data.get("sub")

    # Busca o usuário correspondente no banco de dados.
    user = user_crud.get_user_by_id(db, id=int(user_id))

    # Se o usuário dono do token não existir mais, o token é inválido.
    if not user:
        raise credentials_exception

    # Se todas as verificações passarem, retorna o payload do token.
    return token_data