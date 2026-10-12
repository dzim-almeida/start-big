# ---------------------------------------------------------------------------
# ARQUIVO: app/db/models/marcenaria/evento.py
# DESCRICAO: Historico da marcenaria (Spec 06A, D25; SPEC-00, T7).
# ---------------------------------------------------------------------------
"""
Uma linha por TRANSICAO ou ACAO (criar, enviar, voltar a editar, recusar,
renovar, nova versao, precos atualizados, anexo incluido/removido, excluir).
NAO registra cada edicao de campo: o salvamento automatico da tela geraria
centenas de eventos inuteis por orcamento.

So inclusao: nada aqui e editado nem apagado pelo sistema. As proximas specs
(OS, producao, entrega) usam a mesma tabela, pela coluna `os_id`.

`usuario_nome` e uma COPIA do nome no momento: o historico continua legivel
mesmo que o funcionario mude de nome ou seja desligado.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.tempo import agora_utc
from app.db.base import Base


class MarcenariaEvento(Base):
    __tablename__ = "marcenaria_eventos"
    __table_args__ = (
        Index("ix_marcenaria_eventos_orcamento", "orcamento_id", "ocorrido_em"),
        Index("ix_marcenaria_eventos_os", "os_id", "ocorrido_em"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # SET NULL: excluir um rascunho nunca enviado (D18) nao apaga o evento que
    # registra a exclusao; ele fica sem orcamento, com o codigo em `dados`.
    orcamento_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("marcenaria_orcamentos.id", ondelete="SET NULL"), nullable=True,
    )
    os_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ordens_servico.id"), nullable=True)   # Spec 08A em diante
    tipo: Mapped[str] = mapped_column(String(40), nullable=False)          # ORCAMENTO_CRIADO, ORCAMENTO_ENVIADO...
    descricao: Mapped[str] = mapped_column(String(500), nullable=False)    # frase pronta para a tela
    dados: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)   # ex.: {"motivo": "..."}
    usuario_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    usuario_nome: Mapped[str] = mapped_column(String(150), nullable=False)
    ocorrido_em: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=agora_utc)
