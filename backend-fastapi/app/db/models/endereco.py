# ---------------------------------------------------------------------------
# ARQUIVO: endereco.py
# DESCRIÇÃO: Modelo SQLAlchemy para a tabela 'enderecos', que representa
#            os endereços vinculados a diferentes entidades (ex: Clientes).
# ---------------------------------------------------------------------------

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import Enum as SQLAlchemyEnum

from app.db.base import Base
from app.core.enum import State  # Enum dos estados brasileiros
from app.core.enum import EntityType # Enum dos tipos de entidade (CLIENTE, FORNECEDOR)

# =========================
# Modelo SQLAlchemy: Endereco
# =========================
class Endereco(Base):
    """
    Representa a tabela 'enderecos'. Cada registro é um endereço
    associado a uma entidade polimórfica (Cliente, Fornecedor, etc.).
    """
    __tablename__ = "enderecos"

    # Chave primária da tabela de endereços
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # --- Colunas para Relação Polimórfica ---
    # Armazena o ID da entidade (ex: ID do cliente)
    id_entidade: Mapped[int] = mapped_column(Integer, nullable=False)
    # Armazena o tipo da entidade (ex: 'CLIENTE' ou 'FORNECEDOR')
    tipo_entidade: Mapped[EntityType] = mapped_column(SQLAlchemyEnum(EntityType), nullable=False)
    # (Nota: O 'backref' do modelo Cliente criará um atributo 'cliente' aqui)

    # --- Campos de endereço ---
    logradouro: Mapped[str] = mapped_column(String(255), nullable=False, doc="Nome da rua, avenida, etc.")
    numero: Mapped[str] = mapped_column(String(20), nullable=False, doc="Número do endereço")
    complemento: Mapped[str | None] = mapped_column(String(100), nullable=True, doc="Complemento do endereço (opcional)")
    bairro: Mapped[str] = mapped_column(String(100), nullable=False, doc="Bairro")
    cidade: Mapped[str] = mapped_column(String(100), nullable=False, doc="Cidade")
    estado: Mapped[State] = mapped_column(SQLAlchemyEnum(State), nullable=False, doc="Estado (UF)")
    cep: Mapped[str] = mapped_column(String(10), nullable=False, doc="CEP")