# ---------------------------------------------------------------------------
# ARQUIVO: db/models/log_produto.py
# DESCRICAO: Modelo SQLAlchemy para a tabela 'logs_produto'.
#            Historico de auditoria imutavel para movimentacoes de estoque.
# ---------------------------------------------------------------------------

from datetime import datetime
from sqlalchemy import Integer, DateTime, Enum as SqlAlchemyEnum, ForeignKey, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

from app.db.base import Base
from app.core.enum import TipoTransacaoEstoque

if TYPE_CHECKING:
    from .produto import Produto
    from .venda import Venda
    from .funcionario import Funcionario


class LogProduto(Base):
    """Modelo ORM que representa um log de movimentacao de estoque na tabela 'logs_produto'."""

    __tablename__ = "logs_produto"
    __table_args__ = (
        CheckConstraint("quantidade != 0", name="ck_log_produto_quantidade_nao_zero"),\
        CheckConstraint("(tipo_transacao == 'ENTRADA') OR (venda_id IS NOT NULL)", name="ck_log_produto_tipo_transacao_valida")
    )

    # --- Identificacao ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, doc="ID do log (PK)")

    # --- Vinculos ---
    produto_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("produtos.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Produto movimentado (FK)"
    )
    venda_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("vendas.id", ondelete="SET NULL"),
        nullable=True,
        doc="Venda que causou saida ou estorno (FK)"
    )
    funcionario_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("funcionarios.id"),
        nullable=False,
        doc="Responsavel pela acao (FK)"
    )

    # --- Dados da Movimentacao ---
    tipo_transacao: Mapped[TipoTransacaoEstoque] = mapped_column(
        SqlAlchemyEnum(TipoTransacaoEstoque),
        nullable=False,
        doc="Tipo da transacao de estoque"
    )
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False, doc="Quantidade movimentada (+ ou -)")
    data_registro: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, doc="Data exata da movimentacao no sistema")

    # --- Relacionamentos ---
    produto: Mapped["Produto"] = relationship(back_populates="logs")
    venda: Mapped[Optional["Venda"]] = relationship(back_populates="logs_produto")
    funcionario: Mapped["Funcionario"] = relationship(doc="Funcionario responsavel pela movimentacao")
