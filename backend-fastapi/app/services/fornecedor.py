# ---------------------------------------------------------------------------
# ARQUIVO: services/fornecedor.py
# DESCRIÇÃO: Camada de serviço com a lógica de negócio para Fornecedores.
#            Implementa o CRUD completo, incluindo a gestão de
#            endereços polimórficos.
# ---------------------------------------------------------------------------

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Sequence # Importação para type hint de lista

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
    # 1. REGRA DE NEGÓCIO: Verificar se o CNPJ já existe
    existing_supplier = supplier_crud.get_supplier_by_cnpj(db, supplier.cnpj)
    
    if existing_supplier:
        # Lança exceção se o CNPJ já estiver cadastrado
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="CNPJ já cadastrado." # Corrigido: 'cadastrado'
        )

    # 2. MAPEAMENTO: Cria a instância do modelo SQLAlchemy
    supplier_to_db = FornecedorModel(
        nome=supplier.nome,
        cnpj=supplier.cnpj,
        nome_fantasia=supplier.nome_fantasia,
        ie=supplier.ie
    )

    # 3. CHAMA A CAMADA CRUD (para obter o ID)
    # Persiste o fornecedor (add, flush, refresh)
    new_supplier_in_db = supplier_crud.create_supplier(db, supplier_to_db)

    # 4. PREPARA E VINCULA OS ENDEREÇOS (Lógica Refatorada)
    # Chama o serviço de endereço para criar as instâncias de EnderecoModel
    supplier_address_to_db = address_service.address_to_db(
        new_supplier_in_db.id, # O ID obtido do passo 3
        EntityType.FORNECEDOR, # Define o tipo da entidade
        supplier.endereco # A lista de schemas Pydantic de endereço
    )

    # Vincula a lista de modelos de endereço ao fornecedor (em memória)
    new_supplier_in_db.endereco = supplier_address_to_db
    
    # 5. RETORNA O OBJETO PERSISTIDO
    # O objeto já está completo e será comitado pelo endpoint
    return new_supplier_in_db

# =========================
# Serviço: Buscar Fornecedores
# =========================
def get_supplier_by_search(db: Session, supplier_search: str) -> list[FornecedorModel]:
    """
    Busca fornecedores usando a camada CRUD.
    Retorna a lista de fornecedores encontrada (pode ser vazia).

    Args:
        db (Session): A sessão do banco de dados.
        supplier_search (str): O termo a ser buscado.

    Returns:
        list[FornecedorModel]: Uma lista de objetos FornecedorModel.
    """
    # Delega a busca para a função do CRUD
    suppliers_in_db = supplier_crud.get_supplier_by_search(db, supplier_search)
    # Retorna a lista de fornecedores (pode ser vazia)
    return suppliers_in_db

# =========================
# Serviço: Atualizar Fornecedor
# =========================
def update_supplier(db: Session, supplier_id: int, supplier: FornecedorUpdate) -> FornecedorModel:
    """
    Atualiza um fornecedor existente pelo ID.
    Aplica atualizações parciais (patch) e retorna o objeto atualizado.

    Args:
        db (Session): A sessão do banco de dados.
        supplier_id (int): O ID do fornecedor a ser atualizado.
        supplier (FornecedorUpdate): O schema Pydantic com os campos a atualizar.

    Raises:
        HTTPException: 404 (Not Found) se o fornecedor não for encontrado.

    Returns:
        FornecedorModel: O objeto do fornecedor atualizado.
    """
    
    # 1. Busca o fornecedor existente no banco pelo ID
    supplier_in_db = supplier_crud.get_supplier_by_id(db, supplier_id)
    
    # 2. Verifica se o fornecedor foi encontrado
    if not supplier_in_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fornecedor não encontrado." # Corrigido: 'não'
        )
    
    # 3. Extrai apenas os dados enviados na requisição (para atualização parcial)
    update_supplier = supplier.model_dump(exclude_unset=True)

    # 4. Itera sobre os dados e atualiza o objeto SQLAlchemy
    for key, value in update_supplier.items():
        # Tratamento especial para o relacionamento aninhado 'endereco'
        if key == "endereco" and update_supplier["endereco"] is not None:
            # Chama o serviço de endereço para lidar com a atualização da lista
            updated_addresses = address_service.update_address_in_db(
                supplier_in_db.endereco, # Lista de endereços do banco
                supplier.endereco,        # Lista de dados de atualização do schema
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
# Serviço: Deletar Fornecedor
# =========================
def delete_supplier(db: Session, supplier_id: int) -> None:
    """
    Serviço para deletar um fornecedor pelo seu ID.

    1. Busca o fornecedor.
    2. Se encontrado, delega a exclusão para o CRUD.

    Args:
        db (Session): A sessão do banco de dados.
        supplier_id (int): O ID do fornecedor a ser deletado.

    Raises:
        HTTPException: 404 (Not Found) se o fornecedor não for encontrado.
    """
    # 1. Busca o fornecedor existente pelo ID
    supplier_in_db = supplier_crud.get_supplier_by_id(db, supplier_id)
    
    # 2. Verifica se o fornecedor foi encontrado
    if not supplier_in_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fornecedor não encontrado." # Corrigido: 'não'
        )
    
    # 3. Delega a exclusão para a camada CRUD (que faz db.delete e db.flush)
    return supplier_crud.delete_supplier(db, supplier_in_db)