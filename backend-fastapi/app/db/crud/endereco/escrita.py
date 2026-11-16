# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/endereco/escrita.py
# DESCRICAO: Endereco (crud) - apagar endereco.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from app.db.models.endereco import Endereco as EnderecoModel


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
