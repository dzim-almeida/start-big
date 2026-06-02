# ---------------------------------------------------------------------------
# ARQUIVO: db/models/orcamento.py
# DESCRICAO: Modelo SQLAlchemy para a tabela 'orcamentos'.
#            Simulacao de valores que pode ser convertida em venda.
# ---------------------------------------------------------------------------

from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from .funcionario import Funcionario
    from .venda import Venda
    from .orcamento_produto import OrcamentoProduto


class Orcamento(Base):
    """Modelo ORM que representa um orcamento na tabela 'orcamentos'."""

    __tablename__ = "orcamentos"
    __table_args__ = (
        CheckConstraint("subtotal >= 0", name="ck_orcamento_subtotal_nao_negativo"),
        CheckConstraint("entrega >= 0", name="ck_orcamento_entrega_nao_negativo"),
        CheckConstraint("total >= 0", name="ck_orcamento_total_nao_negativo"),
    )

    # --- Identificacao (id = numero_orcamento) ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, doc="ID unico do orcamento (PK)")

    # --- Vinculos ---
    funcionario_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("funcionarios.id"),
        nullable=False,
        index=True,
        doc="Funcionario responsavel pelo orcamento (FK)"
    )
    venda_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("vendas.id", ondelete="SET NULL"),
        nullable=True,
        doc="Venda criada a partir deste orcamento (FK)"
    )

    # --- Status ---
    convertido: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, doc="Indica se foi convertido em venda")
    observacao: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        doc="Campo livre para anotacoes ou observacoes sobre o orcamento"
    )

    # --- Financeiro (valores em centavos) ---
    subtotal: Mapped[int] = mapped_column(Integer, default=0, nullable=False, doc="Soma dos itens sem descontos e fretes (centavos)")
    entrega: Mapped[int] = mapped_column(Integer, default=0, nullable=False, doc="Valor do frete/motoboy (centavos)")
    total: Mapped[int] = mapped_column(Integer, default=0, nullable=False, doc="(subtotal + entrega) - (descontos) (centavos)")

    @property
    def total_bruto(self):
        total_itens = sum(item.subtotal for item in self.itens)
        return total_itens + (self.entrega or 0)

    @property
    def descontos(self):
        return sum(item.desconto for item in self.itens)

    # --- Datas ---
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, doc="Data de criacao do orcamento")
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, doc="Ultima alteracao no orcamento")

    # --- Relacionamentos ---
    funcionario: Mapped["Funcionario"] = relationship(
        "Funcionario",
        back_populates="orcamentos",
        doc="Funcionario responsavel pelo orcamento"
    )
    venda: Mapped[Optional["Venda"]] = relationship(
        "Venda",
        doc="Venda criada a partir deste orcamento"
    )
    itens: Mapped[List["OrcamentoProduto"]] = relationship(
        "OrcamentoProduto",
        back_populates="orcamento",
        cascade="all, delete-orphan",
        doc="Itens do orcamento"
    )
