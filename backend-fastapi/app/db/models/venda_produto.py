# ---------------------------------------------------------------------------
# ARQUIVO: db/models/venda_produto.py
# DESCRICAO: Modelo SQLAlchemy para a tabela 'produtos_venda'.
#            Tabela pivo do carrinho. Congela precos e aceita itens avulsos.
# ---------------------------------------------------------------------------

from sqlalchemy import Integer, String, ForeignKey, CheckConstraint, Enum as SqlAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING
from app.core.enum import TipoProdutoVenda

from app.db.base import Base

if TYPE_CHECKING:
    from .venda import Venda
    from .produto import Produto


class ProdutoVenda(Base):
    """Modelo ORM que representa um item do carrinho na tabela 'produtos_venda'."""

    __tablename__ = "produtos_venda"
    __table_args__ = (
        CheckConstraint("quantidade > 0", name="ck_produto_venda_qtd_positiva"),
        CheckConstraint("valor_unitario >= 0", name="ck_produto_venda_valor_unitario_nao_negativo"),
        CheckConstraint("desconto >= 0", name="ck_produto_venda_desconto_nao_negativo"),
        CheckConstraint(
            "(produto_id IS NOT NULL) OR (descricao_avulsa IS NOT NULL)",
            name="ck_produto_venda_referencia_obrigatoria"
        ),
        CheckConstraint(
            "((tipo_produto = 'CADASTRADO') AND (produto_id IS NOT NULL)) OR "
            "((tipo_produto = 'AVULSO') AND (descricao_avulsa IS NOT NULL) AND (produto_id IS NULL))",
            name="ck_produto_venda_tipo_referencia_consistente"
        ),
    )

    # --- Identificacao ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, doc="ID da linha do carrinho (PK)")

    # --- Vinculos ---
    venda_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vendas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Referencia a venda matriz (FK)"
    )
    produto_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("produtos.id", ondelete="SET NULL"),
        nullable=True,
        doc="Item de estoque. Nulo se for item avulso (FK)"
    )

    # --- Dados do Item ---
    tipo_produto: Mapped[TipoProdutoVenda] = mapped_column(
        SqlAlchemyEnum(TipoProdutoVenda),
        nullable=False,
        doc="Tipo do produto vendido"
    )
    descricao_avulsa: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Descricao obrigatoria se produto_id for nulo"
    )
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False, doc="Quantidade do item vendido")
    valor_unitario: Mapped[int] = mapped_column(Integer, nullable=False, doc="Preco unitario congelado no ato da inclusao (centavos)")
    desconto: Mapped[int] = mapped_column(Integer, default=0, nullable=False, doc="Desconto especifico deste item (centavos)")
    subtotal: Mapped[int] = mapped_column(Integer, nullable=False, doc="(valor_unitario * qtd) - desconto (centavos)")

    # --- Relacionamentos ---
    venda: Mapped["Venda"] = relationship(back_populates="itens")
    produto: Mapped[Optional["Produto"]] = relationship(doc="Produto do catalogo associado")
