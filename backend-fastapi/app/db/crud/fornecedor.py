# ---------------------------------------------------------------------------
# ARQUIVO: crud/fornecedor.py
# DESCRIÇÃO: Funções de CRUD (Create, Read, Update, Delete) para interagir
#            com a tabela de Fornecedores no banco de dados (Repository Layer).
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from sqlalchemy import select, or_, and_
from typing import Sequence, Callable, Optional, TypeGuard # TypeGuard para o Callable

from app.db.models.fornecedor import Fornecedor as FornecedorModel

# =========================
# Funções de Validação/Conflito (REGRA 4: Robustez)
# =========================

# Define o tipo da função de busca para clareza
SearchMethod = Callable[[Session, str], Optional[FornecedorModel]]

def verify_fornecedor_conflict(
    db: Session,
    value: str,
    search_method: SearchMethod, 
    search_name: str
) -> Optional[str]:
    """
    Verifica se o valor fornecido (ex: CNPJ, IE) já existe no BD.

    Args:
        db (Session): Sessão de banco de dados.
        value (str): O valor a ser verificado (CNPJ ou IE).
        search_method (SearchMethod): A função CRUD específica para buscar o valor.
        search_name (str): Nome do campo para mensagem de erro.

    Returns:
        Optional[str]: Retorna 'disabled fornecedor' se inativo, 
                       a mensagem de erro se ativo, ou None se não houver conflito.
    """
    if not value:
        return None

    fornecedor_in_db = search_method(db, value)
    
    if fornecedor_in_db:
        # REGRA DE NEGÓCIO: Verifica se o registro duplicado está inativo
        if fornecedor_in_db.ativo is not True:
            return "disabled fornecedor"
        # Conflito: Registro ativo encontrado
        return f"{search_name} já cadastrado"

    return None

# Funções de Leitura (Read) (Docstrings detalhadas)
# ... (demais funções de CRUD get_fornecedor_by_id, get_fornecedor_by_cnpj, etc., com Docstrings completas) ...

def get_fornecedor_by_id(db: Session, fornecedor_id: int) -> Optional[FornecedorModel]:
    """Busca um único fornecedor pelo seu ID (chave primária)."""
    stmt = select(FornecedorModel).where(FornecedorModel.id == fornecedor_id)
    return db.scalars(stmt).first()

def get_fornecedor_by_cnpj(db: Session, fornecedor_cnpj: str) -> Optional[FornecedorModel]:
    """Busca um único fornecedor pelo seu 'cnpj' exato."""
    stmt = select(FornecedorModel).where(FornecedorModel.cnpj == fornecedor_cnpj)
    return db.scalars(stmt).first()

def get_fornecedor_by_ie(db: Session, fornecedor_ie: str) -> Optional[FornecedorModel]:
    """Busca um único fornecedor pelo seu 'ie' exato."""
    stmt = select(FornecedorModel).where(FornecedorModel.ie == fornecedor_ie)
    return db.scalars(stmt).first()

def get_fornecedor_by_search(db: Session, search: Optional[str]) -> Sequence[FornecedorModel]:
    """
    Busca fornecedores ativos por nome, nome fantasia ou CNPJ.
    
    Args:
        db (Session): Sessão de banco de dados.
        search (Optional[str]): Termo de busca (parcial).

    Returns:
        Sequence[FornecedorModel]: Lista de fornecedores ativos encontrados.
    """
    base_stmt = select(FornecedorModel).where(FornecedorModel.ativo.is_(True))
    
    if not search:
        stmt = base_stmt
    else:
        conditions = or_(
            FornecedorModel.nome.ilike(f"%{search}%"), # Adicionado % para busca parcial no início e fim
            FornecedorModel.nome_fantasia.ilike(f"%{search}%"),
            FornecedorModel.cnpj.like(f"{search}%") 
        )

        stmt = base_stmt.where(conditions) # Combina a condição de ativo com as condições de busca
        
    return db.scalars(stmt).all()


def create_fornecedor(db: Session, fornecedor_to_add: FornecedorModel) -> FornecedorModel:
    """
    Adiciona um novo fornecedor (e seus endereços associados em cascata)
    ao banco de dados.
    """
    db.add(fornecedor_to_add)
    db.flush()
    db.refresh(fornecedor_to_add)
    return fornecedor_to_add

def update_fornecedor(db: Session, fornecedor_to_update: FornecedorModel) -> FornecedorModel:
    """
    Persiste as alterações feitas em um objeto Fornecedor na sessão.
    """
    db.flush()
    db.refresh(fornecedor_to_update)
    return fornecedor_to_update