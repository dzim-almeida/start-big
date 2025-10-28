# ---------------------------------------------------------------------------
# ARQUIVO: cliente.py
# DESCRIÇÃO: Modelos SQLAlchemy para as tabelas 'clientes' e 'clientes_pf'.
#            Define a hierarquia de herança polimórfica, onde 'Cliente' é a
#            classe base e 'ClientePF' é uma especialização (filha).
# ---------------------------------------------------------------------------

from sqlalchemy import Integer, String, Date, ForeignKey, Enum as SqlAlchemyEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.base import Base
from app.core.enum import Gender, ClientType
from app.db.models.endereco import Endereco # Importa o modelo Endereco para o relationship

# =========================
# Modelo SQLAlchemy: Cliente (Classe Base)
# =========================

class Cliente(Base):
    """
    Representa a tabela base 'clientes', contendo dados comuns
    a todos os tipos de clientes (PF, PJ, etc.).
    """
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Coluna discriminadora para o polimorfismo ('PF' ou 'PJ')
    tipo: Mapped[ClientType] = mapped_column(SqlAlchemyEnum(ClientType), nullable=False)
    
    email: Mapped[str | None] = mapped_column(String(255, collation="NOCASE"), unique=True, nullable=True)
    contato: Mapped[str | None] = mapped_column(String(20), nullable=True)
    observacoes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relação 1-para-Muitos com Endereco
    # Um cliente pode ter vários endereços
    endereco = relationship(
        "Endereco",
        back_populates="cliente", # Aponta para o atributo 'cliente' no modelo Endereco
        cascade="all, delete-orphan", # Garante que os endereços sejam deletados junto com o cliente
        uselist=True, # Indica que este lado da relação é uma lista
    )

    # CONFIGURAÇÃO DO POLIMORFISMO
    __mapper_args__ = {
        'polymorphic_on': tipo,      # Coluna que define o tipo
        'polymorphic_identity': 'cliente' # Identidade desta classe base
    }

# ==========================================
# Modelo SQLAlchemy: Cliente Pessoa Física (Classe Filha)
# ==========================================
class ClientePF(Cliente): # Herda da classe base 'Cliente'
    """
    Representa a tabela 'clientes_pf', contendo dados específicos
    de clientes do tipo Pessoa Física. Utiliza herança de tabela unida.
    """
    __tablename__ = "clientes_pf"

    # Chave primária que também é chave estrangeira para 'clientes.id'
    id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), primary_key=True, index=True)
    
    # Nome completo
    nome: Mapped[str] = mapped_column(String(255, collation="NOCASE"), index=True, nullable=False)
    
    # CPF, obrigatório e único
    cpf: Mapped[str] = mapped_column(String(11), unique=True, index=True, nullable=False)
    
    # RG, pode ser nulo e único
    rg: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    
    # Enum de gênero
    genero: Mapped[Gender | None] = mapped_column(SqlAlchemyEnum(Gender), nullable=True)
    
    # Data de nascimento
    data_nascimento: Mapped[Date | None] = mapped_column(Date, nullable=True)

    # CONFIGURAÇÃO DO POLIMORFISMO PARA A CLASSE FILHA
    __mapper_args__ = {
        'polymorphic_identity': ClientType.PF.value, # Mapeia esta classe ao valor 'PF' do Enum
    }

# ==========================================
# Modelo SQLAlchemy: Cliente Pessoa Jurídica (Classe Filha)
# ==========================================
class ClientePJ(Cliente): # Herda da classe base 'Cliente'
    """
    Representa a tabela 'clientes_PJ', contendo dados específicos
    de clientes do tipo Pessoa Jurídica. Utiliza herança de tabela unida.
    """
    __tablename__ = "clientes_pj"

    # Chave primária que também é chave estrangeira para 'clientes.id'
    id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), primary_key=True, index=True)
    
    # Razão social, obrigatório e único
    razao_social: Mapped[str] = mapped_column(String(255, collation="NOCASE"), index=True, nullable=False)
    
    # CNPJ, obrigatório e único
    cnpj: Mapped[str] = mapped_column(String(14), unique=True, index=True, nullable=False)
    
    # Nome fantasia, obrigatório
    nome_fantasia: Mapped[str] = mapped_column(String(255, collation="NOCASE"), index=True, nullable=False)
    
    # Inscrição Estadual, opcional e único
    ie: Mapped[str | None] = mapped_column(String(14), unique=True, nullable=True)
    
    # Reponsável pela empresa, opcional
    responsavel: Mapped[str | None] = mapped_column(String(255, collation="NOCASE"), nullable=True)

    # CONFIGURAÇÃO DO POLIMORFISMO PARA A CLASSE FILHA
    __mapper_args__ = {
        'polymorphic_identity': ClientType.PJ.value, # Mapeia esta classe ao valor 'PJ' do Enum
    }

