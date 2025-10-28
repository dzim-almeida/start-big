# ---------------------------------------------------------------------------
# ARQUIVO: endereco.py
# DESCRIÇÃO: Modelo SQLAlchemy para a tabela 'enderecos', que representa
#            os endereços vinculados aos clientes.
# ---------------------------------------------------------------------------

from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import Enum as SQLAlchemyEnum

from app.db.base import Base
from app.core.enum import State  # Enum dos estados brasileiros

# =========================
# Modelo SQLAlchemy: Endereco
# =========================
class Endereco(Base):
    """
    Representa a tabela 'enderecos'. Cada registro é um endereço
    associado a um cliente.
    """
    __tablename__ = "enderecos"

    # Chave primária
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Chave estrangeira referenciando 'clientes.id'
    id_cliente: Mapped[int] = mapped_column(Integer, ForeignKey("clientes.id"), nullable=False)

    # Campos de endereço
    logradouro: Mapped[str] = mapped_column(String(255), nullable=False, doc="Nome da rua, avenida, etc.")
    numero: Mapped[str] = mapped_column(String(20), nullable=False, doc="Número do endereço")
    complemento: Mapped[str | None] = mapped_column(String(100), nullable=True, doc="Complemento do endereço (opcional)")
    bairro: Mapped[str] = mapped_column(String(100), nullable=False, doc="Bairro")
    cidade: Mapped[str] = mapped_column(String(100), nullable=False, doc="Cidade")
    estado: Mapped[State] = mapped_column(SQLAlchemyEnum(State), nullable=False, doc="Estado (UF)")
    cep: Mapped[str] = mapped_column(String(10), nullable=False, doc="CEP")

    # Relacionamento Muitos-para-Um com o modelo Cliente
    # 'back_populates' aponta para o atributo 'endereco' no modelo Cliente
    cliente = relationship(
        "Cliente",
        back_populates="endereco",
        doc="Relacionamento com o cliente proprietário do endereço"
    )