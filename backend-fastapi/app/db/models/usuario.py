# Modelos SQLAlchemy para Usuários
# ---------------------------------------------------------------------------
# ARQUIVO: usuario.py
# DESCRIÇÃO: Modelo SQLAlchemy para a tabela 'usuarios'.
#            Define o modelo Usuario e a relação Um-para-Um com Funcionario.
# ---------------------------------------------------------------------------

from sqlalchemy import Integer, String, DateTime, Enum as SqlAlchemyEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional # Para tipagem moderna de campos opcionais
from datetime import datetime

from app.db.base import Base
from app.core.enum import UserType  # Enum de tipo de usuário (Assumindo que está neste caminho)

# =========================
# Modelo SQLAlchemy: Usuários (SQLAlchemy 2.0)
# =========================
class Usuario(Base):
    """
    Representa a tabela 'usuarios', contendo dados de acesso e autenticação.
    Implementa a relação 1:1 com a entidade Funcionario.
    """
    __tablename__ = "usuarios"

    # Chave primária: id (PK)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, doc="ID único do usuário (PK)")
    
    # Colunas de Dados
    tipo: Mapped[UserType] = mapped_column(SqlAlchemyEnum(UserType), nullable=False, doc="Tipo de usuário ('Admin' ou 'User')")
    nome: Mapped[str] = mapped_column(String(255), nullable=False, doc="Nome de login/exibição do usuário")
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True, doc="E-mail do usuário")
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False, doc="Hash da senha do usuário")
    data_criacao: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False, doc="Timestamp da criação do registro")

    # RELACIONAMENTO 1:1 com Funcionario
    # 1. Usa string literal "Funcionario" para evitar Importação Circular.
    # 2. 'uselist=False' garante que no máximo UM Funcionario esteja associado.
    funcionario = relationship(
        "Funcionario",
        back_populates="usuario",
        uselist=False, # 🔑 Essencial para a relação Um-para-Um
        doc="Relacionamento Um-para-Um com a ficha do Funcionário"
    )