# ---------------------------------------------------------------------------
# ARQUIVO: crud/servico.py
# DESCRIÇÃO: Funções de acesso e manipulação da tabela de Serviços (CRUD).
#            Esta é a camada de acesso direto ao banco de dados.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from typing import Sequence

# Importa o modelo ORM, renomeando para clareza
from app.db.models.servico import Servico as ServicoModel


# =========================
# READ: Buscar por ID
# =========================
def get_service_by_id(db: Session, id: int) -> ServicoModel | None:
    """
    Busca um serviço específico pelo seu ID (chave primária).

    Args:
        db (Session): Sessão do banco de dados.
        id (int): ID do serviço a ser buscado.

    Returns:
        ServicoModel | None: O objeto modelo do serviço ou None se não encontrado.
    """
    # Cria a query: SELECT * FROM servico WHERE id = :id
    stmt = select(ServicoModel).where(ServicoModel.id == id)
    
    # Executa a query e retorna o primeiro resultado (ou None)
    service_in_db = db.scalars(stmt).first()
    return service_in_db


# =========================
# READ: Buscar por Termo (Search)
# =========================
def get_service_by_search(db: Session, search: str) -> Sequence[ServicoModel]:
    """
    Busca serviços cuja descrição começa com o termo de busca.

    Args:
        db (Session): Sessão do banco de dados.
        search (str): Termo de busca (prefixo).

    Returns:
        Sequence[ServicoModel]: Uma lista (sequência) de serviços
                                que correspondem à busca.
    """
    # Define as condições de busca (atualmente, apenas 'descricao')
    # O or_ é útil para adicionar mais campos de busca (ex: código, etc.)
    conditions = or_(
        ServicoModel.descricao.startswith(search)
    )

    # Cria a query: SELECT * FROM servico WHERE conditions
    stmt = select(ServicoModel).where(conditions)
    
    # Executa a query e retorna todos os resultados
    services_in_db = db.scalars(stmt).all()
    return services_in_db


# =========================
# READ: Buscar por Descrição Exata
# =========================
def get_service_by_description(db: Session, description_to_search: str) -> ServicoModel | None:
    """
    Busca um serviço pela sua descrição exata.
    (Usado geralmente para verificar duplicidade antes de criar)

    Args:
        db (Session): Sessão do banco de dados.
        description_to_search (str): Descrição exata a ser buscada.

    Returns:
        ServicoModel | None: O objeto modelo do serviço ou None se não encontrado.
    """
    # Cria a query: SELECT * FROM servico WHERE descricao = :description
    stmt = select(ServicoModel).where(ServicoModel.descricao == description_to_search)
    
    # Executa a query e retorna o primeiro resultado
    service_in_db = db.scalars(stmt).first()
    return service_in_db


# =========================
# CREATE
# =========================
def create_service(db: Session, service_to_add: ServicoModel) -> ServicoModel:
    """
    Adiciona um novo objeto de serviço à sessão do banco de dados.

    Args:
        db (Session): Sessão do banco de dados.
        service_to_add (ServicoModel): O objeto modelo (preenchido) a ser criado.

    Returns:
        ServicoModel: O objeto modelo após ser salvo e atualizado (ex: com ID).
    """
    # Adiciona o objeto à sessão
    db.add(service_to_add)
    
    # Envia as alterações para o DB (para que o ID seja gerado pela sequence)
    db.flush()
    
    # Atualiza o objeto 'service_to_add' com os dados do DB (ex: ID gerado)
    db.refresh(service_to_add)
    
    return service_to_add


# =========================
# UPDATE
# =========================
def update_service(db: Session, service_to_update: ServicoModel) -> ServicoModel:
    """
    Atualiza um serviço na sessão.
    Nota: A modificação dos atributos do objeto 'service_to_update'
    deve ter sido feita *antes* de chamar esta função (na camada de serviço).

    Args:
        db (Session): Sessão do banco de dados.
        service_to_update (ServicoModel): O objeto modelo já modificado em memória.

    Returns:
        ServicoModel: O objeto modelo atualizado.
    """
    # Envia as alterações (updates) para o DB
    # O SQLAlchemy já sabe que o objeto 'service_to_update' está "sujo" (dirty)
    db.flush()
    
    # Atualiza o objeto com quaisquer triggers/defaults que possam ter mudado no DB
    db.refresh(service_to_update)
    
    return service_to_update


# =========================
# DELETE
# =========================
def delete_service(db: Session, service_to_delete: ServicoModel) -> None:
    """
    Remove um serviço da sessão do banco de dados.

    Args:
        db (Session): Sessão do banco de dados.
        service_to_delete (ServicoModel): O objeto modelo a ser deletado.
    """
    # Marca o objeto para deleção
    db.delete(service_to_delete)
    
    # Envia a operação de 'DELETE' para o DB
    db.flush()