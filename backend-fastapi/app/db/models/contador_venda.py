from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ContadorVenda(Base):
    """Contador sequencial de vendas finalizadas. Contém sempre uma única linha."""

    __tablename__ = "contador_venda"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    proximo_numero: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        doc="Próximo número a ser atribuído a uma venda finalizada",
    )
