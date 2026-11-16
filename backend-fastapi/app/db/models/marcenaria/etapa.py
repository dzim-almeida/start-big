# ---------------------------------------------------------------------------
# ARQUIVO: app/db/models/marcenaria/etapa.py
# DESCRICAO: As etapas de producao de cada movel aprovado (Spec 12A, secao 5).
# ---------------------------------------------------------------------------
"""
Na aprovacao, cada movel INTERNO recebe uma COPIA das etapas padrao da
configuracao (Corte -> Borda -> Furacao -> Montagem -> Embalagem), que pode ser
editada naquele movel (P1). Cada etapa passa por:

    PENDENTE -> EM_EXECUCAO -> CONCLUIDA

com quem fez e quando. Um movel com quantidade 3 tem UM conjunto de etapas
(D2): o marceneiro corta e monta os iguais juntos.

O nome do responsavel e de quem concluiu e COPIADO (texto): sobrevive a troca
de nome ou a saida do funcionario, como o resto do historico.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.marcenaria.ambiente import MarcenariaMovel


class StatusEtapa:
    """Os status de uma etapa (D7-D9). Texto gravado no banco."""
    PENDENTE = "PENDENTE"
    EM_EXECUCAO = "EM_EXECUCAO"
    CONCLUIDA = "CONCLUIDA"


class MarcenariaEtapa(Base):
    """Uma etapa de producao de um movel."""
    __tablename__ = "marcenaria_etapas"
    __table_args__ = (
        # O nome nao repete no movel. Maiusculas: o servico confere antes
        # ("corte" e "Corte" sao a mesma etapa para quem le a OS).
        UniqueConstraint("movel_id", "nome", name="uq_marcenaria_etapas_movel_nome"),
        Index("ix_marcenaria_etapas_movel", "movel_id", "ordem"),
        Index("ix_marcenaria_etapas_status", "status"),          # o quadro da fabrica conta por status
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    movel_id: Mapped[int] = mapped_column(
        ForeignKey("marcenaria_moveis.id", ondelete="CASCADE"), nullable=False,
    )
    nome: Mapped[str] = mapped_column(String(60), nullable=False)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(12), nullable=False, default=StatusEtapa.PENDENTE, server_default=StatusEtapa.PENDENTE,
    )
    # Quem esta fazendo (padrao: o funcionario do usuario logado, D7).
    responsavel_funcionario_id: Mapped[Optional[int]] = mapped_column(ForeignKey("funcionarios.id"), nullable=True)
    responsavel_nome: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    iniciada_em: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)     # UTC
    concluida_em: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)    # UTC
    concluida_por_nome: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)

    movel: Mapped["MarcenariaMovel"] = relationship("MarcenariaMovel", back_populates="etapas")
