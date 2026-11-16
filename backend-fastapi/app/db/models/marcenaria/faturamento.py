# ---------------------------------------------------------------------------
# ARQUIVO: app/db/models/marcenaria/faturamento.py
# DESCRICAO: O caminho de cada movel aprovado ate a nota fiscal
#            (docs/marcenaria-faturamento-plano.md, §3).
# ---------------------------------------------------------------------------
"""
Uma linha por movel: o movel ficou pronto e entrou no estoque como PRODUTO
ACABADO (F2), e depois saiu numa NF-e (F3/F4).

    NO_ESTOQUE -> FATURADO        (nota autorizada)
    FATURADO   -> NO_ESTOQUE      (nota cancelada: o movel volta ao estoque)
    NO_ESTOQUE -> ESTORNADO       (o movel deixou de estar pronto)

`movel_id` e UNIQUE: e o que garante a decisao D1 -- cada movel e faturado
uma vez so, mesmo que a OS tenha varias notas (uma por entrega).
"""

from datetime import datetime, UTC
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SituacaoFaturamento:
    """Texto gravado em `marcenaria_moveis_faturamento.situacao`."""
    NO_ESTOQUE = "NO_ESTOQUE"
    FATURADO = "FATURADO"
    ESTORNADO = "ESTORNADO"


class MarcenariaMovelFaturamento(Base):
    """Um movel aprovado no caminho produto acabado -> NF-e."""
    __tablename__ = "marcenaria_moveis_faturamento"
    __table_args__ = (
        Index("ix_marcenaria_moveis_faturamento_os", "os_id"),
        Index("ix_marcenaria_moveis_faturamento_doc", "documento_fiscal_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    os_id: Mapped[int] = mapped_column(ForeignKey("ordens_servico.id"), nullable=False)
    movel_id: Mapped[int] = mapped_column(
        ForeignKey("marcenaria_moveis.id", ondelete="CASCADE"), nullable=False, unique=True,
    )
    # O produto acabado em que o movel entrou (o do movel, ou o padrao da configuracao).
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False)
    quantidade: Mapped[float] = mapped_column(Float, nullable=False)
    # Custo de material por unidade (D9), congelado na entrada.
    custo_unitario_centavos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mov_entrada_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("movimentacoes_estoque.id", ondelete="SET NULL"), nullable=True,
    )
    mov_saida_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("movimentacoes_estoque.id", ondelete="SET NULL"), nullable=True,
    )
    # A nota de venda (F3) ou de remessa (F4) em que o movel saiu.
    documento_fiscal_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("documento_fiscal.id", ondelete="SET NULL"), nullable=True,
    )
    # Entrega futura (F4): a nota de simples faturamento que cobre o movel.
    documento_simples_faturamento_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("documento_fiscal.id", ondelete="SET NULL"), nullable=True,
    )
    situacao: Mapped[str] = mapped_column(String(12), nullable=False, default=SituacaoFaturamento.NO_ESTOQUE)

    criado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC),
    )
