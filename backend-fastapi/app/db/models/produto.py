# ---------------------------------------------------------------------------
# ARQUIVO: produto.py
# DESCRIÇÃO: Modelo SQLAlchemy para a tabela 'produtos', representando
#            os dados de um produto no sistema.
# ---------------------------------------------------------------------------

from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.base import Base

class Produto(Base):
    """
    Representa a tabela base 'produtos', contendo os dados de
    identificação de um produto.
    """
    __tablename__ = "produtos"

    # Chave primária do produto
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, doc="ID único do produto (Chave primária)")
    
    # Campos de dados do produto
    nome: Mapped[str] = mapped_column(String(255), index=True, nullable=False, doc="Nome do produto")
    codigo_produto: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False, doc="Código único (SKU, EAN, etc.) para identificação")
    unidade_medida: Mapped[str | None] = mapped_column(String(25), nullable=True, doc="Unidade de medida (ex: UN, KG, CX)")
    observacao: Mapped[str | None] = mapped_column(String(500), nullable=True, doc="Observações gerais sobre o produto")
    nota_fiscal: Mapped[str | None] = mapped_column(String(100), nullable=True, doc="Nota fiscal de entrada ou referência")
    categoria: Mapped[str | None] = mapped_column(String(100), nullable=True, doc="Categoria à qual o produto pertence")
    marca: Mapped[str | None] = mapped_column(String(100), nullable=True, doc="Marca do produto")
    
    # Chave estrangeira para o fornecedor (Muitos-para-Um)
    fornecedor_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("fornecedores.id", ondelete="SET NULL"), nullable=True, doc="ID do fornecedor principal (FK)")
    
    # Relação Lado "Muitos" (Produto) para "Um" (Fornecedor)
    fornecedor = relationship(
        "Fornecedor",
        back_populates="produto",
        doc="Relacionamento Muitos-para-Um com o Fornecedor"
    )
    
    # Relação Lado "Um" (Produto) para "Um" (Estoque)
    estoque = relationship(
        "Estoque",
        back_populates="produto",
        cascade="all, delete-orphan", # Garante a exclusão do registro de Estoque ao deletar o Produto
        uselist=False, # Define a relação como 1-para-1
        doc="Relacionamento Um-para-Um com os dados de estoque"
    )

    fotos = relationship(
        "ProdutoFoto",
        back_populates="produto",
        cascade="all, delete-orphan", # Garante a exclusão de todas as Fotos ao deletar o Produto
        uselist=True, # Define a relação como 1-para-Vários
        doc="Relacionamento de Um-para-Vários com Fotos"
    )