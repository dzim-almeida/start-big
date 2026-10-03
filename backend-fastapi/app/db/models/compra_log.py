# ---------------------------------------------------------------------------
# ARQUIVO: app/db/models/compra_log.py
# DESCRIÇÃO: Histórico do módulo de Compras — só INSERT (RC18 do resumo).
# ---------------------------------------------------------------------------
"""
Toda mudança de situação de um pedido (e, na fase 3, cada recebimento) vira
uma linha aqui, com quem, quando e por quê. Nunca se edita nem se apaga: é a
resposta para "quem cancelou o pedido da Ambev?".

Sem FK para o objeto (`objeto` + `objeto_id`): o histórico sobrevive ao que
ele descreve, e serve a pedidos e recebimentos com a mesma tabela.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CompraLog(Base):
    __tablename__ = "compras_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    objeto: Mapped[str] = mapped_column(String(20), nullable=False, doc="PEDIDO (fase 3: RECEBIMENTO)")
    objeto_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    acao: Mapped[str] = mapped_column(String(40), nullable=False, doc="CRIADO, EDITADO, ENVIADO, CANCELADO…")
    situacao_anterior: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    situacao_nova: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    motivo: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    usuario_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    usuario_nome: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ocorrido_em: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
