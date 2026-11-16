# ---------------------------------------------------------------------------
# ARQUIVO: db/models/venda_produto.py
# DESCRICAO: Modelo SQLAlchemy para a tabela 'produtos_venda'.
#            Tabela pivo do carrinho. Congela precos e aceita itens avulsos.
# ---------------------------------------------------------------------------

from sqlalchemy import Float, Integer, String, ForeignKey, CheckConstraint, Enum as SqlAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING
from app.core.enum import TipoProdutoVenda

from app.db.base import Base

if TYPE_CHECKING:
    from .venda import Venda
    from .produto import Produto
    from .produto_embalagem import ProdutoEmbalagem


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
    descricao_avulsa: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Descricao obrigatoria se produto_id for nulo"
    )
    # Float desde 07/10/2026 (venda fracionada: 3,5 kg), SEM migration — mesma
    # decisão de estoque.py: o SQLite guarda 3.5 numa coluna INTEGER sem perda
    # (test/db/test_quantidade_fracionada_venda_schema_antigo.py).
    quantidade: Mapped[float] = mapped_column(Float, nullable=False, doc="Quantidade do item vendido")
    valor_unitario: Mapped[int] = mapped_column(Integer, nullable=False, doc="Preco unitario congelado no ato da inclusao (centavos)")
    # Custo declarado a mao, so faz sentido em item AVULSO. Produto CADASTRADO
    # da baixa no estoque e tem o custo congelado no livro (movimentacoes_estoque);
    # o avulso nao passa por la, entao sem este campo ele entrava no relatorio
    # como receita sem custo nenhum e inflava o lucro.
    #
    # E INTERNO: nao sai em nenhuma via impressa, igual ao equivalente na OS.
    custo_unitario: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Custo unitario que a loja teve com este item avulso (centavos). Interno: nunca impresso."
    )
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

    # --- Regra de preço por quantidade (§6.1, fase 5) ---
    # Congelado na linha, como o preço (D6): mudar a regra amanhã não reescreve
    # a venda de hoje.
    #
    # `desconto_regra` é SEPARADO de `desconto` de propósito. `desconto` é do
    # operador: o rateio do desconto da venda o sobrescreve, a finalização o
    # zera acima do limite da loja, e a tela o devolve no PATCH. Guardar a R1/R3
    # ali faria a regra sumir no checkout ou contar duas vezes.
    #
    # R2 ("a partir de N") não usa desconto: muda `valor_unitario` (dá centavos
    # exatos) e guarda o preço cheio em `valor_unitario_tabela`.
    desconto_regra: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0",
        doc="Desconto da regra de preço R1/R3 (centavos). Fora do limite de desconto do operador",
    )
    regra_preco: Mapped[Optional[str]] = mapped_column(
        String(12), nullable=True,
        doc="R1, R2, R3 — regra aplicada; MANUAL = preço trocado pelo gerente (as regras não mexem)",
    )
    regra_descricao: Mapped[Optional[str]] = mapped_column(
        String(80), nullable=True, doc="Como a linha mostra a regra ('Preço de fardo: 1 FD')"
    )
    valor_unitario_tabela: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        doc="Preço cheio da unidade antes da R2 (centavos) — o que a tela mostra riscado",
    )

    @property
    def quantidade_base(self) -> float:
        """Quantas unidades do produto a linha representa (2 FD de 12 = 24)."""
        return (self.quantidade or 0) * (self.fator_embalagem or 1)

    @property
    def desconto_total(self) -> int:
        """Operador + regra: o que vai no vDesc da nota e sai do faturamento."""
        return (self.desconto or 0) + (self.desconto_regra or 0)

    @property
    def total(self):
        return self.subtotal - self.desconto_total
    @property
    def imagem_url(self):
        if self.tipo_produto == TipoProdutoVenda.CADASTRADO and self.produto:
            return self.produto.imagem_url
        return None

    @property
    def unidade_medida(self):
        if self.tipo_produto == TipoProdutoVenda.CADASTRADO and self.produto:
            return self.produto.unidade_medida
        return None

    @property
    def estoque_disponivel(self):
        if self.tipo_produto == TipoProdutoVenda.CADASTRADO and self.produto and self.produto.estoque:
            return self.produto.estoque.quantidade
        return None

    # --- Relacionamentos ---
    venda: Mapped["Venda"] = relationship(back_populates="itens")
    produto: Mapped[Optional["Produto"]] = relationship(doc="Produto do catalogo associado")
    # So para a nota (cEAN do fardo, fase 4). Sigla e fator NAO vem daqui: estao
    # congelados na linha.
    embalagem: Mapped[Optional["ProdutoEmbalagem"]] = relationship(doc="Embalagem vendida (fardo/caixa)")
