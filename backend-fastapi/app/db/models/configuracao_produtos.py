from datetime import datetime, UTC
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.empresa import Empresa


class ConfiguracaoProdutos(Base):
    __tablename__ = "configuracoes_produtos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    empresa_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("empresas.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # Campos obrigatórios no cadastro
    exigir_codigo_barras: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    exigir_categoria: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    exigir_preco_custo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Preços e exibição
    margem_lucro_padrao: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    utilizar_preco_atacado: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Controle de estoque
    permitir_venda_estoque_zerado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    quantidade_minima_padrao: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    unidade_medida_padrao: Mapped[str] = mapped_column(String(10), default="UN", nullable=False)

    data_atualizacao: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    empresa: Mapped["Empresa"] = relationship(
        "Empresa",
        back_populates="config_produtos",
    )

    def __repr__(self) -> str:
        return f"<ConfiguracaoProdutos(id={self.id}, empresa_id={self.empresa_id})>"
