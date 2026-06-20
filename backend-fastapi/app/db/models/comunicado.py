from datetime import datetime, UTC
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.funcionario import Funcionario


class Comunicado(Base):
    __tablename__ = "comunicados"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    empresa_id: Mapped[int] = mapped_column(Integer, ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, index=True)
    funcionario_autor_id: Mapped[int] = mapped_column(Integer, ForeignKey("funcionarios.id", ondelete="CASCADE"), nullable=False)
    titulo: Mapped[str] = mapped_column(String(100), nullable=False)
    mensagem: Mapped[str] = mapped_column(Text, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    autor: Mapped["Funcionario"] = relationship("Funcionario", foreign_keys=[funcionario_autor_id])
    leituras: Mapped[list["ComunicadoLeitura"]] = relationship("ComunicadoLeitura", back_populates="comunicado", cascade="all, delete-orphan")


class ComunicadoLeitura(Base):
    __tablename__ = "comunicados_leituras"
    __table_args__ = (UniqueConstraint("comunicado_id", "funcionario_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    comunicado_id: Mapped[int] = mapped_column(Integer, ForeignKey("comunicados.id", ondelete="CASCADE"), nullable=False)
    funcionario_id: Mapped[int] = mapped_column(Integer, ForeignKey("funcionarios.id", ondelete="CASCADE"), nullable=False)
    lido_em: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    comunicado: Mapped["Comunicado"] = relationship("Comunicado", back_populates="leituras")
