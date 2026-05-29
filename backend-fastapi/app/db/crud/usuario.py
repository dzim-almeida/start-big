# ---------------------------------------------------------------------------
# ARQUIVO: crud/usuario_crud.py
# MÓDULO: Acesso a Dados (Repository)
# DESCRIÇÃO: Queries SQL otimizadas para a tabela de usuários.
# ---------------------------------------------------------------------------

from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Sequence, Optional

from app.db.models.usuario import Usuario as UsuarioModel

# ===========================================================================
# LEITURA (READ)
# ===========================================================================

def get_usuario_by_email(db: Session, usuario_email: str) -> Optional[UsuarioModel]:
    """
    Busca exata por e-mail no banco de dados.

    Args:
        db (Session): Sessão de banco de dados ativa.
        usuario_email (str): O e-mail do usuário a ser buscado.

    Returns:
        Optional[UsuarioModel]: O objeto UsuarioModel se encontrado, ou None.
    """
    stmt = select(UsuarioModel).where(UsuarioModel.email == usuario_email)
    return db.scalars(stmt).first()

def get_usuario_by_id(db: Session, usuario_id: int) -> Optional[UsuarioModel]:
    """
    Busca um usuário pela Chave Primária (ID).

    Args:
        db (Session): Sessão de banco de dados ativa.
        usuario_id (int): O ID do usuário (PK).

    Returns:
        Optional[UsuarioModel]: O objeto UsuarioModel se encontrado, ou None.
    """
    stmt = select(UsuarioModel).where(UsuarioModel.id == usuario_id)
    return db.scalars(stmt).first()

def get_usuario_master(db: Session) -> Optional[UsuarioModel]:
    """
    Verifica se existe algum usuário com a flag 'is_master' como True no sistema.

    Args:
        db (Session): Sessão de banco de dados ativa.

    Returns:
        Optional[UsuarioModel]: O primeiro objeto UsuarioModel mestre encontrado, ou None.
    """
    # REGRA 4 aplicada: Uso correto do .is_(True) do SQLAlchemy
    stmt = select(UsuarioModel).where(UsuarioModel.is_master.is_(True))
    return db.scalars(stmt).first()

def get_usuario_by_search(db: Session, usuario_search: str | None) -> Sequence[UsuarioModel]:
    """
    Lista usuários ativos com filtro opcional por nome ou e-mail (busca parcial).

    Args:
        db (Session): Sessão de banco de dados ativa.
        usuario_search (str | None): Termo de busca (nome, e-mail) ou None para listar todos ativos.

    Returns:
        Sequence[UsuarioModel]: Uma sequência (lista) de objetos UsuarioModel que correspondem ao filtro.
    """
    # A base da query é sempre buscar usuários ativos.
    base_stmt = select(UsuarioModel).where(UsuarioModel.ativo.is_(True))
    
    if usuario_search:
        # Nota: Usando ilike para busca case-insensitive e % para busca parcial
        # O uso do 'and' implícito do where é correto para múltiplos filtros
        # mas para clareza em SQLA 2.0, o '&' é mais explícito.
        stmt = base_stmt.where(
            (UsuarioModel.nome.ilike(f"%{usuario_search}%")) |
            (UsuarioModel.email.ilike(f"%{usuario_search}%")) # Adicionei filtro por e-mail para robustez
        )
    else:
        stmt = base_stmt
        
    return db.scalars(stmt).all()

# ===========================================================================
# ESCRITA (CREATE)
# ===========================================================================    

def create_user(db: Session, usuario_to_add: UsuarioModel) -> UsuarioModel:
    """
    Persiste um novo objeto Usuário no banco de dados.

    Args:
        db (Session): Sessão de banco de dados ativa.
        usuario_to_add (UsuarioModel): O objeto ORM de usuário a ser adicionado.

    Returns:
        UsuarioModel: O objeto UsuarioModel recém-criado, após refresh.
    """
    db.add(usuario_to_add)
    # db.flush() e db.refresh() garantem que o ID (PK) seja populado no objeto
    # antes do retorno. O flush pode ser omitido se o refresh for chamado logo após o add,
    # mas mantê-lo é claro em sua intenção.
    db.flush() 
    db.refresh(usuario_to_add)
    return usuario_to_add