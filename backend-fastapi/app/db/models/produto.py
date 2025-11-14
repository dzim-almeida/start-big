# ---------------------------------------------------------------------------
# ARQUIVO: produto.py
# DESCRIÇÃO: Modelo SQLAlchemy para a tabela 'produtos', representando
#            os dados de um produto no sistema.
# ---------------------------------------------------------------------------

from sqlalchemy import Integer, String, Boolean, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.base import Base
# Importar modelos relacionados para tipagem
# Assumindo que 'Estoque', e 'ProdutoFoto' estão em seus respectivos módulos.
from app.db.models.estoque import Estoque
from app.db.models.produto_fotos import ProdutoFoto
from typing import List
class Produto(Base):
    """
    Representa a tabela base 'produtos', contendo os dados de
    identificação de um produto.
    """
    __tablename__ = "produtos"

    # Chave primária do produto
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, doc="ID único do produto (Chave primária)")
    
    # Campos de dados do produto
    nome: Mapped[str] = mapped_column(String(255), index=True, nullable=False, doc="Nome completo do produto")
    # O Código_produto é nullable=True na coluna, mas a restrição de tabela garante que seja NULL se ativo=False
    codigo_produto: Mapped[str | None] = mapped_column(String(100), unique=True, index=True, nullable=True, doc="Código único (SKU, EAN, etc.) para identificação")
    unidade_medida: Mapped[str | None] = mapped_column(String(25), nullable=True, doc="Unidade de medida (ex: UN, KG, CX)")
    observacao: Mapped[str | None] = mapped_column(String(500), nullable=True, doc="Observações gerais sobre o produto")
    nota_fiscal: Mapped[str | None] = mapped_column(String(100), nullable=True, doc="Referência de nota fiscal de entrada ou origem")
    categoria: Mapped[str | None] = mapped_column(String(100), nullable=True, doc="Categoria à qual o produto pertence")
    marca: Mapped[str | None] = mapped_column(String(100), nullable=True, doc="Marca do produto")
    
    # Chave estrangeira para o fornecedor (Muitos-para-Um)
    # A tipagem Mapped[int | None] reflete o nullable=True
    fornecedor_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("fornecedores.id", ondelete="SET NULL"), nullable=True, doc="ID do fornecedor principal (FK)")

    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, doc="Define se o produto está ativo (True) ou desativado (False)")
    
    # Relação Lado "Muitos" (Produto) para "Um" (Fornecedor)
    # Tipagem simplificada: Um produto tem UM fornecedor (ou None, devido à FK SET NULL)
    fornecedor = relationship(
        "Fornecedor",
        back_populates="produto",
        doc="Relacionamento Muitos-para-Um com o Fornecedor"
    )
    
    # Relação Lado "Um" (Produto) para "Um" (Estoque)
    # Tipagem simplificada: Um produto tem UM estoque
    estoque: Mapped[Estoque] = relationship(
        "Estoque",
        back_populates="produto",
        cascade="all, delete-orphan", # Garante a exclusão do registro de Estoque ao deletar o Produto
        uselist=False, # Define a relação como 1-para-1
        doc="Relacionamento Um-para-Um com os dados de estoque"
    )

    # Relação Lado "Um" (Produto) para "Muitos" (Fotos)
    # Tipagem simplificada: Um produto tem uma lista de fotos
    fotos: Mapped[List[ProdutoFoto]] = relationship(
        "ProdutoFoto",
        back_populates="produto",
        cascade="all, delete-orphan", # Garante a exclusão de todas as Fotos ao deletar o Produto
        doc="Relacionamento de Um-para-Vários com Fotos"
    )

    # Restrições (Constraints)
    __table_args__ = (
        CheckConstraint(
            # Garante que o 'codigo_produto' seja obrigatório SOMENTE se o produto estiver 'ativo'
            # (ativo = FALSE) OR ((codigo_produto IS NOT NULL) AND (ativo = TRUE))
            "(NOT ativo) OR (codigo_produto IS NOT NULL)", 
            name='ck_codigo_produto_ativo_obrigatorio' 
        ),
    )