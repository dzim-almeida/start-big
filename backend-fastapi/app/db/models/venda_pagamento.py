# ---------------------------------------------------------------------------
# ARQUIVO: db/models/venda_pagamento.py
# DESCRICAO: Modelo SQLAlchemy para a tabela 'pagamentos_venda'.
#            Armazena multiplas formas de pagamento para uma unica venda.
# ---------------------------------------------------------------------------

from datetime import datetime
from sqlalchemy import Integer, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from .venda import Venda
    from .forma_pagamento import FormaPagamento


class PagamentoVenda(Base):
    """Modelo ORM que representa um pagamento de venda na tabela 'pagamentos_venda'."""

    __tablename__ = "pagamentos_venda"
    __table_args__ = (
        CheckConstraint("valor > 0", name="ck_pagamento_venda_valor_positivo"),
        CheckConstraint("(parcelado IS NOT NULL) AND (qtd_parcelas >= 1)", name="ck_pagamento_venda_parcelas_min_1"),
    )

    # --- Identificacao ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, doc="ID unico da transacao (PK)")

    # --- Vinculos ---
    venda_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vendas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Venda correspondente (FK)"
    )
    forma_pagamento_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("formas_pagamento.id"),
        nullable=False,
        doc="Forma de pagamento utilizada (FK)"
    )

    # --- Dados do Pagamento ---
    valor: Mapped[int] = mapped_column(Integer, nullable=False, doc="Fracao financeira paga neste metodo (centavos)")
    parcelado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True, doc="Flag indicando compra a prazo")
    qtd_parcelas: Mapped[int] = mapped_column(Integer, default=1, nullable=True, doc="Quantidade de parcelas (1 = a vista)")
    data_pagamento: Mapped[datetime] = mapped_column(DateTime, nullable=False, doc="Momento exato do registro do pagamento")

    # --- Relacionamentos ---
    venda: Mapped["Venda"] = relationship(back_populates="pagamentos")
    forma_pagamento: Mapped["FormaPagamento"] = relationship("FormaPagamento", back_populates="pagamentos_venda")
