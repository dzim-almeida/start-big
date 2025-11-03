# ---------------------------------------------------------------------------
# ARQUIVO: fonecedor.py
# DESCRIÇÃO: Modelo SQLAlchemy para a tabela 'fornecedores'.
# ---------------------------------------------------------------------------

from sqlalchemy import Integer, String, and_
from sqlalchemy.orm import relationship, Mapped, mapped_column, foreign

from app.db.models.endereco import Endereco
from app.db.base import Base
from app.core.enum import EntityType # (Necessário para a primaryjoin)

class Fornecedor(Base):
    """
    Representa a tabela 'fornecedores', contendo os dados de
    um fornecedor de produtos.
    """
    __tablename__ = "fornecedores"

    # Chave primária
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, doc="ID único do fornecedor (Chave primária)")
    
    # Campos de dados do fornecedor
    nome: Mapped[str] = mapped_column(String(255, collation="NOCASE"), index=True, nullable=False, doc="Nome do fornecedor (Pessoa Física ou Contato)")
    cnpj: Mapped[str] = mapped_column(String(14), index=True, nullable=False, doc="CNPJ do fornecedor (14 dígitos)")
    nome_fantasia: Mapped[str] = mapped_column(String(255, collation="NOCASE"), index=True, nullable=False, doc="Nome fantasia da empresa fornecedora")
    ie: Mapped[str | None] = mapped_column(String(14), unique=True, nullable=True, doc="Inscrição Estadual (IE) do fornecedor")

    # Relação Lado "Um" (Fornecedor) para "Muitos" (Produto)
    produto = relationship(
        "Produto",
        back_populates="fornecedor",
        doc="Relacionamento um-para-muitos com os produtos deste fornecedor",
        uselist=True # Define que um fornecedor pode ter múltiplos produtos
    )
    
    # Relação Lado "Um" (Fornecedor) para "Muitos" (Endereco) - Polimórfica
    endereco = relationship(
        "Endereco",
        # Junção manual para relação polimórfica
        primaryjoin="and_(foreign(Endereco.id_entidade) == Fornecedor.id, foreign(Endereco.tipo_entidade) == 'FORNECEDOR')",
        cascade="all, delete-orphan",
        uselist=True, # Define que um fornecedor pode ter múltiplos endereços
        # Evita conflitos com o relacionamento 'Cliente.endereco'
        overlaps="endereco",
        doc="Relacionamento polimórfico um-para-muitos com os endereços"
    )