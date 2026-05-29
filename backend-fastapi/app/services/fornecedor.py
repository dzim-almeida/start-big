# ---------------------------------------------------------------------------
# ARQUIVO: services/fornecedor.py
# DESCRIÇÃO: Camada de serviço com a lógica de negócio para Fornecedores.
#            Implementa o CRUD completo, incluindo a gestão de
#            endereços polimórficos.
# ---------------------------------------------------------------------------

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Sequence, List, Optional, Dict, Any

# Importa os schemas Pydantic (Create para entrada, Update para modificação)
from app.schemas.fornecedor import FornecedorCreate, FornecedorUpdate
# Importa o modelo ORM
from app.db.models.fornecedor import Fornecedor as FornecedorModel

# Importa os Enums e serviços necessários
from app.core.enum import EntityType
from app.services import endereco as endereco_service
from app.db.crud import fornecedor as fornecedor_crud

# Definição de exceções padrão para reutilização
conflict_exce = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Fornecedor já cadastrado no sistema"
)

not_found_exce = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Fornecedor não encontrado no sistema"
)

# Nota: O Pydantic V2 permite que o 'detail' seja '...' para listas/erros customizados
validation_exce = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail=...
)

# Campos que exigem verificação de unicidade no banco
unique_fields = ["cnpj", "ie"]

# Mapa de validadores mapeando campo -> função de busca no CRUD
validators = {
    "cnpj": fornecedor_crud.get_fornecedor_by_cnpj,
    "ie": fornecedor_crud.get_fornecedor_by_ie
}

# =========================
# Serviço: Criar Fornecedor
# =========================
def create_fornecedor(db: Session, fornecedor_to_add: FornecedorCreate) -> FornecedorModel:
    """
    Serviço para criar um novo Fornecedor, validando unicidade e vinculando endereços.

    Regras:
    1. Valida unicidade de CNPJ/IE e trata casos de reativação.
    2. Persiste o fornecedor para obter o ID.
    3. Chama o serviço de endereço para criar e vincular os dados polimórficos.

    Args:
        db (Session): Sessão de banco de dados ativa.
        fornecedor_to_add (FornecedorCreate): DTO com dados do novo fornecedor e endereços.

    Raises:
        HTTPException 409 CONFLICT: Se houver conflito de CNPJ/IE ou necessidade de reativação.

    Returns:
        FornecedorModel: O objeto FornecedorModel criado, incluindo as relações de endereço.
    """
    # 1. REGRA DE NEGÓCIO: Verificar se o CNPJ/IE já existe
    validation_errors: List[Dict[str, str]] = []

    # Exclui explicitamente 'endereco' antes de mapear os dados para validação de unicidade
    fornecedor_data = fornecedor_to_add.model_dump(exclude={"endereco"}, exclude_unset=True)

# Loop de validação de unicidade
    for field in unique_fields:
        value: Optional[str] = fornecedor_data.get(field)
        if value is not None:
            error: Optional[str] = fornecedor_crud.verify_fornecedor_conflict(
                db, value, validators[field], field
            )
            if error:
                # Tratamento especial para fornecedor desativado
                if error == "disabled fornecedor":
                    # REGRA 4 aplicada: Lança a exceção de reativação
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Fornecedor desabilitado com este CPF/CNPJ. Por favor, reative o cadastro."
                    )
                # Conflito padrão de unicidade
                validation_errors.append({"campo": field, "mensagem": error})
    
    if validation_errors:
        validation_exce.detail = validation_errors
        raise validation_exce

    
    # 2. MAPEAMENTO: Cria a instância do modelo SQLAlchemy
    # Nota: `fornecedor_data` não contém 'endereco'
    fornecedor_to_db = FornecedorModel(**fornecedor_data)
    # 3. CHAMA A CAMADA CRUD (para obter o ID)
    fornecedor_in_db = fornecedor_crud.create_fornecedor(db, fornecedor_to_add=fornecedor_to_db)

    # 4. PREPARA E VINCULA OS ENDEREÇOS
    if fornecedor_to_add.endereco:
        fornecedor_address_to_db = endereco_service.address_to_db(
            id_entity=fornecedor_in_db.id,
            type_entity=EntityType.FORNECEDOR,
            address_data=fornecedor_to_add.endereco
        )

        fornecedor_in_db.endereco = fornecedor_address_to_db
    
    # 5. RETORNA O OBJETO PERSISTIDO
    return fornecedor_in_db

# =========================
# Serviço: Buscar Fornecedores
# =========================
def get_fornecedor_by_search(db: Session, search: Optional[str]) -> Sequence[FornecedorModel]:
    """
    Busca fornecedores ativos por critério de busca (nome, fantasia ou CNPJ).

    Args:
        db (Session): Sessão de banco de dados ativa.
        search (str | None): Termo de busca opcional (nome, cnpj, ie).

    Returns:
        Sequence[FornecedorModel]: Lista de objetos FornecedorModel encontrados.
    """
    return fornecedor_crud.get_fornecedor_by_search(db, search)

# =========================
# Serviço: Atualizar Fornecedor
# =========================
def update_fornecedor_by_id(
    db: Session, 
    fornecedor_id: int, 
    fornecedor_to_update: FornecedorUpdate
) -> FornecedorModel:
    """
    Atualiza um fornecedor existente pelo ID, validando unicidade e atualizando endereços aninhados.

    Args:
        db (Session): Sessão de banco de dados ativa.
        fornecedor_id (int): ID do fornecedor a ser atualizado.
        fornecedor_to_update (FornecedorUpdate): DTO com os campos opcionais a serem modificados.

    Raises:
        HTTPException 404 NOT FOUND: Se o fornecedor não for encontrado.
        HTTPException 409 CONFLICT: Se a atualização gerar duplicidade de CNPJ/IE.

    Returns:
        FornecedorModel: O objeto FornecedorModel atualizado.
    """
   
    validation_errors: List[Dict[str, str]] = []

    # 1. Busca e valida a existência
    fornecedor_in_db: Optional[FornecedorModel] = fornecedor_crud.get_fornecedor_by_id(db, fornecedor_id=fornecedor_id)
    if not fornecedor_in_db:
        raise not_found_exce

    # 2. Mapeamento de dados de atualização (apenas campos setados no DTO)
    data_to_update: Dict[str, Any] = fornecedor_to_update.model_dump(exclude_unset=True)

# Loop de validação de unicidade
    for field in unique_fields:
        value: Optional[str] = data_to_update.get(field)
        if value is not None:
            # Pula a validação se o valor for igual ao que já está no objeto (evita conflito consigo mesmo)
            if getattr(fornecedor_in_db, field) == value:
                continue
                
            error: Optional[str] = fornecedor_crud.verify_fornecedor_conflict(
                db, value, validators[field], field
            )
            if error:
                validation_errors.append({"campo": field, "mensagem": error})
    
    if validation_errors:
        validation_exce.detail = validation_errors
        raise validation_exce
    
    # 3. Tratamento de Endereços Aninhados
    if "endereco" in data_to_update:
        updated_addresses = endereco_service.update_address_in_db(
            address_in_db=fornecedor_in_db.endereco, # Relação atual (pode ser None)
            address_to_update=fornecedor_to_update.endereco, # DTO de entrada
            id_entity=fornecedor_in_db.id,
            type_entity=EntityType.FORNECEDOR
        )
        fornecedor_in_db.endereco = updated_addresses
        del data_to_update["endereco"]

    # 4. Itera sobre os dados e atualiza o objeto SQLAlchemy
    for key, value in data_to_update.items():
        setattr(fornecedor_in_db, key, value)

    # 5. Chama o CRUD para persistir as alterações (flush + refresh)
    return fornecedor_crud.update_fornecedor(db, fornecedor_to_update=fornecedor_in_db)

# =========================
# Serviço: Ativar Fornecedor
# =========================
def toggle_active_disable_fornecedor_by_id(db: Session, fornecedor_id: int) -> FornecedorModel:
    """
    Alterna o status 'ativo' (True <-> False) de um fornecedor (Deleção/Reativação Lógica).

    Args:
        db (Session): Sessão de banco de dados ativa.
        fornecedor_id (int): ID do fornecedor a ter o status modificado.

    Raises:
        HTTPException 404 NOT FOUND: Se o fornecedor não for encontrado.

    Returns:
        FornecedorModel: O objeto FornecedorModel com o status 'ativo' atualizado.
    """
    
    # 1. Busca e valida a existência
    fornecedor_in_db: Optional[FornecedorModel] = fornecedor_crud.get_fornecedor_by_id(db, fornecedor_id=fornecedor_id)
    if not fornecedor_in_db:
        raise not_found_exce
    
    # 2. Inverte o status lógico
    fornecedor_in_db.ativo = not fornecedor_in_db.ativo

    # 3. Delega a persistência para a camada CRUD
    return fornecedor_crud.update_fornecedor(db, fornecedor_to_update=fornecedor_in_db)