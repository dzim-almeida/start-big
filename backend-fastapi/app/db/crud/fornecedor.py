# ---------------------------------------------------------------------------
# ARQUIVO: crud/fornecedor.py
# DESCRIÇÃO: Funções de CRUD (Create, Read, Update, Delete) para interagir
#            com a tabela de Fornecedores no banco de dados (Repository Layer).
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from typing import Sequence, Callable, Optional # Adicionado Optional para clareza

from app.db.models.fornecedor import Fornecedor as FornecedorModel

# =========================
# Funções de Validação/Conflito
# =========================

def verify_supplier_conflict(
    db: Session,
    value: str,
    # A função de busca deve retornar o modelo ou None
    search_method: Callable[[Session, str], FornecedorModel | None], 
    search_name: str
) -> str | None: # Retorna a mensagem de erro (str) ou None
    """
    Verifica se o valor fornecido (ex: CNPJ, IE) já existe no BD e se está ativo.
    """
    if not value:
        return None

    supplier_in_db = search_method(db, value)
    
    if supplier_in_db:
        # Verifica o status de atividade (para retornar mensagem específica de reativação)
        if not supplier_in_db.ativo:
            return "disabled supplier"
        # Conflito: Registro ativo encontrado
        return f"{search_name} já cadastrado"

    return None

# =========================
# Funções de Leitura (Read)
# =========================

def get_supplier_by_id(db: Session, supplier_id: int) -> FornecedorModel | None:
    """
    Busca um único fornecedor pelo seu ID (chave primária).
    """
    # Constrói a query para buscar pelo ID
    stmt = select(FornecedorModel).where(FornecedorModel.id == supplier_id)
    # Executa e retorna o primeiro resultado (ou None)
    supplier_in_db = db.scalars(stmt).first()
    return supplier_in_db

def get_all_suppliers(db: Session) -> Sequence[FornecedorModel]:
    """
    Busca TODOS os fornecedores cadastrados no banco de dados.
    """
    # Constrói a query: SELECT * FROM fornecedor
    stmt = select(FornecedorModel)
    # Executa a query e retorna todos os resultados
    suppliers_in_db = db.scalars(stmt).all()
    return suppliers_in_db

def get_supplier_by_cnpj(db: Session, supplier_cnpj: str) -> FornecedorModel | None:
    """
    Busca um único fornecedor pelo seu 'cnpj' exato.
    """
    # Constrói a query para buscar pelo CNPJ
    stmt = select(FornecedorModel).where(FornecedorModel.cnpj == supplier_cnpj)
    # Executa e retorna o primeiro resultado (ou None)
    supplier_in_db = db.scalars(stmt).first()
    return supplier_in_db

def get_supplier_by_ie(db: Session, supplier_ie: str) -> FornecedorModel | None:
    """
    Busca um único fornecedor pelo seu 'ie' exato.
    """
    # Constrói a query para buscar pelo ie
    stmt = select(FornecedorModel).where(FornecedorModel.ie == supplier_ie)
    # Executa e retorna o primeiro resultado (ou None)
    supplier_in_db = db.scalars(stmt).first()
    return supplier_in_db

def get_supplier_by_search(db: Session, supplier_search: str) -> Sequence[FornecedorModel]:
    """
    Busca fornecedores cujo nome, nome fantasia ou CNPJ comece
    com o termo de pesquisa (case-insensitive).
    """
    # Define as condições de busca (OR)
    conditions = or_(
        # Uso de ilike ou lower() para busca case-insensitive (depende do dialecto)
        FornecedorModel.nome.ilike(f"{supplier_search}%"), 
        FornecedorModel.nome_fantasia.ilike(f"{supplier_search}%"),
        FornecedorModel.cnpj.startswith(supplier_search) # CNPJ geralmente case-sensitive
    )

    # Constrói a query de seleção com o filtro
    stmt = select(FornecedorModel).where(conditions)
    # Executa a query e retorna todos os resultados
    suppliers_in_db = db.scalars(stmt).all()
    return suppliers_in_db

# =========================
# Função de Criação (Create)
# =========================

def create_supplier(db: Session, supplier_to_add: FornecedorModel) -> FornecedorModel:
    """
    Adiciona um novo fornecedor (e seus endereços associados em cascata)
    ao banco de dados.
    """
    # Adiciona o objeto principal à sessão (endereços vão junto por 'cascade')
    db.add(supplier_to_add)
    # Envia os INSERTs para o banco e obtém o ID gerado
    db.flush()
    # Atualiza o objeto Python com os dados do banco (incluindo o ID)
    db.refresh(supplier_to_add)
    # Retorna o objeto persistido
    return supplier_to_add

# =========================
# Função de Atualização (Update)
# =========================

def update_supplier(db: Session, supplier_to_update: FornecedorModel) -> FornecedorModel:
    """
    Persiste as alterações feitas em um objeto Fornecedor na sessão.
    O objeto já deve estar associado à sessão e ter sido modificado
    pela camada de serviço.
    """
    # O objeto já está rastreado pela sessão. db.flush() envia os UPDATEs.
    db.flush()
    # Recarrega o objeto do banco para garantir que esteja sincronizado.
    db.refresh(supplier_to_update)
    # Retorna o objeto atualizado.
    return supplier_to_update

# =========================
# Funções de Status (Ativar/Desativar)
# =========================

def active_supplier_by_id(db: Session, active_supplier: FornecedorModel) -> FornecedorModel:
    """
    Persiste o status de ativação (ativo=True) para o fornecedor na sessão.
    """
    # A modificação (active_supplier.ativo = True) é feita na camada de serviço.
    db.flush()
    db.refresh(active_supplier)
    return active_supplier

def disable_supplier_by_id(db: Session, disable_supplier: FornecedorModel) -> FornecedorModel:
    """
    Persiste o status de desativação (ativo=False) para o fornecedor na sessão (Soft Delete).
    """
    # A modificação (disable_supplier.ativo = False) é feita na camada de serviço.
    db.flush()
    db.refresh(disable_supplier)
    return disable_supplier