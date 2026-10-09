# ---------------------------------------------------------------------------
# ARQUIVO: app/db/models/configuracao_marcenaria.py
# DESCRICAO: Parametros padrao do orcamento de marcenaria, por empresa (1:1).
#            Spec 04A da marcenaria (docs/marcenaria/), decisoes D5-D7.
# ---------------------------------------------------------------------------

from datetime import datetime, UTC
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.empresa import Empresa


# Etapas de producao padrao (SPEC-00, P1): cada OS recebe uma COPIA desta lista,
# entao mudar a configuracao nao altera OS ja abertas.
ETAPAS_PADRAO = ["Corte", "Borda", "Furação", "Montagem", "Embalagem"]

# Checklist da vistoria de entrega (SPEC-00, I2), tirado do Termo de Entrega do
# Figma, em linguagem que serve a qualquer ambiente.
CHECKLIST_PADRAO = [
    "Alinhamento de portas e gavetas",
    "Acabamento de bordas e vedação com silicone",
    "Funcionamento de corrediças, dobradiças e pistões",
    "Fixação e nivelamento dos móveis",
    "Limpeza final do ambiente",
]


class ConfiguracaoMarcenaria(Base):
    """Parametros padrao do orcamento de marcenaria, por empresa (1:1).

    Todo orcamento novo COPIA estes valores; mudar aqui nao altera orcamento
    nem OS ja existentes. Percentuais em basis points (9000 = 90%), dinheiro em
    centavos (SPEC-00, PR4): nada de float.
    """
    __tablename__ = "configuracoes_marcenaria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # Uma configuracao por empresa (unique); apagar a empresa apaga junto.
    empresa_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("empresas.id", ondelete="CASCADE"), unique=True, nullable=False,
    )

    # --- Preco (so quem tem view_custos_marcenaria ve; D9) -----------------
    markup_padrao_bp: Mapped[int] = mapped_column(Integer, default=9000, nullable=False)      # 90%
    perda_padrao_bp: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)       # 10%
    custo_hora_centavos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)      # R$ 0,00
    rt_padrao_bp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)             # 0%
    rt_modo: Mapped[str] = mapped_column(String(10), default="MARGEM", nullable=False)        # 'MARGEM' | 'PRECO'

    # --- Prazos e listas (qualquer usuario logado ve; D9) ------------------
    validade_dias: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    prazo_entrega_dias: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    # `default=lambda: list(...)`: cada linha ganha a SUA copia da lista; sem o
    # lambda, todas compartilhariam a mesma lista em memoria.
    etapas_producao: Mapped[list[str]] = mapped_column(
        JSON, default=lambda: list(ETAPAS_PADRAO), nullable=False,
    )
    checklist_vistoria: Mapped[list[str]] = mapped_column(
        JSON, default=lambda: list(CHECKLIST_PADRAO), nullable=False,
    )

    data_atualizacao: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    empresa: Mapped["Empresa"] = relationship("Empresa", back_populates="config_marcenaria")

    def __repr__(self) -> str:
        return f"<ConfiguracaoMarcenaria(id={self.id}, empresa_id={self.empresa_id})>"
