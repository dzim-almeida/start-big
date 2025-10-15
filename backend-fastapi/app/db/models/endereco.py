# app/db/models/endereco.py

"""
Modelos SQLAlchemy para a tabela 'enderecos'.
Define o modelo Endereco, que representa os endereços vinculados aos clientes.
"""

from sqlalchemy import Column, Integer, String, Enum as SQLAlchemyEnum, ForeignKey  # type: ignore
from sqlalchemy.orm import relationship  # type: ignore

from app.db.base import Base
from app.core.enum import State  # Enum dos estados brasileiros

# =========================
# Modelo SQLAlchemy: Endereco
# =========================
class Endereco(Base):
    __tablename__ = "enderecos"

    # Chave primária
    id = Column(Integer, primary_key=True)

    # Chave estrangeira referenciando 'clientes.id'
    id_cliente = Column(Integer, ForeignKey("clientes.id"), nullable=False)

    # Campos de endereço
    logradouro = Column(String(255), nullable=False, doc="Nome da rua, avenida, etc.")
    numero = Column(String(20), nullable=False, doc="Número do endereço")
    complemento = Column(String(100), nullable=True, doc="Complemento do endereço (opcional)")
    bairro = Column(String(100), nullable=False, doc="Bairro")
    cidade = Column(String(100), nullable=False, doc="Cidade")
    estado = Column(SQLAlchemyEnum(State), nullable=False, doc="Estado (UF)")
    cep = Column(String(10), nullable=False, doc="CEP")

    # Relacionamento com o modelo Cliente
    endereco_cliente = relationship(
        "Cliente",
        back_populates="cliente_endereco",
        doc="Relacionamento com o cliente proprietário do endereço"
    )
