# ---------------------------------------------------------------------------
# ARQUIVO: fonecedor.py
# DESCRIÇÃO: Modelo SQLAlchemy para a tabela 'fornecedores'.
# ---------------------------------------------------------------------------

from sqlalchemy import Integer, String, Boolean, and_
from sqlalchemy.orm import relationship, Mapped, mapped_column, foreign
from typing import List, Optional

from app.db.models.endereco import Endereco # Importado Endereco
from app.db.models.produto import Produto as ProdutoModel
from app.db.base import Base
# from app.core.enum import EntityType # Não é necessário importar o Enum aqui se ele for usado apenas na primaryjoin

class Fornecedor(Base):
    """
    Representa a tabela 'fornecedores', contendo os dados de
    um fornecedor de produtos.
    """
    __tablename__ = "fornecedores"

    # Chave primária
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, doc="ID único do fornecedor (Chave primária)")
    
    # Campos de dados do fornecedor
    nome: Mapped[str] = mapped_column(String(255, collation="NOCASE"), index=True, nullable=False, doc="Nome ou Razão Social do fornecedor")
    cnpj: Mapped[str] = mapped_column(String(14), unique=True, index=True, nullable=False, doc="CNPJ do fornecedor (14 dígitos)")
    nome_fantasia: Mapped[str] = mapped_column(String(255, collation="NOCASE"), index=True, nullable=False, doc="Nome fantasia da empresa fornecedora")
    ie: Mapped[Optional[str]] = mapped_column(String(14), unique=True, nullable=True, doc="Inscrição Estadual (IE) do fornecedor")

    # Contato
    telefone: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, doc="Telefone de contato do fornecedor")
    celular: Mapped[Optional[str]] = mapped_column(String(11), nullable=True, doc="Celular de contato do fornecedor")
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, doc="Email para contato com fornecedor")
    representante: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, doc="Nome do representante da empresa fornecedora")

    # Uso de 'bool' para tipagem
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, doc="Define se um Fornecedor está ativo (True) ou desativado (False)")

    # Relação Lado "Um" (Fornecedor) para "Muitos" (Produto)
    # Tipagem: Lista de objetos Produto
    produto: Mapped[list[ProdutoModel]] = relationship(
        "Produto",
        back_populates="fornecedor",
        doc="Relacionamento um-para-muitos com os produtos deste fornecedor",
        # uselist=True é o padrão para list/List, mas pode ser omitido
    )
    
    # Relação Lado "Um" (Fornecedor) para "Muitos" (Endereco) - Polimórfica
    # Tipagem: Lista de objetos Endereco
    endereco: Mapped[List[Endereco]] = relationship(
        "Endereco",
        # Junção manual para relação polimórfica
        primaryjoin="and_(foreign(Endereco.id_entidade) == Fornecedor.id, foreign(Endereco.tipo_entidade) == 'FORNECEDOR')",
        cascade="all, delete-orphan",
        # uselist=True é o padrão
        overlaps="endereco",
        doc="Relacionamento polimórfico um-para-muitos com os endereços"
    )