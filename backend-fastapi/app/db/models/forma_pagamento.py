from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, List

from app.db.base import Base

if TYPE_CHECKING:
    from .ordem_servico_pagamento import OrdemServicoPagamento


class FormaPagamento(Base):
    """Catalogo de formas de pagamento aceitas para OS."""

    __tablename__ = "formas_pagamento"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, doc="ID unico da forma de pagamento (PK)")
    nome: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, doc="Nome da forma de pagamento")
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, doc="Status ativo/inativo")

    pagamentos: Mapped[List["OrdemServicoPagamento"]] = relationship(
        "OrdemServicoPagamento",
        back_populates="forma_pagamento",
        doc="Pagamentos de OS associados a esta forma de pagamento"
    )
