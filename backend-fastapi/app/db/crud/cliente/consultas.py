# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/cliente/consultas.py
# DESCRICAO: Clientes - buscas por id/CPF/CNPJ/e-mail/RG/IE, pesquisa e
#            verificacao de conflito de documento.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session, with_polymorphic
from sqlalchemy import and_, select, func
from typing import Sequence, Callable, Optional

from app.core.busca import filtro_busca
from app.db.models.cliente import Cliente as ClienteModel, ClientePF, ClientePJ


def _campos_busca(poly) -> tuple:
    """
    Campos varridos na busca de cliente.

    Recebe o `with_polymorphic` já montado porque PF e PJ vivem em tabelas
    filhas: as colunas precisam vir da mesma entidade polimórfica usada no
    SELECT, senão o SQLAlchemy repete o JOIN.

    Não há resgate por similaridade aqui, de propósito: confundir "José Silva"
    com "Josué Silva" custa caro num campo que decide quem vai ser cobrado.
    Ignorar acentos e ordem das palavras já resolve o caso real ("joao" achar
    "João").
    """
    return (
        poly.ClientePF.nome,
        poly.ClientePF.cpf,
        poly.ClientePJ.razao_social,
        poly.ClientePJ.nome_fantasia,
        poly.ClientePJ.cnpj,
        poly.email,
    )


# ===========================================================================
# VERIFICAÇÕES (AUXILIARES)
# ===========================================================================

def verify_cliente_conflict(
    db: Session,
    value: str,
    search_method: Callable[[Session, str], ClienteModel | None],
    search_name: str,
    cliente_id: Optional[int] = None,
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

    if cliente_in_db:
        if cliente_id and cliente_in_db.id == cliente_id:
            return None

        if not cliente_in_db.ativo:
            return "disabled cliente"

        return f"{search_name} já cadastrado"

    return None


# ===========================================================================
# LEITURA (READ)
# ===========================================================================

def get_cliente_by_id(db: Session, cliente_id: int) -> ClienteModel | None:
    """Busca cliente pelo ID (PK). Retorna ClientePF ou ClientePJ conforme o tipo."""
    return db.get(ClienteModel, cliente_id)


def get_cliente_by_email(db: Session, email: str) -> ClienteModel | None:
    """Busca cliente pelo Email (campo comum na tabela pai)."""
    return db.scalar(select(ClienteModel).where(ClienteModel.email == email))


def get_cliente_by_cpf(db: Session, cpf: str) -> ClientePF | None:
    """Busca Pessoa Física pelo CPF (tabela clientes_pf)."""
    return db.scalar(select(ClientePF).where(ClientePF.cpf == cpf))


def get_cliente_by_cnpj(db: Session, cnpj: str) -> ClientePJ | None:
    """Busca Pessoa Jurídica pelo CNPJ (tabela clientes_pj)."""
    return db.scalar(select(ClientePJ).where(ClientePJ.cnpj == cnpj))


def get_cliente_by_rg(db: Session, rg: str) -> ClientePF | None:
    """Busca Pessoa Física pelo RG (tabela clientes_pf)."""
    return db.scalar(select(ClientePF).where(ClientePF.rg == rg))


def get_cliente_by_ie(db: Session, ie: str) -> ClientePJ | None:
    """Busca Pessoa Jurídica pela Inscrição Estadual (tabela clientes_pj)."""
    return db.scalar(select(ClientePJ).where(ClientePJ.ie == ie))


def get_cliente_by_search(
    db: Session,
    filters: dict,
    skip: int = 0,
    limit: int = 20) -> tuple[Sequence[ClienteModel], int]:
    """
    Busca com paginação e contagem total.
    Usa with_polymorphic para carregar PF e PJ em uma única query (LEFT JOIN),
    evitando conflitos com o Joined Table Inheritance do SQLAlchemy.
    """
    poly = with_polymorphic(ClienteModel, [ClientePF, ClientePJ])
    query = select(poly)

    if filters.get("only_active", True):
        query = query.where(poly.ativo == True)

    search = filters.get("search")
    filtro = filtro_busca(search, _campos_busca(poly))
    if filtro is not None:
        query = query.where(filtro)

    count_stmt = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_stmt) or 0

    stmt = query.order_by(poly.id.desc()).offset(skip).limit(limit)
    clientes = db.scalars(stmt).all()

    return clientes, total


def get_cliente_simple_by_search(db: Session, search: Optional[str]) -> Sequence[ClienteModel]:

    customers = with_polymorphic(ClienteModel, [ClientePF, ClientePJ])

    filtro = filtro_busca(search, _campos_busca(customers))
    if filtro is not None:
        return db.scalars(select(customers).where(and_(filtro, customers.ativo == True))).all()

    return db.scalars(select(customers).where(customers.ativo == True)).all()
