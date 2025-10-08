# Modelos SQLAlchemy para Clientes

from sqlalchemy import Column, Integer, String, Date, UniqueConstraint, ForeignKey, Enum as SqlAlchemyEnum  # type: ignore
from sqlalchemy.orm import relationship  # type: ignore
from app.db.base import Base
from app.core.enum import Genero, TipoCliente  # Enum de gênero

# =========================
# Modelo SQLAlchemy: Cliente
# =========================
class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(SqlAlchemyEnum(TipoCliente), nullable=False)  # 'PF' ou 'PJ'
    email = Column(String(255, collation="NOCASE"), unique=True, nullable=True)
    contato = Column(String(20), nullable=True)
    observacoes = Column(String(500), nullable=True)

    # Relação com endereço
    cliente_endereco = relationship(
        "Endereco",
        back_populates="endereco_cliente",
        uselist=True,
    )

    # Relação 1:1 com ClientePF
    pf = relationship(
        "ClientePF",
        back_populates="cliente_base",
        uselist=False,
        primaryjoin="Cliente.id==ClientePF.id"
    )

    __mapper_args__ = {
        'polymorphic_on': tipo,
        'polymorphic_identity': 'cliente'
    }

# ==========================================
# Modelo SQLAlchemy: Cliente Pessoa Física
# ==========================================
class ClientePF(Base):
    __tablename__ = "clientes_pf"

    # ID único do cliente PF, referenciando FK de clientes
    id = Column(Integer, ForeignKey("clientes.id"), primary_key=True, index=True)
    nome = Column(String(255, collation="NOCASE"), index=True, nullable=False)  # Nome completo
    cpf = Column(String(14), unique=True, index=True, nullable=False)         # CPF, obrigatório e único
    rg = Column(String(20), unique=True, nullable=True)                       # RG, pode ser nulo e único
    email = Column(String(255, collation="NOCASE"), unique=True, nullable=True) # Email, pode ser nulo e único
    genero = Column(SqlAlchemyEnum(Genero), nullable=True)                    # Enum de gênero: Masculino, Feminino, Outro
    data_nascimento = Column(Date, nullable=True)                             # Data de nascimento

    # Relação 1:1 com Cliente
    cliente_base = relationship(
        "Cliente",
        back_populates="pf",
        uselist=False,
        primaryjoin="Cliente.id==ClientePF.id"
    )

    # Restrição de unicidade para CPF e RG juntos
    __table_args__ = (
        UniqueConstraint('cpf', 'rg', name='_rg_cpf_uc'),
    )