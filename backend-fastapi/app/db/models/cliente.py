# ---------------------------------------------------------------------------
# ARQUIVO: cliente.py
# DESCRIÇÃO: Modelos SQLAlchemy para as tabelas 'clientes', 'clientes_pf',
#            e 'clientes_pj'. Define a hierarquia de herança polimórfica,
#            utilizando Herança de Tabela Unida.
# ---------------------------------------------------------------------------

from sqlalchemy import Integer, String, Boolean, Date, ForeignKey, Enum as SqlAlchemyEnum, and_
from sqlalchemy.orm import relationship, Mapped, mapped_column, foreign
from typing import List

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

    # Chave primária
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, doc="ID único do cliente (Chave primária)")
    
    # Uso de 'bool'
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, doc="Define se o cliente está ativo (True) ou desativado (False)")

    # Coluna discriminadora para o polimorfismo ('PF' ou 'PJ')
    tipo: Mapped[ClientType] = mapped_column(SqlAlchemyEnum(ClientType), nullable=False, doc="Tipo de cliente (PF ou PJ)")
    
    # Campos comuns
    email: Mapped[str | None] = mapped_column(String(255, collation="NOCASE"), unique=True, nullable=True, doc="Email do cliente")
    contato: Mapped[str | None] = mapped_column(String(20), nullable=True, doc="Telefone de contato do cliente")
    observacoes: Mapped[str | None] = mapped_column(String(500), nullable=True, doc="Observações gerais sobre o cliente")
    
    # Relação 1-para-Muitos com Endereco (Polimórfica)
    # Tipagem: Lista de objetos Endereco
    endereco: Mapped[List[Endereco]] = relationship(
        "Endereco",
        # Define a condição de junção manual para esta relação polimórfica
        primaryjoin="and_(foreign(Endereco.id_entidade) == Cliente.id, foreign(Endereco.tipo_entidade) == 'CLIENTE')",
        cascade="all, delete-orphan", 
        # uselist=True é o padrão
        overlaps="endereco",
        doc="Lista de endereços associados a este cliente"
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
    id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), primary_key=True, index=True, doc="ID do cliente (FK de 'clientes')")
    
    # Campos específicos de PF
    nome: Mapped[str] = mapped_column(String(255, collation="NOCASE"), index=True, nullable=False, doc="Nome completo do cliente")
    cpf: Mapped[str] = mapped_column(String(11), unique=True, index=True, nullable=False, doc="CPF do cliente (11 dígitos)")
    rg: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True, doc="RG do cliente")
    genero: Mapped[Gender | None] = mapped_column(SqlAlchemyEnum(Gender), nullable=True, doc="Gênero do cliente")
    data_nascimento: Mapped[Date | None] = mapped_column(Date, nullable=True, doc="Data de nascimento do cliente")

    # CONFIGURAÇÃO DO POLIMORFISMO PARA A CLASSE FILHA
    __mapper_args__ = {
        'polymorphic_identity': ClientType.PF.value, # Mapeia esta classe ao valor 'PF' do Enum
    }

# ==========================================
# Modelo SQLAlchemy: Cliente Pessoa Jurídica (Classe Filha)
# ==========================================
class ClientePJ(Cliente): # Herda da classe base 'Cliente'
    """
    Representa a tabela 'clientes_pj', contendo dados específicos
    de clientes do tipo Pessoa Jurídica. Utiliza herança de tabela unida.
    """
    __tablename__ = "clientes_pj"

    # Chave primária que também é chave estrangeira para 'clientes.id'
    id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), primary_key=True, index=True, doc="ID do cliente (FK de 'clientes')")
    
    # Campos específicos de PJ
    razao_social: Mapped[str] = mapped_column(String(255, collation="NOCASE"), index=True, nullable=False, doc="Razão social da empresa")
    cnpj: Mapped[str] = mapped_column(String(14), unique=True, index=True, nullable=False, doc="CNPJ da empresa (14 dígitos)")
    nome_fantasia: Mapped[str] = mapped_column(String(255, collation="NOCASE"), index=True, nullable=False, doc="Nome fantasia da empresa")
    ie: Mapped[str | None] = mapped_column(String(14), unique=True, nullable=True, doc="Inscrição Estadual (IE) da empresa")
    responsavel: Mapped[str | None] = mapped_column(String(255, collation="NOCASE"), nullable=True, doc="Nome do responsável ou contato principal")

    # CONFIGURAÇÃO DO POLIMORFISMO PARA A CLASSE FILHA
    __mapper_args__ = {
        'polymorphic_identity': ClientType.PJ.value, # Mapeia esta classe ao valor 'PJ' do Enum
    }