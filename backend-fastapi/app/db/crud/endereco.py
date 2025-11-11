from typing import Optional # Importação adicionada para tipagem
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models.endereco import Endereco as EnderecoModel

def get_address_by_id(db: Session, address_id: int) -> Optional[EnderecoModel]:
    """
    Busca um objeto Endereco pelo ID na base de dados.

    Args:
        db (Session): A sessão ativa do banco de dados.
        address_id (int): O ID do endereço a ser buscado.

    Returns:
        Optional[EnderecoModel]: O objeto EnderecoModel correspondente ou None.
    """
    # Cria a instrução SELECT usando o padrão SQLAlchemy 2.0
    stmt = select(EnderecoModel).where(EnderecoModel.id == address_id)
    
    # Executa a query e retorna o primeiro resultado
    address_in_db = db.scalars(stmt).first()
    return address_in_db

def delete_address_by_id(db: Session, address_to_delete: EnderecoModel) -> None:
    """
    Deleta um objeto EnderecoModel do banco de dados.
    A deleção é marcada na sessão e forçada com um flush.

    Args:
        db (Session): A sessão ativa do banco de dados.
        address_to_delete (EnderecoModel): O objeto Endereco a ser deletado.
    """
    # Marca o objeto para deleção na sessão
    db.delete(address_to_delete)
    
    # Executa a deleção no banco de dados imediatamente (sem commit)
    db.flush()