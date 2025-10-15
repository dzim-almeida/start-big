# Modelos SQLAlchemy para Usuários

"""
Modelos SQLAlchemy para a tabela 'usuarios'.
Define o modelo Usuario, que representa os dados de um usuário do sistema.
"""

from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint, ForeignKey, Enum as SqlAlchemyEnum  # type: ignore
from sqlalchemy.orm import relationship  # type: ignore
from app.db.base import Base
from app.core.enum import UserType  # Enum de tipo de usuário

# =========================
# Modelo SQLAlchemy: Usuários
# =========================
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(SqlAlchemyEnum(UserType), nullable=False)  # 'Admin' ou 'User'
    nome = Column(String(255, collation="NOCASE"), nullable=False)
    email = Column(String(255, collation="NOCASE"), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255, collation="NOCASE"), nullable=False)
    data_criacao = Column(DateTime, nullable=False)