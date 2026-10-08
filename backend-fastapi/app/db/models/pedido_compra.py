# ---------------------------------------------------------------------------
# ARQUIVO: app/db/models/pedido_compra.py
# DESCRIÇÃO: Pedido de compra ao fornecedor (módulo Compras, fase 2).
# ---------------------------------------------------------------------------
"""
O pedido é o COMPROMISSO com o fornecedor: o que foi pedido, a que preço,
para quando, em que condição de pagamento. Ele não mexe no estoque nem no
financeiro — isso acontece no recebimento (fase 3). Ver docs/compras-plano.md.

SITUAÇÕES (D5), em texto e não em Enum do banco: acrescentar uma situação
depois não pode exigir recriar tabela no SQLite do cliente.

    RASCUNHO → ENVIADO → PARCIAL → RECEBIDO          (PARCIAL/RECEBIDO: fase 3)
        ↘          ↘
         CANCELADO   CANCELADO

NOMES DESNORMALIZADOS (fornecedor, produto, embalagem): o pedido é um
documento enviado. Renomear o produto depois não pode reescrever o que o
fornecedor recebeu — mesmo princípio do `produto_nome` do livro de estoque.

QUANTIDADES INTEIRAS na unidade de compra (D3): 5 fardos, não 60 latas. O
estoque recebe `quantidade × fator` no recebimento.
"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SituacaoPedido:
    RASCUNHO = "RASCUNHO"
    ENVIADO = "ENVIADO"
    PARCIAL = "PARCIAL"
    RECEBIDO = "RECEBIDO"
    CANCELADO = "CANCELADO"

    TODAS = (RASCUNHO, ENVIADO, PARCIAL, RECEBIDO, CANCELADO)
    # O que está "a caminho": conta como em_pedido nas Necessidades. Rascunho
    # NÃO conta — um rascunho esquecido sumiria com a necessidade.
    EM_ABERTO = (ENVIADO, PARCIAL)


class TipoPedido:
    MATERIAL = "MATERIAL"
    # Central de corte, montador (marcenaria, fase 6). Nasce no modelo já, para
    # não exigir migration depois (D15); a tela só abre na fase 6.
    SERVICO = "SERVICO"


class PedidoCompra(Base):
    __tablename__ = "pedidos_compra"
    __table_args__ = (UniqueConstraint("numero", name="uq_pedido_compra_numero"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    empresa_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("empresas.id", ondelete="SET NULL"), nullable=True, index=True
    )
    numero: Mapped[int] = mapped_column(Integer, nullable=False, doc="Sequencial; exibido como PC-000123")
    tipo: Mapped[str] = mapped_column(String(20), nullable=False, default=TipoPedido.MATERIAL)
    situacao: Mapped[str] = mapped_column(String(20), nullable=False, default=SituacaoPedido.RASCUNHO, index=True)

    fornecedor_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("fornecedores.id", ondelete="SET NULL"), nullable=True, index=True
    )
    fornecedor_nome: Mapped[str] = mapped_column(String(255), nullable=False, doc="Nome no momento do pedido")

    previsao_entrega: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    condicao_pagamento: Mapped[Optional[str]] = mapped_column(
        String(60), nullable=True, doc='Como combinado: "30/60/90", "à vista"'
    )
    frete: Mapped[int] = mapped_column(Integer, nullable=False, default=0, doc="Centavos")
    desconto: Mapped[int] = mapped_column(Integer, nullable=False, default=0, doc="Centavos")
    valor_itens: Mapped[int] = mapped_column(Integer, nullable=False, default=0, doc="Σ quantidade × custo, centavos")
    valor_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0, doc="itens + frete − desconto")
    observacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    enviado_em: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    cancelado_em: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    motivo_cancelamento: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    criado_por_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    criado_por_nome: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    itens = relationship(
        "PedidoCompraItem", back_populates="pedido", cascade="all, delete-orphan",
        order_by="PedidoCompraItem.id",
    )
    parcelas = relationship(
        "PedidoCompraParcela", back_populates="pedido", cascade="all, delete-orphan",
        order_by="PedidoCompraParcela.numero",
    )
    fornecedor = relationship("Fornecedor", lazy="joined")

    @property
    def codigo(self) -> str:
        return f"PC-{self.numero:06d}"


class PedidoCompraItem(Base):
    __tablename__ = "pedido_compra_itens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pedido_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pedidos_compra.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Nulo = item de serviço (fase 6) ou produto apagado depois — o nome fica.
    produto_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("produtos.id", ondelete="SET NULL"), nullable=True, index=True
    )
    descricao: Mapped[str] = mapped_column(String(255), nullable=False, doc="Nome do produto no momento do pedido")
    codigo_fornecedor: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    embalagem_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("produto_embalagens.id", ondelete="SET NULL"), nullable=True
    )
    unidade_compra: Mapped[str] = mapped_column(String(10), nullable=False, default="UN", doc="FD, CX, UN…")
    fator: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False, doc="Na unidade de compra")
    quantidade_recebida: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quantidade_cancelada: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    custo_unitario: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, doc="Centavos por unidade de compra"
    )

    pedido = relationship("PedidoCompra", back_populates="itens")

    @property
    def pendente(self) -> int:
        """Unidades de compra que ainda não chegaram nem foram canceladas."""
        return max(self.quantidade - self.quantidade_recebida - self.quantidade_cancelada, 0)


class PedidoCompraParcela(Base):
    """A condição combinada com o fornecedor (D8a). NÃO é conta a pagar.

    A conta a pagar nasce no recebimento (fase 3), das duplicatas da nota ou
    destas parcelas proporcionais ao que chegou.
    """

    __tablename__ = "pedido_compra_parcelas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pedido_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pedidos_compra.id", ondelete="CASCADE"), nullable=False, index=True
    )
    numero: Mapped[int] = mapped_column(Integer, nullable=False)
    dias: Mapped[int] = mapped_column(Integer, nullable=False, doc="Dias após o recebimento")
    valor: Mapped[int] = mapped_column(Integer, nullable=False, doc="Centavos")

    pedido = relationship("PedidoCompra", back_populates="parcelas")
