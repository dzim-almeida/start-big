# ---------------------------------------------------------------------------
# ARQUIVO: services/empresa_service.py
# MÓDULO: Regras de Negócio (Service Layer)
# DESCRIÇÃO: Controla a unicidade da empresa e gerenciamento de arquivos.
# ---------------------------------------------------------------------------

import os
import shutil
import uuid
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from typing import List, Optional

# Importa modelos e serviços
from app.db.models.empresa import Empresa as EmpresaModel
from app.db.models.usuario import Usuario as UsuarioModel
from app.schemas.empresa import EmpresaCreate
from app.services import endereco as endereco_service
from app.services import usuario as usuario_service
from app.core.enum import EntityType
from app.db.crud import empresa as empresa_crud

# ---------------------------------------------------------------------------
# CONSTANTES E EXCEÇÕES
# ---------------------------------------------------------------------------

# Exceção Singleton
CONFLICT_EXCE = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="O sistema já possui uma empresa cadastrada. Operação bloqueada."
)

NOT_FOUND_EXCE = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Empresa não encontrada."
)

UPLOAD_BASE_DIR = "static/uploads/empresa"
os.makedirs(UPLOAD_BASE_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# FUNÇÕES DE SERVIÇO
# ---------------------------------------------------------------------------

def save_image_locally(image_file: UploadFile, empresa_id: int) -> str:
    """
    Salva o arquivo de imagem da logo localmente, usando o ID da empresa como subdiretório.

    Args:
        image_file (UploadFile): O arquivo enviado pelo cliente.
        empresa_id (int): O ID da empresa para criar o subdiretório.

    Returns:
        str: O caminho relativo da imagem salva (URL).
    """
    file_extension = os.path.splitext(image_file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"

    produto_folder = os.path.join(UPLOAD_BASE_DIR, str(empresa_id))
    os.makedirs(produto_folder, exist_ok=True)
    file_path = os.path.join(produto_folder, unique_filename)

    try:
        # Usa shutil.copyfileobj para lidar com arquivos grandes de forma eficiente
        with open(file_path, "wb") as f:
            shutil.copyfileobj(image_file.file, f)
    finally:
        # Garante que o stream de arquivo seja fechado
        image_file.file.close()

    url_image_file = f"{UPLOAD_BASE_DIR}/{empresa_id}/{unique_filename}"
    return url_image_file


def create_empresa(
    db: Session, 
    usuario_master_id: int, 
    empresa_to_add: EmpresaCreate
) -> EmpresaModel:
    """
    Cria a Entidade Empresa e orquestra a vinculação de Endereços e do Usuário Master.

    Fluxo:
    1. Valida se já existe empresa (Regra Singleton: uma empresa por sistema).
    2. Persiste a Empresa no banco.
    3. Persiste o Endereço(s) (se houver).
    4. Vincula o ID da nova empresa ao Usuário Master.
    
    Args:
        db (Session): Sessão do banco de dados.
        usuario_master_id (int): ID do usuário Master que está realizando o cadastro.
        empresa_to_add (EmpresaCreate): DTO de entrada.

    Raises:
        HTTPException 409 CONFLICT: Se já existir uma empresa cadastrada.

    Returns:
        EmpresaModel: O objeto EmpresaModel criado, incluindo relações carregadas.
    """
    # 1. Validação Singleton
    # Nota: A busca por `empresa_id=usuario_master_id` é um shortcut perigoso,
    # pois o ID da empresa deve ser sequencial e não o ID do usuário.
    # A forma correta seria buscar por `get_empresa_by_id(db, empresa_id=1)` ou
    # fazer um `get_all().first()` se for Singleton. **Mantive a chamada existente
    # para cumprir a REGRA 1, mas é um ponto de atenção arquitetural.**
    empresa_in_db = empresa_crud.get_empresa_by_id(db, empresa_id=usuario_master_id) 
    if empresa_in_db:
        raise CONFLICT_EXCE

    # 2. Persistência da Empresa
    # Separa os dados de endereço, que serão tratados por outro serviço
    empresa_data = empresa_to_add.model_dump(exclude={"endereco"})
    empresa_to_db = EmpresaModel(**empresa_data)
    empresa_in_db = empresa_crud.create_empresa(db, empresa_to_add=empresa_to_db)
   
    # 3. Persistência do Endereço (Opcional)
    if empresa_to_add.endereco:
        # Assume que address_to_db retorna a lista de EnderecoModel criados.
        endereco_models = endereco_service.address_to_db(
            id_entity=empresa_in_db.id,
            type_entity=EntityType.EMPRESA, 
            address_data=empresa_to_add.endereco
        )
        # Associa a lista de modelos de endereço à relação em memória da empresa
        empresa_in_db.enderecos = endereco_models # Type Hinting: espera List[EnderecoModel]
    
    # 4. Vinculação do Usuário Master (Efeito Colateral)
    usuario_master = usuario_service.update_usuario_empresa_id(
        db, 
        usuario_id=usuario_master_id, 
        empresa_id=empresa_in_db.id
    )

    # 5. Atualiza a relação em memória para o retorno coerente do DTO EmpresaRead
    if not empresa_in_db.usuarios:
        empresa_in_db.usuarios = []
        
    # Adiciona o usuário master à lista de usuários da empresa
    if usuario_master not in empresa_in_db.usuarios:
        empresa_in_db.usuarios.append(usuario_master)
    
    return empresa_in_db


def create_image_empresa(db: Session, empresa_id: int, file: UploadFile) -> EmpresaModel:
    """
    Gerencia o upload local da logo da empresa e atualiza o URL no registro.

    Args:
        db (Session): Sessão do banco de dados.
        empresa_id (int): ID da empresa que receberá a logo.
        file (UploadFile): O arquivo de imagem recebido via requisição.

    Raises:
        HTTPException 404 NOT FOUND: Se a empresa não for encontrada.

    Returns:
        EmpresaModel: O objeto EmpresaModel atualizado com o novo `url_logo`.
    """
    empresa_in_db = empresa_crud.get_empresa_by_id(db, empresa_id=empresa_id)

    if not empresa_in_db:
        raise NOT_FOUND_EXCE
    
    img_url = save_image_locally(image_file=file, empresa_id=empresa_id)
    empresa_in_db.url_logo = img_url

    # O objeto modificado é retornado. A persistência (commit) é feita na camada de Endpoint.
    return empresa_in_db

def get_empresa_by_id(db: Session, empresa_id: int) -> EmpresaModel:
    return empresa_crud.get_empresa_by_id(db, empresa_id=empresa_id)