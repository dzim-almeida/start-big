# ---------------------------------------------------------------------------
# ARQUIVO: db/models/orcamento_produto.py
# DESCRICAO: Modelo SQLAlchemy para a tabela 'orcamentos_produtos'.
#            Tabela pivo dos itens de um orcamento.
# ---------------------------------------------------------------------------

from sqlalchemy import Float, Integer, String, ForeignKey, CheckConstraint, Enum as SqlAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING
from app.core.enum import TipoProdutoVenda

from app.db.base import Base

if TYPE_CHECKING:
    from .orcamento import Orcamento
    from .produto import Produto


class OrcamentoProduto(Base):
    """Modelo ORM que representa um item do orcamento na tabela 'orcamentos_produtos'."""

    __tablename__ = "orcamentos_produtos"
    __table_args__ = (
        CheckConstraint("quantidade > 0", name="ck_orcamento_produto_qtd_positiva"),
        CheckConstraint("valor_unitario >= 0", name="ck_orcamento_produto_valor_unitario_nao_negativo"),
        CheckConstraint("desconto >= 0", name="ck_orcamento_produto_desconto_nao_negativo"),
        CheckConstraint(
            "(produto_id IS NOT NULL) OR (descricao_avulsa IS NOT NULL)",
            name="ck_orcamento_produto_referencia_obrigatoria"
        ),
        CheckConstraint(
            "((tipo_produto = 'CADASTRADO') AND (produto_id IS NOT NULL)) OR "
            "((tipo_produto = 'AVULSO') AND (descricao_avulsa IS NOT NULL) AND (produto_id IS NULL))",
            name="ck_orcamento_produto_tipo_referencia_consistente"
        ),
    )

    # --- Identificacao ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, doc="ID da linha do orcamento (PK)")

    # --- Vinculos ---
    orcamento_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("orcamentos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Referencia ao orcamento matriz (FK)"
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
        doc="Tipo do produto no orcamento"
    )

    @property
    def nome(self):
        if self.tipo_produto == TipoProdutoVenda.CADASTRADO and self.produto:
            return self.produto.nome
        return self.descricao_avulsa

    @property
    def sku(self):
        if self.tipo_produto == TipoProdutoVenda.CADASTRADO and self.produto:
            return self.produto.codigo_produto
        return None

    @property
    def unidade_medida(self):
        """A tela decide pela unidade se a linha aceita 3,5 (venda fracionada, D1)."""
        if self.tipo_produto == TipoProdutoVenda.CADASTRADO and self.produto:
            return self.produto.unidade_medida
        return None

    descricao_avulsa: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Descricao obrigatoria se produto_id for nulo"
    )
    # Float desde 07/10/2026 (venda fracionada: 3,5 kg), SEM migration — mesma
    # decisão de estoque.py: o SQLite guarda 3.5 numa coluna INTEGER sem perda
    # (test/db/test_quantidade_fracionada_venda_schema_antigo.py).
    quantidade: Mapped[float] = mapped_column(Float, nullable=False, doc="Quantidade do item")
    valor_unitario: Mapped[int] = mapped_column(Integer, nullable=False, doc="Preco unitario congelado (centavos)")
    desconto: Mapped[int] = mapped_column(Integer, default=0, nullable=False, doc="Desconto especifico deste item (centavos)")
    subtotal: Mapped[int] = mapped_column(Integer, nullable=False, doc="Subtotal calculado (quantidade * valor_unitario)")

    # --- Embalagem (fardo/caixa) — plano de embalagens, D6 ---
    # A linha vende EMBALAGENS: `quantidade` = 2 (FD), `valor_unitario` = preço
    # do fardo. O estoque baixa `quantidade × fator_embalagem`. Sigla e fator são
    # congelados: mudar o cadastro amanhã não reescreve a baixa, o estorno nem a
    # nota de hoje. Linha sem embalagem (todas as antigas) tem fator 1.
    embalagem_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("produto_embalagens.id", ondelete="SET NULL"),
        nullable=True,
        doc="Embalagem vendida nesta linha (nulo = unidade)",
    )
    fator_embalagem: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1",
        doc="Unidades por embalagem, congelado (1 = unidade)",
    )
    sigla_embalagem: Mapped[Optional[str]] = mapped_column(String(6), nullable=True, doc="FD, CX... congelado")

    @property
    def quantidade_base(self) -> float:
        """Quantas unidades do produto a linha representa (2 FD de 12 = 24)."""
        return (self.quantidade or 0) * (self.fator_embalagem or 1)

    @property
    def total(self):
        return self.subtotal - self.desconto

    @property
    def imagem_url(self):
        if self.tipo_produto == TipoProdutoVenda.CADASTRADO and self.produto:
            return self.produto.imagem_url
        return None

    # --- Relacionamentos ---
    orcamento: Mapped["Orcamento"] = relationship(back_populates="itens")
    produto: Mapped[Optional["Produto"]] = relationship(doc="Produto do catalogo associado")
