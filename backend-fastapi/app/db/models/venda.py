# ---------------------------------------------------------------------------
# ARQUIVO: db/models/venda.py
# DESCRICAO: Modelo SQLAlchemy para a tabela 'vendas'.
#            Entidade central do fluxo transacional do PDV.
# ---------------------------------------------------------------------------

from datetime import datetime
from sqlalchemy import Integer, DateTime, Enum as SqlAlchemyEnum, ForeignKey, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, TYPE_CHECKING

from app.db.base import Base
from app.core.enum import VendaStatus

if TYPE_CHECKING:
    from .cliente import Cliente
    from .funcionario import Funcionario
    from .sessao_caixa import SessaoCaixa
    from .venda_produto import ProdutoVenda
    from .venda_pagamento import PagamentoVenda
    from .log_produto import LogProduto


class Venda(Base):
    """Modelo ORM que representa uma venda na tabela 'vendas'."""

    __tablename__ = "vendas"
    __table_args__ = (
        CheckConstraint("subtotal >= 0", name="ck_venda_subtotal_nao_negativo"),
        CheckConstraint("desconto >= 0", name="ck_venda_desconto_nao_negativo"),
        CheckConstraint("entrega >= 0", name="ck_venda_entrega_nao_negativo"),
        CheckConstraint("adiantamento >= 0", name="ck_venda_adiantamento_nao_negativo"),
        CheckConstraint("total >= 0", name="ck_venda_total_nao_negativo"),
    )

    # --- Identificacao ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, doc="ID unico da venda (PK)")

    # --- Vinculos ---
    cliente_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("clientes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Cliente atrelado. Nulo para vendas rapidas de balcao (FK)"
    )
    funcionario_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("funcionarios.id"),
        nullable=False,
        index=True,
        doc="Vendedor responsavel pelo caixa (FK)"
    )
    sessao_caixa_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("sessao_caixa.id", ondelete="SET NULL"),
        nullable=True,
        doc="Vinculo com o turno/caixa atual (FK)"
    )

    # --- Status ---
    status: Mapped[VendaStatus] = mapped_column(
        SqlAlchemyEnum(VendaStatus),
        default=VendaStatus.RASCUNHO,
        nullable=False,
        doc="Status atual da venda"
    )

    # --- Financeiro (valores em centavos) ---
    subtotal: Mapped[int] = mapped_column(Integer, default=0, nullable=False, doc="Soma dos itens sem descontos e fretes (centavos)")
    desconto: Mapped[int] = mapped_column(Integer, default=0, nullable=False, doc="Desconto global aplicado no fechamento (centavos)")
    entrega: Mapped[int] = mapped_column(Integer, default=0, nullable=False, doc="Valor do frete/motoboy (centavos)")
    adiantamento: Mapped[int] = mapped_column(Integer, default=0, nullable=False, doc="Valor pago previamente/sinal (centavos)")
    total: Mapped[int] = mapped_column(Integer, default=0, nullable=False, doc="(subtotal + entrega) - (desconto + adiantamento) (centavos)")

    # --- Datas ---
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, doc="Data de criacao do rascunho")
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, doc="Ultima alteracao no carrinho")

    # --- Relacionamentos ---
    cliente: Mapped[Optional["Cliente"]] = relationship(
        "Cliente",
        back_populates="vendas",
        doc="Cliente associado a esta venda"
    )
    funcionario: Mapped["Funcionario"] = relationship(
        "Funcionario",
        back_populates="vendas",
        doc="Funcionario responsavel pela venda"
    )
    sessao_caixa: Mapped[Optional["SessaoCaixa"]] = relationship(
        "SessaoCaixa",
        back_populates="vendas",
        doc="Sessao de caixa em que a venda foi realizada"
    )
    itens: Mapped[List["ProdutoVenda"]] = relationship(
        "ProdutoVenda",
        back_populates="venda",
        cascade="all, delete-orphan",
        doc="Itens do carrinho desta venda"
    )
    pagamentos: Mapped[List["PagamentoVenda"]] = relationship(
        "PagamentoVenda",
        back_populates="venda",
        cascade="all, delete-orphan",
        doc="Pagamentos desta venda"
    )
    logs_produto: Mapped[List["LogProduto"]] = relationship(
        "LogProduto",
        back_populates="venda",
        doc="Logs de movimentacao de estoque desta venda"
    )
