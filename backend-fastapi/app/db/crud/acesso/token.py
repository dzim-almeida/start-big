# ---------------------------------------------------------------------------
# ARQUIVO: token.py (crud)
# DESCRIÇÃO: Funções de acesso ao banco de dados para a tabela TokenBlocklist.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from app.db.models.token import TokenBlocklist

def create_revoke_token(db: Session, token: TokenBlocklist) -> None:
    """
    Adiciona um token revogado à sessão do banco de dados.
    Não realiza o commit da transação.

    Args:
        db (Session): A sessão do banco de dados.
        token (TokenBlocklist): O objeto do token a ser adicionado.
    """
    db.add(token)
    db.flush()

def get_revoke_token(db: Session, token_jti: str) -> TokenBlocklist | None:
    """
    Busca por um token revogado na blocklist usando seu JTI.

    Args:
        db (Session): A sessão do banco de dados.
        token_jti (str): O JTI (ID do token) a ser pesquisado.

    Returns:
        TokenBlocklist | None: Retorna o objeto se o token estiver na
                                blocklist, caso contrário, retorna None.
    """
    return db.query(TokenBlocklist).filter(TokenBlocklist.jti == token_jti).first()