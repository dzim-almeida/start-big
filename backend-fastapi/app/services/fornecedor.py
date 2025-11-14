# ---------------------------------------------------------------------------
# ARQUIVO: services/fornecedor.py
# DESCRIÇÃO: Camada de serviço com a lógica de negócio para Fornecedores.
#            Implementa o CRUD completo, incluindo a gestão de
#            endereços polimórficos.
# ---------------------------------------------------------------------------

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Sequence, List # Importação para type hint

# Importa os schemas Pydantic (Create para entrada, Update para modificação)
from app.schemas.fornecedor import FornecedorCreate, FornecedorUpdate
# Importa o modelo ORM
from app.db.models.fornecedor import Fornecedor as FornecedorModel

# Importa os Enums e serviços necessários
from app.core.enum import EntityType
from app.services import endereco as address_service
from app.db.crud import fornecedor as supplier_crud

# =========================
# Serviço: Criar Fornecedor
# =========================
def create_supplier(db: Session, supplier: FornecedorCreate) -> FornecedorModel:
    """
    Serviço para criar um novo Fornecedor e seus endereços associados.

    1. Valida regras de negócio (ex: CNPJ duplicado).
    2. Cria a instância de FornecedorModel (sem endereços).
    3. Persiste o fornecedor no banco (para obter o ID).
    4. Chama o serviço de endereço para criar e vincular os endereços.
    5. Retorna o fornecedor completo.
    """
    # 1. REGRA DE NEGÓCIO: Verificar se o CNPJ/IE já existe
    validation_errors = []

    # Verifica CNPJ
    error_cnpj = supplier_crud.verify_supplier_conflict(
        db, supplier.cnpj, supplier_crud.get_supplier_by_cnpj, "CNPJ"
    )
    if error_cnpj:
        if error_cnpj == "disabled supplier":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Fornecedor desabilitado com este CNPJ. Por favor, reative o cadastro."
            )
        validation_errors.append({"campo": "cnpj", "mensagem": error_cnpj})

    # Verifica Inscrição Estadual (IE)
    error_ie = supplier_crud.verify_supplier_conflict(
        db, supplier.ie, supplier_crud.get_supplier_by_ie, "Inscrição Estadual"
    )
    if error_ie:
        validation_errors.append({"campo": "ie", "mensagem": error_ie})
    
    if validation_errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=validation_errors
        )
    
    # 2. MAPEAMENTO: Cria a instância do modelo SQLAlchemy
    supplier_to_db = FornecedorModel(
        nome=supplier.nome,
        cnpj=supplier.cnpj,
        nome_fantasia=supplier.nome_fantasia,
        ie=supplier.ie
    )

    # 3. CHAMA A CAMADA CRUD (para obter o ID)
    new_supplier_in_db = supplier_crud.create_supplier(db, supplier_to_db)

    # 4. PREPARA E VINCULA OS ENDEREÇOS
    supplier_address_to_db = address_service.address_to_db(
        new_supplier_in_db.id,
        EntityType.FORNECEDOR,
        supplier.endereco
    )

    # Vincula a lista de modelos de endereço ao fornecedor (em memória)
    new_supplier_in_db.endereco = supplier_address_to_db
    
    # 5. RETORNA O OBJETO PERSISTIDO
    return new_supplier_in_db

# =========================
# Serviço: Buscar TODOS os Fornecedores
# =========================
def get_all_suppliers(db: Session) -> Sequence[FornecedorModel]:
    """
    Busca TODOS os fornecedores cadastrados. (Apenas delega para o CRUD).
    """
    return supplier_crud.get_all_suppliers(db)

# =========================
# Serviço: Buscar Fornecedores
# =========================
def get_supplier_by_search(db: Session, supplier_search: str) -> Sequence[FornecedorModel]: # Corrigido: Usando Sequence
    """
    Busca fornecedores usando a camada CRUD.
    """
    return supplier_crud.get_supplier_by_search(db, supplier_search)

# =========================
# Serviço: Atualizar Fornecedor
# =========================
def update_supplier(db: Session, supplier_id: int, supplier: FornecedorUpdate) -> FornecedorModel:
    """
    Atualiza um fornecedor existente pelo ID.
    Aplica atualizações parciais (patch) e retorna o objeto atualizado.
    """
    
    # 1. Busca o fornecedor existente no banco pelo ID
    supplier_in_db = supplier_crud.get_supplier_by_id(db, supplier_id)
    
    # 2. Verifica se o fornecedor foi encontrado
    if not supplier_in_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fornecedor não encontrado."
        )
    
    # 3. Extrai apenas os dados enviados na requisição (para atualização parcial)
    update_supplier = supplier.model_dump(exclude_unset=True)

    # 4. Itera sobre os dados e atualiza o objeto SQLAlchemy
    for key, value in update_supplier.items():
        # Tratamento especial para o relacionamento aninhado 'endereco'
        if key == "endereco" and value is not None: # Simplificado o 'and'
            # Chama o serviço de endereço para lidar com a atualização da lista
            updated_addresses = address_service.update_address_in_db(
                supplier_in_db.endereco, # Lista de endereços do banco
                value,                    # Lista de dados de atualização do schema (o próprio 'value')
                supplier_in_db.id,
                EntityType.FORNECEDOR
            )
            supplier_in_db.endereco = updated_addresses
        else:
            # Aplica atualização para campos simples
            setattr(supplier_in_db, key, value)

    # 5. Chama o CRUD para persistir as alterações (flush + refresh)
    return supplier_crud.update_supplier(db, supplier_in_db)

# =========================
# Serviço: Ativar Fornecedor
# =========================
def active_supplier_by_id(db: Session, supplier_id: int) -> FornecedorModel: # Corrigido retorno
    """
    Serviço para ativar um Fornecedor pelo seu ID.
    """
    # 1. Busca o Fornecedor existente pelo ID
    existing_supplier = supplier_crud.get_supplier_by_id(db, supplier_id)

    # 2. Verifica se o Fornecedor foi encontrado
    if not existing_supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fornecedor não encontrado")
    
    # 3. Atualiza o objeto em memória
    existing_supplier.ativo = True

    # 4. Delega a ativação para a camada CRUD e retorna o objeto atualizado
    return supplier_crud.active_supplier_by_id(db, existing_supplier)

# =========================
# Serviço: Desativar Fornecedor
# =========================
def disable_supplier_by_id(db: Session, supplier_id: int) -> FornecedorModel: # Corrigido retorno
    """
    Serviço para desativar um Fornecedor pelo seu ID (Soft Delete).
    """
    # 1. Busca o Fornecedor existente pelo ID
    existing_supplier = supplier_crud.get_supplier_by_id(db, supplier_id)

    # 2. Verifica se o Fornecedor foi encontrado
    if not existing_supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fornecedor não encontrado")
    
    # 3. Atualiza o objeto em memória
    existing_supplier.ativo = False

    # 4. Delega a desativação para a camada CRUD e retorna o objeto atualizado
    return supplier_crud.disable_supplier_by_id(db, existing_supplier)