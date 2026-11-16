# ---------------------------------------------------------------------------
# ARQUIVO: app/db/models/lava_rapido/agendamento.py
# DESCRICAO: Agendamentos (docs/lava-rapido/ SPEC-00 O11 e Spec 08A).
# ---------------------------------------------------------------------------
"""
O agendamento vem ANTES da OS: o cliente liga, marca sexta as 9h, e so quando
ele chega a lavagem vira OS (pela comanda, ja preenchida). Por isso a agenda
da marcenaria nao serve -- ela agenda uma OS que ja existe.

Guarda o minimo para o balcao reconhecer o cliente e preparar o box: quem
(cliente cadastrado ou so nome e telefone), qual veiculo, quais servicos e a
hora. Quando ele chega, `numero_os` aponta a OS que nasceu daqui.
"""

from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.tempo import agora_utc
from app.db.base import Base

# Situacoes (O11). Texto, e nao enum do banco: acrescentar uma nao exige migracao.
AGENDADO = "AGENDADO"
CHEGOU = "CHEGOU"
NAO_VEIO = "NAO_VEIO"
CANCELADO = "CANCELADO"
SITUACOES = (AGENDADO, CHEGOU, NAO_VEIO, CANCELADO)


class Agendamento(Base):
    __tablename__ = "agendamentos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # Instante marcado, em UTC (como toda data da casa).
    inicio: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    duracao_minutos: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Cliente cadastrado OU so nome e telefone (quem liga pela primeira vez).
    cliente_id: Mapped[Optional[int]] = mapped_column(ForeignKey("clientes.id"), nullable=True)
    cliente_nome: Mapped[str] = mapped_column(String(255), nullable=False)
    cliente_contato: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    placa: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    veiculo: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)      # "Gol prata"
    tipo_veiculo: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    porte_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("portes_veiculo.id", ondelete="SET NULL"), nullable=True,
    )
    # [{"servico_id": 1, "nome": "Lavagem completa", "valor": 6000}] -- copia no
    # momento: o preco combinado ao telefone nao muda se a tabela mudar.
    servicos: Mapped[List[Any]] = mapped_column(JSON, nullable=False, default=list)
    observacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    situacao: Mapped[str] = mapped_column(String(15), nullable=False, default=AGENDADO, index=True)
    numero_os: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=agora_utc)
