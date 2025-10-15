# ---------------------------------------------------------------------------
# ARQUIVO: depends.py
# DESCRIÇÃO: Define dependências reutilizáveis para os endpoints da API,
#            como a obtenção do usuário autenticado a partir de um token.
# ---------------------------------------------------------------------------

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import verify_token_data
from app.db.crud import usuario as user_crud
from app.db.crud import token as token_crud
from app.db.session import get_db
from app.db.models.usuario import Usuario as UsuarioModel # Importar o modelo para o type hint

# Define o esquema de autenticação OAuth2.
# O 'tokenUrl' aponta para o endpoint de login que fornecerá o token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_token(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> UsuarioModel:
    """
    Dependência para ser usada em endpoints protegidos.
    1. Extrai o token da requisição.
    2. Valida o token JWT.
    3. Busca o usuário no banco de dados com base no ID do token.
    4. Retorna o objeto do usuário ou lança uma exceção HTTP 401 se falhar.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Valida o token e obtém os dados (payload)
    token_data = verify_token_data(token)

    token_jti = token_data.get("jti")

    revoke_token = token_crud.get_revoke_token(db, token_jti)

    if revoke_token:
        # Se o usuário não for encontrado (ex: foi deletado), o token é inválido.
        raise credentials_exception
    
    # Extrai o ID do usuário do payload do token ('sub' é o campo padrão)
    user_id = token_data.get("sub")

    # Busca o usuário no banco de dados
    user = user_crud.get_user_by_id(db, id=int(user_id))

    if not user:
        # Se o usuário não for encontrado (ex: foi deletado), o token é inválido.
        raise credentials_exception
        
    return token_data