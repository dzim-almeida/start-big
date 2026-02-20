from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Enum as SqlAlchemyEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enum import TipoEquipamento

from app.db.base import Base

if TYPE_CHECKING:
    from .cliente import Cliente
    from .ordem_servico import OrdemServico


class OrdemServicoEquipamento(Base):
    """Equipamento cadastrado para um cliente e reutilizavel em OS."""

    __tablename__ = "ordem_servico_equipamentos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, doc="ID unico do equipamento (PK)")

    cliente_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("clientes.id"),
        nullable=False,
        index=True,
        doc="ID do cliente proprietario do equipamento (FK)"
    )

    tipo_equipamento: Mapped[TipoEquipamento] = mapped_column(SqlAlchemyEnum(TipoEquipamento), default=TipoEquipamento.OUTROS, nullable=False, doc="Nome/tipo do equipamento")
    marca: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, doc="Marca do equipamento")
    modelo: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, doc="Modelo do equipamento")
    numero_serie: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, doc="Numero de serie")
    imei: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, doc="IMEI do aparelho")
    cor: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, doc="Cor do equipamento")
    
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, doc="Status ativo (soft delete)")
    data_criacao: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, doc="Data de criacao")
    data_atualizacao: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Data da ultima atualizacao"
    )

    cliente: Mapped["Cliente"] = relationship("Cliente", back_populates="equipamentos", doc="Cliente dono do equipamento")
    ordens_servico: Mapped[List["OrdemServico"]] = relationship(
        "OrdemServico",
        back_populates="equipamento_rel",
        doc="Ordens de servico associadas a este equipamento"
    )
