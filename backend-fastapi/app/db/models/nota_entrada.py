# ---------------------------------------------------------------------------
# ARQUIVO: app/db/models/nota_entrada.py
# DESCRIÇÃO: NF-e de compra importada pela XML (docs/entrada-xml-nfe-plano.md).
# ---------------------------------------------------------------------------
"""
Uma linha por nota importada. Existe para duas coisas:

- **Não importar a mesma nota duas vezes** (X6): a `chave` é única. Sem isto,
  abrir o mesmo XML de novo dobraria o estoque em silêncio.
- **Rastrear:** cada movimento de estoque da nota aponta para cá
  (`movimentacoes_estoque.nota_entrada_id`).
"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class NotaEntrada(Base):
    __tablename__ = "notas_entrada"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    empresa_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("empresas.id", ondelete="SET NULL"), nullable=True, index=True
    )
    chave: Mapped[str] = mapped_column(String(44), unique=True, nullable=False, doc="Chave de acesso (44 dígitos)")
    numero: Mapped[str] = mapped_column(String(9), nullable=False)
    serie: Mapped[str] = mapped_column(String(3), nullable=False)
    emissao: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    valor_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0, doc="vNF, em centavos")
    fornecedor_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("fornecedores.id", ondelete="SET NULL"), nullable=True, index=True
    )
    fornecedor_nome: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, doc="Como veio na nota")
    itens_lancados: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    contas_pagar_lancadas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    usuario_nome: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    importada_em: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
