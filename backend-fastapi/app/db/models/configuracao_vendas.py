from datetime import datetime, UTC
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.empresa import Empresa


class ConfiguracaoVendas(Base):
    __tablename__ = "configuracoes_vendas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    empresa_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("empresas.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    permitir_desconto: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    desconto_maximo_percent: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    exigir_cliente_identificado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    acao_ao_finalizar: Mapped[str] = mapped_column(String(20), default="perguntar", nullable=False)

    data_atualizacao: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    empresa: Mapped["Empresa"] = relationship(
        "Empresa",
        back_populates="config_vendas",
    )
