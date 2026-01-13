# ---------------------------------------------------------------------------
# ARQUIVO: endpoints/usuario_endpoint.py
# MÓDULO: Interface de API (Controller)
# DESCRIÇÃO: Rotas para gerenciamento de contas de acesso (Usuários).
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, File, status, UploadFile
from sqlalchemy.orm import Session

from app.schemas.usuario import UsuarioCreate, UsuarioRead
from app.core.depends import get_current_user, _handle_db_transaction
from app.db.session import get_db
from app.services import usuario as usuario_service

router = APIRouter()

# ===========================================================================
# ROTAS DE CRIAÇÃO (POST)
# ===========================================================================

@router.post(
    "/",
    response_model=UsuarioRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar Usuário Master",
    description="Endpoint exclusivo para o Setup Inicial. Cria o primeiro administrador do sistema."
)
def create_usuario_master(
    usuario_master_to_add: UsuarioCreate,
    db: Session = Depends(get_db)
):
    """
    Cria o Usuário Master (Admin) do sistema.
    
    Regra de Negócio:
    - Este endpoint deve ser usado apenas na instalação do sistema (Onboarding).
    - O serviço validará se já existe um Master cadastrado para evitar duplicidade.
    
    Args:
        usuario_master_to_add (UsuarioCreate): Payload com email, senha e nome.
        db (Session): Sessão de banco de dados.

    Returns:
        UsuarioRead: O usuário criado (sem a senha hashada).
    """
    return _handle_db_transaction(
        db,
        usuario_service.create_usuario,
        usuario_master_to_add,
        empresa_id=None, # Master inicial não tem empresa até criar uma
        is_master=True   # Flag que ativa a regra de unicidade de Master
    )

@router.post(
    "/imagem",
    response_model=UsuarioRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma nova imagem de usuario"
)
def create_image_usuario(
    user_token: dict = Depends(get_current_user),
    img_file: UploadFile = File(
        ...,
        description="Arquivo de Imagem (JPEG, PNG)"
    ), 
    db: Session = Depends(get_db)
):
    return _handle_db_transaction(
        db,
        usuario_service.create_image_usuario,
        user_token.get("sub"),
        img_file
    )

@router.get(
    "/me",
    response_model=UsuarioRead,
    status_code=status.HTTP_200_OK,
    summary="Retorna dados do usuario"
)
def get_usuario_me(
    token_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return _handle_db_transaction(
        db,
        usuario_service.get_usuario_me_by_id,
        token_user.get("sub"),
    )
    