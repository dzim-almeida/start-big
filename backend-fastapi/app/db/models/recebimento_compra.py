# ---------------------------------------------------------------------------
# ARQUIVO: app/db/models/recebimento_compra.py
# DESCRIÇÃO: Recebimento de um pedido de compra (módulo Compras, fase 3).
# ---------------------------------------------------------------------------
"""
Cada chegada de mercadoria de um pedido é um recebimento — um pedido de 10
fardos que chega em 6 + 4 tem dois. É aqui que o pedido vira ESTOQUE (uma
ENTRADA no livro, origem COMPRA, com o custo real) e CONTA A PAGAR
(proporcional ao que chegou, D8). Ver docs/compras-plano.md.

Os valores ficam gravados como foram NO RECEBIMENTO: o custo real de cada item
e a parte do frete/desconto que coube a esta chegada. O último recebimento
fecha o ajuste do pedido ao centavo (ver services/compras/recebimentos.py).
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RecebimentoCompra(Base):
    __tablename__ = "recebimentos_compra"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    empresa_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("empresas.id", ondelete="SET NULL"), nullable=True, index=True
    )
    pedido_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pedidos_compra.id", ondelete="CASCADE"), nullable=False, index=True
    )
    numero_nota: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, doc="Número da nota em papel, quando o recebimento é manual"
    )
    observacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    valor_itens: Mapped[int] = mapped_column(Integer, nullable=False, default=0, doc="Σ qtd × custo real, centavos")
    valor_ajuste: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, doc="Parte do frete − desconto do pedido que coube a esta chegada"
    )
    valor_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    contas_pagar_lancadas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    recebido_por_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    recebido_por_nome: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    recebido_em: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())

    itens = relationship(
        "RecebimentoCompraItem", back_populates="recebimento", cascade="all, delete-orphan",
        order_by="RecebimentoCompraItem.id",
    )


class RecebimentoCompraItem(Base):
    __tablename__ = "recebimento_compra_itens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    recebimento_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("recebimentos_compra.id", ondelete="CASCADE"), nullable=False, index=True
    )
    pedido_item_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("pedido_compra_itens.id", ondelete="SET NULL"), nullable=True, index=True
    )
    produto_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("produtos.id", ondelete="SET NULL"), nullable=True
    )
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    unidade_compra: Mapped[str] = mapped_column(String(10), nullable=False, default="UN")
    fator: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False, doc="Na unidade de compra")
    unidades: Mapped[float] = mapped_column(Float, nullable=False, doc="O que entrou no estoque (qtd × fator)")
    custo_unitario: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, doc="Custo REAL por unidade de compra, centavos"
    )
    movimentacao_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("movimentacoes_estoque.id", ondelete="SET NULL"), nullable=True
    )

    recebimento = relationship("RecebimentoCompra", back_populates="itens")
