# ---------------------------------------------------------------------------
# ARQUIVO: services/usuario_service.py
# MÓDULO: Regras de Negócio (Service Layer)
# DESCRIÇÃO: Lógica de autenticação, hashing de senhas e regras de criação.
# ---------------------------------------------------------------------------

from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.db.models.usuario import Usuario as UsuarioModel
from app.schemas.usuario import UsuarioCreate
from app.core.security import hash_password
from app.db.crud import usuario as usuario_crud

# ---------------------------------------------------------------------------
# EXCEÇÕES CONTEXTUALIZADAS (REGRA 4: Robustez)
# ---------------------------------------------------------------------------

def _get_not_found_exception(detail: str = "Usuário não encontrado no sistema") -> HTTPException:
    """Gera uma exceção 404 padronizada."""
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=detail
    )

def _get_conflict_exception(detail: str = "Email de usuário já cadastrado no sistema") -> HTTPException:
    """Gera uma exceção 409 padronizada."""
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=detail
    )

# ---------------------------------------------------------------------------
# FUNÇÕES DE SERVIÇO
# ---------------------------------------------------------------------------

def create_usuario(
    db: Session, 
    usuario_to_add: UsuarioCreate, 
    empresa_id: Optional[int] = None, 
    is_master: bool = False
) -> UsuarioModel:
    """
    Cria um novo usuário com senha criptografada.

    Regras de Negócio:
    1. Se is_master=True, verifica se já existe algum Master no sistema (Regra Singleton de Master).
    2. Se is_master=False, verifica apenas duplicidade de e-mail.
    3. Gera o hash da senha antes de persistir.

    Args:
        db (Session): Sessão do banco de dados.
        usuario_to_add (UsuarioCreate): DTO de entrada com dados do usuário (inclui senha em texto plano).
        empresa_id (Optional[int]): ID da empresa vinculada.
        is_master (bool): Define se o usuário é o superusuário/Master da instalação.

    Raises:
        HTTPException 409 CONFLICT: Se o email já existir ou se tentar criar um segundo Master.

    Returns:
        UsuarioModel: O objeto UsuarioModel persistido no banco.
    """
    # 1. Validação de Conflitos
    if is_master:
        # Verifica a Regra Singleton do Master (o CRUD já faz a busca exata)
        if usuario_crud.get_usuario_master(db):
            raise _get_conflict_exception(
                detail="O sistema já possui um Usuário Master cadastrado. Operação bloqueada."
            )
    
    # Validação padrão por e-mail para todos os usuários
    usuario_in_db = usuario_crud.get_usuario_by_email(db, usuario_email=usuario_to_add.email)
    if usuario_in_db:
        raise _get_conflict_exception()
    
    # 2. Preparação dos Dados e Hashing de Segurança
    usuario_data = usuario_to_add.model_dump()
    password_plain = usuario_data.pop("senha") # Remove a senha em texto plano

    hashed_password = hash_password(password_plain)

    # 3. Instanciação do Modelo
    usuario_to_db = UsuarioModel(
        **usuario_data,
        senha_hash=hashed_password, # Persiste o hash
        empresa_id=empresa_id,
        is_master=is_master,
        ativo=True,
        # Nota: O ideal é que o modelo SQLAlchemy defina o default para `data_criacao`
        data_criacao=datetime.now() 
    )

    # 4. Persistência
    return usuario_crud.create_user(db, usuario_to_add=usuario_to_db)

def get_usuario_by_id(db: Session, usuario_id: int) -> UsuarioModel:
    """
    Busca um usuário pelo ID e levanta 404 se não encontrado.

    Args:
        db (Session): Sessão do banco de dados.
        usuario_id (int): ID do usuário a ser buscado.

    Raises:
        HTTPException 404 NOT FOUND: Se o usuário não for encontrado.

    Returns:
        UsuarioModel: O objeto UsuarioModel encontrado.
    """
    usuario_in_db = usuario_crud.get_usuario_by_id(db, usuario_id=usuario_id)
    if not usuario_in_db:
        raise _get_not_found_exception()

    return usuario_in_db

def get_usuario_by_email(db: Session, usuario_email: str) -> Optional[UsuarioModel]:
    """
    Busca um usuário pelo e-mail (usado primariamente para login/autenticação).

    Args:
        db (Session): Sessão do banco de dados.
        usuario_email (str): E-mail do usuário.

    Returns:
        Optional[UsuarioModel]: O objeto UsuarioModel ou None.
    """
    # Apenas repassa a chamada para o CRUD. Mantido no Service para coerência.
    # A tipagem str | None no CRUD foi ajustada para str aqui, pois o email é 
    # tipado como obrigatório em UsuarioLogin.
    return usuario_crud.get_usuario_by_email(db, usuario_email=usuario_email)

def update_usuario_empresa_id(db: Session, usuario_id: int, empresa_id: int) -> UsuarioModel:
    """
    Vincula um usuário existente (geralmente o Master) a uma empresa (Tenant ID).
    
    Args:
        db (Session): Sessão do banco de dados.
        usuario_id (int): ID do usuário a ser atualizado.
        empresa_id (int): ID da empresa que será vinculada ao usuário.

    Raises:
        HTTPException 404 NOT FOUND: Se o usuário não for encontrado.

    Returns:
        UsuarioModel: O objeto UsuarioModel atualizado.
    """
    usuario_in_db = get_usuario_by_id(db, usuario_id=usuario_id) # Reutiliza a função de busca
    
    usuario_in_db.empresa_id = empresa_id
    
    # O objeto modificado é retornado. A persistência (commit) é feita na camada de Endpoint.
    return usuario_in_db