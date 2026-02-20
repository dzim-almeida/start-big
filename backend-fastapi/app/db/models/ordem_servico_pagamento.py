# ---------------------------------------------------------------------------
# ARQUIVO: db/models/ordem_servico_pagamento.py
# DESCRICAO: Modelo SQLAlchemy para a tabela 'ordem_servico_pagamentos'.
# ---------------------------------------------------------------------------

from sqlalchemy import CheckConstraint, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from .forma_pagamento import FormaPagamento
    from .ordem_servico import OrdemServico


class OrdemServicoPagamento(Base):
    """Modelo ORM que representa um pagamento de uma Ordem de Servico."""

    __tablename__ = "ordem_servico_pagamentos"
    __table_args__ = (
        CheckConstraint("valor >= 0", name="ck_os_pagamento_valor_nao_negativo"),
        CheckConstraint("parcelas >= 1", name="ck_os_pagamento_parcelas_min_1"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, doc="ID unico do pagamento (PK)")

    ordem_servico_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ordens_servico.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="ID da OS (FK)"
    )

    forma_pagamento_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("formas_pagamento.id"),
        nullable=False,
        doc="ID da forma de pagamento"
    )
    valor: Mapped[int] = mapped_column(Integer, nullable=False, doc="Valor pago (centavos)")
    parcelas: Mapped[int] = mapped_column(Integer, default=1, nullable=False, doc="Numero de parcelas")
    bandeira_cartao: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, doc="Bandeira do cartao (VISA, MASTERCARD, etc)")
    detalhes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, doc="Detalhes adicionais do pagamento")

    # --- Relacionamentos ---
    ordem_servico: Mapped["OrdemServico"] = relationship(back_populates="pagamentos")
    forma_pagamento: Mapped["FormaPagamento"] = relationship(back_populates="pagamentos")
