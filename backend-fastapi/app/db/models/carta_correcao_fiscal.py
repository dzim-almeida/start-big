# ---------------------------------------------------------------------------
# ARQUIVO: app/db/models/carta_correcao_fiscal.py
# DESCRIÇÃO: Carta de Correção Eletrônica (CC-e) registrada numa NF-e.
#
# A carta é um EVENTO anexo à nota, como o cancelamento -- não é uma nova
# emissão: não consome número, não tem itens, não mexe em estoque. Uma NF-e
# aceita até 20 cartas e a SEFAZ considera vigente só a última; cada uma tem
# protocolo, XML e PDF próprios, por isso vive em tabela própria (mesmo
# desenho da InutilizacaoFiscal) e não em colunas do DocumentoFiscal.
#
# Só modelo 55: a legislação não prevê CC-e para NFC-e.
# ---------------------------------------------------------------------------

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.documento_fiscal import DocumentoFiscal


class CartaCorrecaoFiscal(Base):
    __tablename__ = "carta_correcao_fiscal"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    empresa_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    documento_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("documento_fiscal.id"), nullable=False, index=True,
        doc="NF-e que recebeu a carta",
    )
    sequencia: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        doc="numero_carta_correcao devolvido pela SEFAZ (1..20). Nulo enquanto não autorizada.",
    )
    correcao: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[str] = mapped_column(
        String(15), nullable=False, default="PROCESSANDO", index=True,
        doc="PROCESSANDO | AUTORIZADA | REJEITADA | ERRO",
    )
    protocolo: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    codigo_status_sefaz: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mensagem_sefaz: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    url_xml: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    url_pdf: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    caminho_xml_local: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    caminho_pdf_local: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ambiente_emissao: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    usuario_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, doc="Quem pediu a carta",
    )
    # UTC, como o resto do banco (app/core/tempo.py converte na tela).
    data_evento: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    data_criacao: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False,
    )

    documento: Mapped["DocumentoFiscal"] = relationship(back_populates="cartas_correcao")
