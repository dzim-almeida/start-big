# ---------------------------------------------------------------------------
# ARQUIVO: empresa.py
# DESCRIÇÃO: Define os endpoints (rotas) da API para operações CRUD
#            relacionadas a Empresas (Multi-tenancy).
#            Rotas base: /empresas
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, File, Path, UploadFile, status
from sqlalchemy.orm import Session

# Importa os schemas necessários para entrada (Create) e saída (Read)
from app.schemas.empresa import EmpresaCreate, EmpresaRead
# Importa as dependências de sessão e transação
from app.core.depends import get_db, _handle_db_transaction
# Importa a camada de serviço que contém a lógica de negócio
from app.services import empresa as enterprise_service


# Cria um roteador específico. Assume que a URL base é /empresas
router = APIRouter()

# ===============================================
# Endpoint 1: Criar Empresa (Sign Up) (POST /)
# ===============================================
@router.post(
    "/",
    response_model=EmpresaRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria a empresa responsável pelo PDV (Processo de Sign Up)"
)
def create_enterprise(
    payload: EmpresaCreate,
    db: Session = Depends(get_db)
):
    """
    Cadastra uma nova **Empresa (Loja)** no sistema, incluindo o **Usuário Master**
    e o(s) **Endereço(s)** inicial(is) em uma única transação.
    
    * **payload**: Dados da empresa + Dados do usuário master inicial.
    * **Retorno**: Objeto Empresa criado com ID.
    * **Exceções**: Retorna 409 Conflict em caso de CNPJ ou E-mail do usuário duplicado.
    
    A transação é gerenciada para garantir a atomicidade (Tudo ou Nada).
    """
    # Chama o serviço de criação de empresa dentro do gerenciador de transação
    return _handle_db_transaction(
        db,
        enterprise_service.create_enterprise,
        payload
    )

# ===============================================
# Endpoint 2: Adicionar Imagem à Empresa (POST /{id}/imagem)
# ===============================================
@router.post(
    "/{empresa_id}/imagem/",
    response_model=EmpresaRead,
    status_code=status.HTTP_201_CREATED,
    summary="Adiciona/Atualiza uma imagem de perfil/logo para a empresa"
)
def create_image_empresa(
    # ID da empresa, obtido da URL (Path Parameter)
    empresa_id: int = Path(
        ...,
        description="ID da empresa a receber a imagem"
    ),
    # Arquivo de imagem, obtido do corpo da requisição (Form-Data)
    file: UploadFile = File(
        ...,
        description="Imagem em arquivo (e.g., JPEG, PNG)"
    ),
    db: Session = Depends(get_db)
):
    """
    Faz o upload de um arquivo e o associa como imagem da empresa.
    """
    # Chama o serviço de criação/associação de imagem
    return _handle_db_transaction(
        db,
        enterprise_service.create_image_empresa,
        empresa_id,
        file
    )