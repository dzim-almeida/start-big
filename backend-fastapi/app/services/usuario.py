# ---------------------------------------------------------------------------
# ARQUIVO: services/usuario_service.py
# MÓDULO: Regras de Negócio (Service Layer)
# DESCRIÇÃO: Lógica de autenticação, hashing de senhas e regras de criação.
# ---------------------------------------------------------------------------

import os
import shutil
import uuid
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.orm import Session
from typing import Optional

from app.db.models.usuario import Usuario as UsuarioModel
from app.schemas.usuario import UsuarioRead
from app.schemas.usuario import UsuarioCreate
from app.core.security import hash_password
from app.db.crud import usuario as usuario_crud

# ---------------------------------------------------------------------------
# CONSTANTES
# ---------------------------------------------------------------------------

UPLOAD_BASE_DIR = "static/uploads/usuarios"

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
def save_image_locally(img_file: UploadFile, usuario_id: int) -> str:
    file_extension = os.path.splitext(img_file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"

    produto_folder = os.path.join(UPLOAD_BASE_DIR, str(usuario_id))
    os.makedirs(produto_folder, exist_ok=True)
    file_path = os.path.join(produto_folder, unique_filename)

    try:
        with open(file_path, 'wb') as f:
            shutil.copyfileobj(img_file.file, f)
    finally:
        img_file.file.close()

    url_image_file = f"{UPLOAD_BASE_DIR}/{usuario_id}/{unique_filename}"
    return url_image_file


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
    )

    # 4. Persistência
    return usuario_crud.create_user(db, usuario_to_add=usuario_to_db)

def create_image_usuario(db: Session, usuario_id: int, img_file: UploadFile) -> UsuarioModel:
    
    usuario_in_db = usuario_crud.get_usuario_by_id(db, usuario_id=usuario_id)

    if not usuario_in_db:
        raise _get_not_found_exception
    
    saved_file_url = save_image_locally(
        img_file=img_file,
        usuario_id=usuario_in_db.id
    )
    
    usuario_in_db.url_perfil = saved_file_url
    return usuario_in_db

def get_usuario_me_by_id(db: Session, usuario_id: int) -> UsuarioRead:
    
    usuario_in_db = usuario_crud.get_usuario_by_id(db, usuario_id=usuario_id)

    if not usuario_in_db:
        raise _get_not_found_exception
    
    if (usuario_in_db.is_master):
        cargo_data = {
            "nome": "Master",
            "permissoes": {"all": True}
        }
    elif (usuario_in_db.funcionario is not None and usuario_in_db.funcionario.cargo is not None):
        cargo_data = usuario_in_db.funcionario.cargo
    else:
        cargo_data = {
            "nome": "Sem cargo atribuído",
            "permissoes": {}
        }

    return UsuarioRead(
        id=usuario_in_db.id,
        nome=usuario_in_db.nome,
        email=usuario_in_db.email,
        url_perfil=usuario_in_db.url_perfil,
        ativo=usuario_in_db.ativo,
        empresa=usuario_in_db.empresa,
        cargo=cargo_data
    )


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
    return usuario_crud.get_usuario_by_id(db, usuario_id=usuario_id)

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