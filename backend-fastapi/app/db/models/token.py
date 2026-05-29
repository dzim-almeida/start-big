# Modelos SQLAlchemy para Clientes

"""
Modelos SQLAlchemy para a tabela 'token_blocklist'.
Define o modelo TokenBlocklist, que representa os tokens revogados do sistema.
"""

from sqlalchemy import Column, Integer, String, DateTime  # type: ignore
from app.db.base import Base

# =========================
# Modelo SQLAlchemy: TokenBlocklist
# =========================
class TokenBlocklist(Base):
    __tablename__ = "token_blocklist"

    jti = Column(String, primary_key=True, index=True)
    exp = Column(DateTime, nullable=False)

