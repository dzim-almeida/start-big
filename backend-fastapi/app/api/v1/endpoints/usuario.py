# ---------------------------------------------------------------------------
# ARQUIVO: endpoints/usuario_endpoint.py
# MÓDULO: Interface de API (Controller)
# DESCRIÇÃO: Rotas para gerenciamento de contas de acesso (Usuários).
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.schemas.usuario import UsuarioCreate, UsuarioRead
from app.core.depends import _handle_db_transaction
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