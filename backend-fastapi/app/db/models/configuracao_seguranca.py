from datetime import datetime, UTC
from typing import Optional, TYPE_CHECKING
from sqlalchemy import JSON, Boolean, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.empresa import Empresa


class ConfiguracaoSeguranca(Base):
    __tablename__ = "configuracoes_seguranca"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    empresa_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("empresas.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    pin_gerente: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Lista de ids de seções do painel de configurações que exigem PIN para acessar
    secoes_protegidas: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    requer_pin_cancelar_venda: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requer_pin_reabrir_venda: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requer_pin_desconto_venda: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requer_pin_alterar_preco_venda: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    requer_pin_cancelar_os: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requer_pin_reabrir_os: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requer_pin_desconto_os: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    data_atualizacao: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    empresa: Mapped["Empresa"] = relationship(
        "Empresa",
        back_populates="config_seguranca",
    )

    def __repr__(self) -> str:
        return f"<ConfiguracaoSeguranca(id={self.id}, empresa_id={self.empresa_id})>"
