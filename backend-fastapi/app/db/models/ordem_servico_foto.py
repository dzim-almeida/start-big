# ---------------------------------------------------------------------------
# ARQUIVO: db/models/ordem_servico_foto.py
# DESCRICAO: Modelo SQLAlchemy para a tabela 'ordem_servico_fotos'.
# ---------------------------------------------------------------------------

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from .ordem_servico import OrdemServico


class OrdemServicoFoto(Base):
    """Modelo ORM que representa uma foto de diagnostico de uma Ordem de Servico."""

    __tablename__ = "ordem_servico_fotos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, doc="ID unico da foto (PK)")

    ordem_servico_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ordens_servico.id", ondelete="CASCADE"),
        nullable=False,
        doc="ID da OS (FK)"
    )

    nome_arquivo: Mapped[str] = mapped_column(String(255), nullable=False, doc="Nome original do arquivo")
    url: Mapped[str] = mapped_column(String(500), nullable=False, doc="URL/caminho do arquivo")
    data_criacao: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, doc="Data de upload")

    # --- Relacionamentos ---
    ordem_servico: Mapped["OrdemServico"] = relationship(back_populates="fotos")
