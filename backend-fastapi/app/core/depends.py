# ---------------------------------------------------------------------------
# ARQUIVO: depends.py
# DESCRIÇÃO: Define dependências reutilizáveis para os endpoints da API,
#            incluindo autenticação, autorização (permissão) e transação DB.
# ---------------------------------------------------------------------------

from typing import Callable, Dict
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import verify_token_data
from app.db.crud import token as token_crud
from app.db.crud import usuario as user_crud
from app.db.session import get_db
from app.db.models.usuario import Usuario as UsuarioModel

# Define o esquema de autenticação OAuth2.
# O 'tokenUrl' aponta para o endpoint de login.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# =========================
# Dependência 1: Obter e Validar Token (Autenticação)
# =========================

def get_token(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> UsuarioModel:
    """
    Dependência que valida o JWT, verifica a blocklist e busca o Usuário no BD.

    Retorna o objeto UsuarioModel se o token for válido e o usuário existir.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. Valida a assinatura e expiração do token, e obtém os dados.
    token_data = verify_token_data(token)

    # 2. Extrai o JTI (JWT ID) para verificação da blocklist.
    token_jti = token_data.get("jti")

    # 3. VERIFICAÇÃO DA BLOCKLIST: Checa se o token foi revogado.
    revoke_token = token_crud.get_revoke_token(db, token_jti)
    if revoke_token:
        raise credentials_exception

    # 4. Extrai o ID do usuário ('sub').
    user_id = token_data.get("sub")

    # 5. Busca o usuário correspondente no banco de dados.
    # Nota: O retorno é o objeto UsuarioModel, e não apenas o payload do token.
    user = user_crud.get_user_by_id(db, id=int(user_id))

    # 6. Se o usuário não existir (ex: deletado após o token), nega.
    if not user:
        raise credentials_exception

    return user

# =========================
# Dependência 2: Obter Usuário Ativo
# =========================

def get_current_user(
    usuario_in_db: UsuarioModel = Depends(get_token)
) -> UsuarioModel:
    """
    Garante que o usuário autenticado esteja ativo.
    """
    inactive_user_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Usuário inativo. O acesso foi revogado.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not usuario_in_db.ativo:
        # Se inativo, lança a exceção e nega o acesso
        raise inactive_user_exception
    
    return usuario_in_db

def get_current_active_user(
    current_user: UsuarioModel = Depends(get_current_user)
) -> UsuarioModel:
    """Dependência padrão que garante usuário autenticado e ativo."""
    return current_user

# =========================
# Dependência 3: Verificação de Usuário Master
# =========================

def get_current_master_user(
    current_user: UsuarioModel = Depends(get_current_user)
) -> UsuarioModel:
    """Garante que o usuário logado é o Master da empresa (Super Admin da loja)."""
    if not current_user.is_master:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Apenas o usuário Master pode realizar esta ação.",
        )
    return current_user

# =========================
# Dependência 4: Verificação de Permissão (Autorização)
# =========================

def check_permission(required_permission: str) -> Callable[[UsuarioModel], Dict[str, int]]:
    """
    Cria uma dependência que verifica se o usuário possui a permissão necessária
    através da sua relação com Funcionário -> Cargo (JSON de Permissões).
    """
    def permission_dependency(
        current_user: UsuarioModel = Depends(get_current_active_user)
    ) -> Dict[str, int]:

        # REGRA DE MESTRE: O Master User tem todas as permissões.
        if current_user.is_master:
            return {
                "user_id": current_user.id,
                "empresa_id": current_user.empresa_id,
            }
        
        # 1. Acesso ao Funcionario (garantir relação 1:1)
        # Nota: Assume-se que o modelo Usuario tem o atributo `funcionario` (backref/relationship).
        funcionario = current_user.funcionario 
        if not funcionario:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuário sem vínculo de funcionário.")

        # 2. Acesso ao Cargo
        cargo = funcionario.cargo
        if not cargo:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Funcionário sem cargo atribuído.")
        
        # 3. Verificação da Permissão no JSON do Cargo
        # Nota: Assume-se que Cargo.permissoes é um campo JSON/Dict com chaves booleanas.
        permissoes = cargo.permissoes
        
        # Checa se a chave da permissão requerida existe e se o valor é True.
        if permissoes.get(required_permission, False) is True:
            # Retorna o user_id e empresa_id para a camada de serviço (Multi-tenancy)
            return {
                "user_id": current_user.id,
                "empresa_id": current_user.empresa_id,
            }

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Acesso negado. Requer permissão de '{required_permission}'.",
        )
    
    return permission_dependency

# =========================
# Função Utilitária: Gerenciador de Transação (Core)
# =========================

def _handle_db_transaction(db: Session, func: Callable, *args, **kwargs):
    """
    Executa a lógica de serviço, gerencia o commit/rollback e trata as exceções.

    Args:
        db (Session): Sessão do banco de dados (injetada).
        func (Callable): A função de serviço a ser executada.
        *args, **kwargs: Argumentos a serem passados para a função de serviço.
    
    Retorno: O resultado da função de serviço.
    """
    try:
        # 1. Executa o serviço (onde ocorre a lógica de negócio e manipulação do ORM)
        result = func(db, *args, **kwargs)
        # 2. Se o serviço for bem-sucedido, commita a transação
        db.commit()
        return result
    except HTTPException as http_exce:
        # 3. Trata erros de negócio controlados (404, 409, 403)
        print(f"Erro de negócio: {http_exce.detail}")
        db.rollback()
        raise http_exce
    except ValueError as e:
        # 4. Captura erros de validação de negócio (lançados por serviços)
        print(f"Erro de validação: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        # 5. Trata erros inesperados (internos)
        print(f"Erro inesperado: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro interno no servidor."
        )