# ---------------------------------------------------------------------------
# ARQUIVO: db/models/ordem_servico_item.py
# DESCRICAO: Modelo SQLAlchemy para a tabela 'ordem_servico_itens'.
# ---------------------------------------------------------------------------

from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from .ordem_servico import OrdemServico
    from .servico import Servico


class OrdemServicoItem(Base):
    """Modelo ORM que representa um item/servico dentro de uma Ordem de Servico."""

    __tablename__ = "ordem_servico_itens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, doc="ID unico do item (PK)")

    ordem_servico_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ordens_servico.id", ondelete="CASCADE"),
        nullable=False,
        doc="ID da OS (FK)"
    )

    servico_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("servicos.id", ondelete="SET NULL"),
        nullable=True,
        doc="ID do servico do catalogo (FK, nullable para itens customizados)"
    )

    descricao: Mapped[str] = mapped_column(String(255), nullable=False, doc="Descricao do item/servico")
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False, doc="Quantidade")
    valor_unitario: Mapped[int] = mapped_column(Integer, nullable=False, doc="Valor unitario (centavos)")
    valor_total: Mapped[int] = mapped_column(Integer, nullable=False, doc="Valor total (centavos)")

    # --- Relacionamentos ---
    ordem_servico: Mapped["OrdemServico"] = relationship(back_populates="itens")
    servico: Mapped[Optional["Servico"]] = relationship(doc="Servico do catalogo associado")
