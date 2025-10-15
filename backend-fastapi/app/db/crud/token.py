
from sqlalchemy.orm import Session
from app.db.models.token import TokenBlocklist

def create_revoke_token(db: Session, token: TokenBlocklist):
    db.add(token)
    db.flush()  

def get_revoke_token(db: Session, token_jti: str) -> TokenBlocklist | None:
    return db.query(TokenBlocklist).filter(TokenBlocklist.jti == token_jti).first()
