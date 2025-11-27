# ---------------------------------------------------------------------------
# ARQUIVO: services/empresa.py
# DESCRIÇÃO: Camada de serviço com a lógica de negócio para Empresas.
#            Gerencia o cadastro "Multi-tenancy" (Empresa + Usuário Master)
#            e o gerenciamento de arquivos (Upload de Logo).
# ---------------------------------------------------------------------------

import os
import shutil
import uuid
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from datetime import datetime

# Importa modelos
from app.db.models.empresa import Empresa as EmpresaModel
from app.db.models.usuario import Usuario as UsuarioModel

# Importa schemas
from app.schemas.empresa import EmpresaCreate

# Importa serviços e utilitários
from app.services import endereco as address_service
from app.core.security import hash_password
from app.core.enum import EntityType
from app.db.crud import empresa_crud as enterprise_crud


# Diretório base onde as imagens serão salvas
UPLOAD_BASE_DIR = "static/uploads/empresa"
# Garante que o diretório base exista (preparação do ambiente)
os.makedirs(UPLOAD_BASE_DIR, exist_ok=True)


# =========================
# Serviço: Criar Empresa (Completa - Sign Up)
# =========================
def create_enterprise(db: Session, new_enterprise: EmpresaCreate) -> EmpresaModel:
    """
    Cria a Empresa (tenant), o Usuário Master e os Endereços em uma única operação atômica.
    """
    # 1. REGRA DE NEGÓCIO: Validação de Tenancy (apenas 1 empresa cadastrada?)
    # Nota: Assumindo que este endpoint é para o cadastro inicial e único do sistema.
    enterprise_in_db = enterprise_crud.get_enterprise_in_db(db)
    if enterprise_in_db:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Empresa já cadastrada."
        )

    # 2. PREPARA E CRIA O OBJETO EMPRESA
    # Removemos 'usuario' e 'endereco' do payload para criar a Empresa primeiro
    enterprise_data = new_enterprise.model_dump(exclude={'usuario', 'endereco'})
    new_enterprise_to_db = EmpresaModel(**enterprise_data)
    # Persiste para obter o ID (Necessário para vincular Usuário e Endereço)
    new_enterprise_in_db = enterprise_crud.create_enterprise(db, new_enterprise_to_db)

    # 3. PREPARA E VINCULA O USUÁRIO MASTER
    user_data = new_enterprise.usuario.model_dump()
    password = user_data.pop("senha")
    
    new_user_to_db = UsuarioModel(
        **user_data,
        senha_hash=hash_password(password),
        empresa_id=new_enterprise_in_db.id, # Vincula à empresa recém criada
        is_master=True,               # Define como Super Admin da loja
        ativo=True,
        data_criacao=datetime.now()
    )

    # Adiciona o usuário à coleção de usuários da empresa
    new_enterprise_in_db.usuarios.append(new_user_to_db)

    # 4. PREPARA E VINCULA OS ENDEREÇOS
    if new_enterprise.endereco:
        # Reutiliza o serviço utilitário de endereço (Polimorfismo)
        address_db = address_service.address_to_db(
            id_entity=new_enterprise_in_db.id,
            type_entity=EntityType.EMPRESA, # Tipo correto para o vínculo
            address_data=new_enterprise.endereco
        )
        # Adiciona os endereços à coleção de endereços da empresa
        new_enterprise_in_db.enderecos = address_db
    
    # O objeto Empresa com todas as relações anexadas é retornado para a transação
    return new_enterprise_in_db


# =========================
# Função Utilitária: Salvar Arquivo Localmente
# =========================
def save_file_locally(file: UploadFile, empresa_id: int) -> str:
    """
    Salva o arquivo de upload (logo) no sistema de arquivos local,
    usando um UUID para garantir nome único e estruturando por pasta da empresa.
    
    Retorna a URL relativa do arquivo salvo.
    """
    # Gera um nome único mantendo a extensão original
    file_extesion = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extesion}"

    # Cria a pasta específica da empresa (se não existir)
    empresa_folder = os.path.join(UPLOAD_BASE_DIR, str(empresa_id))
    os.makedirs(empresa_folder, exist_ok=True)
    file_path = os.path.join(empresa_folder, unique_filename)
    
    # Processa o arquivo em chunks
    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    finally:
        # Garante que o stream de upload seja fechado
        file.file.close()

    # Retorna o caminho que será salvo no banco de dados (URL relativa)
    url = f"{UPLOAD_BASE_DIR}/{empresa_id}/{unique_filename}"
    return url


# =========================
# Serviço: Criar/Atualizar Imagem da Empresa
# =========================
def create_image_empresa(db: Session, empresa_id: int, file: UploadFile) -> EmpresaModel:
    """
    Busca a empresa pelo ID, salva o arquivo de imagem localmente e atualiza
    a URL da logo no objeto Empresa.
    """
    # 1. Busca a empresa
    # Nota: O get_enterprise_in_db deve ser adaptado para receber o ID
    # (Assumindo que get_enterprise_in_db busca pelo ID ou que o nome está errado)
    # Mantenho o nome original, mas o código parece ter um erro: 
    # deveria ser get_enterprise_by_id(db, empresa_id) para buscar pelo ID do parâmetro.
    empresa_in_db = enterprise_crud.get_enterprise_in_db(db)

    if not empresa_in_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada."
        )
    
    # 2. Salva o arquivo e obtém a URL
    img_url = save_file_locally(file=file, empresa_id=empresa_id)

    # 3. Atualiza o objeto ORM em memória
    empresa_in_db.url_logo = img_url

    # O objeto atualizado é retornado e será persistido pela transação
    return empresa_in_db