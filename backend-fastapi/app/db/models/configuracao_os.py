from datetime import datetime, UTC
from typing import TYPE_CHECKING
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.empresa import Empresa


class ConfiguracaoOS(Base):
    """
    Configurações do módulo de Ordens de Serviço por empresa.
    Relacionamento 1:1 com Empresa.
    """
    __tablename__ = "configuracoes_os"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    empresa_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("empresas.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    prazo_entrega_padrao: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    garantia_padrao: Mapped[str] = mapped_column(String(20), default="90 dias", nullable=False)
    prazo_abandono_dias: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    taxa_diagnostico_padrao: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    data_atualizacao: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    empresa: Mapped["Empresa"] = relationship(
        "Empresa",
        back_populates="config_os",
    )

    def __repr__(self) -> str:
        return f"<ConfiguracaoOS(id={self.id}, empresa_id={self.empresa_id})>"
