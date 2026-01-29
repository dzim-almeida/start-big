# ---------------------------------------------------------------------------
# ARQUIVO: cliente_crud.py
# MÓDULO: Acesso a Dados (Repository)
# DESCRIÇÃO: Executa queries SQL via SQLAlchemy para manipulação de Clientes.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session, aliased
from sqlalchemy import select, or_, and_
from typing import Sequence, Callable, Optional

from app.db.models.cliente import Cliente as ClienteModel, ClientePF as ClientePFModel, ClientePJ as ClientePJModel

# ===========================================================================
# VERIFICAÇÕES (AUXILIARES)
# ===========================================================================

def verify_cliente_conflict(
    db: Session,
    value: str,
    search_method: Callable[[Session, str], ClienteModel | None],
    search_name: str,
    cliente_id: Optional[id] = None,
) -> str | None:
    """
    Verifica se um valor único (CPF, CNPJ, Email) já existe no banco.
    
    Returns:
        str: Mensagem de erro se houver conflito ou cliente inativo.
        None: Se o valor estiver livre para uso.
    """
    if not value:
        return None

    cliente_in_db = search_method(db, value)

    if cliente_id and cliente_in_db.id == cliente_id:
        return None
    
    if cliente_in_db:
        # Se existe mas está inativo, retorna mensagem específica para reativação
        if not cliente_in_db.ativo: 
            return "disabled cliente"
    
        return f"{search_name} já cadastrado"

    return None

# ===========================================================================
# LEITURA (READ)
# ===========================================================================

def get_all_clientes(db: Session) -> Sequence[ClienteModel]:
    """Retorna todos os clientes ativos do sistema."""
    stmt = select(ClienteModel).where(ClienteModel.ativo == True)
    clientes_in_db = db.scalars(stmt).all()
    return clientes_in_db

def get_cliente_by_id(db: Session, cliente_id: int) -> ClienteModel | None:
    """Busca cliente pelo ID (PK)."""
    stmt = select(ClienteModel).where(ClienteModel.id == cliente_id)
    cliente_in_db = db.scalars(stmt).first()
    return  cliente_in_db

def get_cliente_by_email(db: Session, cliente_email: str) -> ClienteModel | None:
    """Busca cliente pelo Email."""
    stmt = select(ClienteModel).where(ClienteModel.email == cliente_email)
    cliente_in_db = db.scalars(stmt).first()
    return  cliente_in_db

def get_cliente_by_cpf(db: Session, cliente_cpf: str) -> ClientePFModel | None:
    """Busca Pessoa Física pelo CPF."""
    stmt = select(ClientePFModel).where(ClientePFModel.cpf == cliente_cpf)
    cliente_in_db = db.scalars(stmt).first()
    return cliente_in_db

def get_cliente_by_rg(db: Session, cliente_rg: str) -> ClientePFModel | None:
    """Busca Pessoa Física pelo RG."""
    stmt = select(ClientePFModel).where(ClientePFModel.rg == cliente_rg)
    cliente_in_db = db.scalars(stmt).first()
    return cliente_in_db

def get_cliente_by_cnpj(db: Session, cliente_cnpj: str) -> ClientePJModel | None:
    """Busca Pessoa Jurídica pelo CNPJ."""
    stmt = select(ClientePJModel).where(ClientePJModel.cnpj == cliente_cnpj)
    cliente_in_db = db.scalars(stmt).first()
    return cliente_in_db

def get_cliente_by_ie(db: Session, cliente_ie: str) -> ClientePJModel | None:
    """Busca Pessoa Jurídica pela Inscrição Estadual."""
    stmt = select(ClientePJModel).where(ClientePJModel.ie == cliente_ie)
    cliente_in_db = db.scalars(stmt).first()
    return cliente_in_db

def get_cliente_by_search(db: Session, search: str | None) -> Sequence[ClienteModel]:
    """
    Busca Complexa Polimórfica.
    
    Realiza JOINs com as tabelas de PF e PJ para permitir buscar por campos
    específicos de cada tipo (CPF, Nome, Razão Social, CNPJ) em uma única query.
    
    Args:
        search (str): Termo a ser buscado (case insensitive).
        
    Returns:
        Sequence[ClienteModel]: Lista de clientes que correspondem aos critérios.
    """
    if not search:
        stmt = select(ClienteModel)
    else:
        # Aliases permitem referenciar as tabelas filhas na cláusula WHERE
        pf_alias = aliased(ClientePFModel)
        pj_alias = aliased(ClientePJModel)

        # Busca flexível em múltiplos campos
        conditions = or_(
            pf_alias.nome.ilike(f"{search}%"),
            pf_alias.cpf.startswith(search),
            pj_alias.razao_social.ilike(f"{search}%"),
            pj_alias.cnpj.startswith(search),
            pj_alias.nome_fantasia.ilike(f"{search}%"),
        )

        stmt = select(ClienteModel)
        # Outer Join permite trazer dados de PF ou PJ se existirem
        stmt = stmt.outerjoin(pf_alias, ClienteModel.id == pf_alias.id)
        stmt = stmt.outerjoin(pj_alias, ClienteModel.id == pj_alias.id)
        
        stmt = stmt.where(
            and_(
                conditions
            )
        )

    return db.scalars(stmt).all()

# ===========================================================================
# ESCRITA (CREATE / UPDATE)
# ===========================================================================

def create_cliente(db: Session, cliente_to_add: ClienteModel) -> ClienteModel:
    """Adiciona e persiste um novo cliente no banco."""
    db.add(cliente_to_add)
    db.flush() # Gera o ID sem comitar a transação final ainda
    db.refresh(cliente_to_add)
    return cliente_to_add

def update_cliente_in_db(db: Session, cliente_to_update: ClienteModel) -> ClienteModel:
    """Atualiza o estado de um cliente já anexado à sessão."""
    db.flush()
    db.refresh(cliente_to_update)
    return cliente_to_update