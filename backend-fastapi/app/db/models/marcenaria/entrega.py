# ---------------------------------------------------------------------------
# ARQUIVO: app/db/models/marcenaria/entrega.py
# DESCRICAO: A entrega e a instalacao da obra (Spec 13A, secao 5): a entrega
#            de cada ambiente, as pendencias, as fotos e os agendamentos.
# ---------------------------------------------------------------------------
"""
Na aprovacao, cada AMBIENTE com movel aprovado recebe uma entrega PENDENTE
com uma COPIA do checklist de vistoria da configuracao (D1). O termo do
ambiente vai para a obra no papel; quando volta assinado, o resultado e
"passado a limpo" aqui (P3):

    PENDENTE -> CONFORME  ou  COM_RESSALVAS (com pelo menos uma pendencia)

Os montadores sao guardados como lista JSON com o NOME copiado: sobrevive a
troca de nome ou a saida do funcionario, como o resto do historico.
"""

from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.marcenaria.ambiente import MarcenariaAmbiente
    from app.db.models.ordem_servico_foto import OrdemServicoFoto


class SituacaoEntrega:
    """A situacao da entrega de um ambiente (D4). Texto gravado no banco."""
    PENDENTE = "PENDENTE"
    CONFORME = "CONFORME"
    COM_RESSALVAS = "COM_RESSALVAS"


class SituacaoPendencia:
    """A situacao de uma pendencia (D6)."""
    ABERTA = "ABERTA"
    RESOLVIDA = "RESOLVIDA"


class TipoFotoEntrega:
    """De que e a foto (D7): o termo assinado ou a montagem."""
    TERMO = "TERMO"
    MONTAGEM = "MONTAGEM"


class MarcenariaEntrega(Base):
    """A entrega de UM ambiente da OS (I6: o termo e por ambiente)."""
    __tablename__ = "marcenaria_entregas"
    __table_args__ = (
        UniqueConstraint("os_id", "ambiente_id", name="uq_marcenaria_entregas_os_ambiente"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    os_id: Mapped[int] = mapped_column(ForeignKey("ordens_servico.id"), nullable=False)
    ambiente_id: Mapped[int] = mapped_column(ForeignKey("marcenaria_ambientes.id"), nullable=False)
    # [{"texto": "Alinhamento de portas", "marcacao": null | "ok" | "nao_ok"}] (D2, D4)
    checklist: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    situacao: Mapped[str] = mapped_column(
        String(14), nullable=False, default=SituacaoEntrega.PENDENTE, server_default=SituacaoEntrega.PENDENTE,
    )
    data_entrega: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    # [{"funcionario_id": 4, "nome": "Carlos"}] -- copia dos nomes (I4)
    montadores: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    recebido_por: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    observacoes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    registrado_por_nome: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    registrado_em: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)      # UTC

    ambiente: Mapped["MarcenariaAmbiente"] = relationship("MarcenariaAmbiente")
    # Apagar a entrega apaga as pendencias e os VINCULOS das fotos (a foto da OS fica).
    pendencias: Mapped[list["MarcenariaPendencia"]] = relationship(
        "MarcenariaPendencia", back_populates="entrega", cascade="all, delete-orphan",
        order_by="MarcenariaPendencia.id",
    )
    fotos: Mapped[list["MarcenariaEntregaFoto"]] = relationship(
        "MarcenariaEntregaFoto", back_populates="entrega", cascade="all, delete-orphan",
        order_by="MarcenariaEntregaFoto.id",
    )


class MarcenariaPendencia(Base):
    """Algo que ficou por fazer na obra (I3). Pode nascer depois da finalizacao (D6)."""
    __tablename__ = "marcenaria_pendencias"
    __table_args__ = (Index("ix_marcenaria_pendencias_aberta", "situacao"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entrega_id: Mapped[int] = mapped_column(
        ForeignKey("marcenaria_entregas.id", ondelete="CASCADE"), nullable=False,
    )
    descricao: Mapped[str] = mapped_column(String(300), nullable=False)
    situacao: Mapped[str] = mapped_column(
        String(10), nullable=False, default=SituacaoPendencia.ABERTA, server_default=SituacaoPendencia.ABERTA,
    )
    criada_em: Mapped[datetime] = mapped_column(DateTime, nullable=False)                   # UTC
    criada_por_nome: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    resolucao: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    resolvida_em: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    resolvida_por_nome: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)

    entrega: Mapped["MarcenariaEntrega"] = relationship("MarcenariaEntrega", back_populates="pendencias")


class MarcenariaEntregaFoto(Base):
    """O VINCULO entre uma foto da OS e a entrega de um ambiente (D7).

    A foto em si e uma foto da OS (`ordem_servico_fotos`, mesmo pipeline e
    galeria). Excluir a foto pela galeria da OS apaga este vinculo (CASCADE).
    """
    __tablename__ = "marcenaria_entrega_fotos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entrega_id: Mapped[int] = mapped_column(
        ForeignKey("marcenaria_entregas.id", ondelete="CASCADE"), nullable=False,
    )
    os_foto_id: Mapped[int] = mapped_column(
        ForeignKey("ordem_servico_fotos.id", ondelete="CASCADE"), nullable=False,
    )
    tipo: Mapped[str] = mapped_column(String(10), nullable=False)          # TERMO | MONTAGEM

    entrega: Mapped["MarcenariaEntrega"] = relationship("MarcenariaEntrega", back_populates="fotos")
    # So leitura daqui: a foto e da OS (sem `back_populates` no model compartilhado).
    foto: Mapped["OrdemServicoFoto"] = relationship("OrdemServicoFoto", viewonly=True)


class MarcenariaAgendamento(Base):
    """Uma visita de instalacao: data, ambientes e montadores (I5, I6)."""
    __tablename__ = "marcenaria_agendamentos"
    __table_args__ = (Index("ix_marcenaria_agendamentos_data", "data"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    os_id: Mapped[int] = mapped_column(ForeignKey("ordens_servico.id"), nullable=False)
    data: Mapped[date] = mapped_column(Date, nullable=False)
    hora_inicio: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)            # "08:00"
    ambiente_ids: Mapped[list] = mapped_column(JSON, nullable=False)                         # [1, 3]
    # [{"funcionario_id": 4, "nome": "Carlos"}] -- copia dos nomes (I4)
    montadores: Mapped[list] = mapped_column(JSON, nullable=False)
    observacao: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    criado_por_nome: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False)                    # UTC
