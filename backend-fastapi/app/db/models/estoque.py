# ---------------------------------------------------------------------------
# ARQUIVO: estoque.py
# DESCRIÇÃO: Modelo SQLAlchemy para a tabela 'estoque', representando
#            os dados de estoque de um produto (Relação 1-para-1 com Produto).
# ---------------------------------------------------------------------------

from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.models.produto import Produto
from app.db.base import Base

class Estoque(Base):
    """
    Representa a tabela 'estoque', contendo os dados de
    controle de estoque (quantidade, valores) de um Produto.
    """
    __tablename__ = "estoque"

    # Chave primária da tabela 'estoque' que também é chave estrangeira
    # referenciando 'produtos.id'. Isso estabelece a relação 1-para-1.
    id: Mapped[int] = mapped_column(Integer, ForeignKey("produtos.id"), primary_key=True, index=True, nullable=False, doc="ID do produto (Chave primária/estrangeira de 'produtos')")
    
    # Campos de controle de estoque
    quantidade: Mapped[int] = mapped_column(Integer, default=0, doc="Quantidade atual de itens em estoque")
    quantidade_ideal: Mapped[int | None] = mapped_column(Integer, nullable=True, doc="Quantidade de estoque considerada ideal")
    quantidade_minima: Mapped[int | None] = mapped_column(Integer, nullable=True, doc="Quantidade mínima para acionar alertas de reposição")
    
    # Valores (assumindo armazenamento em centavos)
    valor_entrada: Mapped[int | None] = mapped_column(Integer, nullable=True, doc="Valor de custo/entrada do produto (em centavos)")
    valor_varejo: Mapped[int] = mapped_column(Integer, nullable=False, doc="Valor de venda no varejo (em centavos)")
    valor_atacado: Mapped[int | None] = mapped_column(Integer, nullable=True, doc="Valor de venda no atacado (em centavos)")

    # Relação Lado "Um" (Estoque) para "Um" (Produto)
    produto = relationship(
        "Produto",
        back_populates="estoque",
        uselist=False, # Define a relação como 1-para-1
        doc="Relacionamento reverso Um-para-Um para o Produto"
    )