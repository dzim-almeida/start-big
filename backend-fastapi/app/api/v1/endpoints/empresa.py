# ---------------------------------------------------------------------------
# ARQUIVO: endpoints/empresa.py
# MÓDULO: Interface de API (Controller)
# DESCRIÇÃO: Gerencia o ciclo de vida da entidade Empresa (Tenant).
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, File, Path, UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.schemas.empresa import EmpresaCreate, EmpresaRead
from app.db.models.usuario import Usuario as UsuarioModel
from app.core.depends import get_current_master_user, _handle_db_transaction
from app.db.session import get_db
from app.services import empresa as empresa_service


router = APIRouter()


@router.post(
    "/",
    response_model=EmpresaRead,
    status_code=status.HTTP_201_CREATED,
    summary="Inicializar Empresa (Setup)",
    description="Cria a empresa única do sistema e vincula o usuário Master logado a ela."
)
def create_empresa(
    usuario_master: dict = Depends(get_current_master_user),
    *,
    empresa_to_add: EmpresaCreate,
    db: Session = Depends(get_db)
):
    """
    Realiza o cadastro da empresa (Tenant) no banco de dados.
    
    Regras:
    1. Requer um usuário Master autenticado.
    2. Só permite o cadastro se não houver nenhuma empresa registrada (Singleton).
    3. Vincula automaticamente o usuário logado como pertencente a essa empresa.

    Args:
        usuario_master (dict): Payload do token do Usuário Master (contém 'sub'/ID).
        empresa_to_add (EmpresaCreate): Payload com dados da empresa e endereço.
        db (Session): Sessão de banco de dados.

    Returns:
        EmpresaRead: Dados da empresa criada.
    """
    # A ID do usuário Master é extraída do token (campo 'sub')
    usuario_master_id = int(usuario_master.get("sub"))
    
    return _handle_db_transaction(
        db,
        empresa_service.create_empresa,
        usuario_master_id,
        empresa_to_add
    )

@router.post(
    "/imagem/",
    response_model=EmpresaRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload de Logomarca",
    description="Armazena a imagem enviada e atualiza a URL da logo da empresa."
)
def create_image_empresa(
    usuario_master: dict = Depends(get_current_master_user),
    file: UploadFile = File(..., description="Arquivo de imagem (JPEG, PNG)"),
    db: Session = Depends(get_db)
):
    """
    Endpoint para upload de branding da empresa.
    
    Args:
        usuario_master (dict): Payload do token do Usuário Master (contém 'empresa_id').
        file (UploadFile): O arquivo de imagem enviado.
        db (Session): Sessão de banco de dados.

    Returns:
        EmpresaRead: Dados da empresa atualizada.
    """
    # FIX/Ajuste: Deve-se passar o empresa_id e não o sub (usuario_id)
    empresa_id: Optional[int] = usuario_master.get("empresa_id")

    if not empresa_id:
        # Se o Master não tiver empresa_id no token, significa que a empresa não foi criada
        # ou o token está desatualizado. Levanta uma exceção (404/400).
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O ID da Empresa não está presente no token de acesso. Crie a empresa primeiro."
        )

    return _handle_db_transaction(
        db,
        empresa_service.create_image_empresa,
        empresa_id, # Passa o ID da empresa do token
        file
    )