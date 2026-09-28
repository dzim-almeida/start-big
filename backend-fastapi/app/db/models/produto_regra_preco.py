# ---------------------------------------------------------------------------
# ARQUIVO: app/db/models/produto_regra_preco.py
# DESCRIÇÃO: Regras de preço por quantidade de um produto (R2 e R3).
# ---------------------------------------------------------------------------
"""
Plano de embalagens, §6.1 (fase 5). Uma tabela só para as duas regras que
moram no produto:

- FAIXA (R2): "a partir de `quantidade` un, cada uma sai por `preco`".
- LEVE_PAGUE (R3): "leve `quantidade`, pague `pague`", com vigência.

A R1 (preço de fardo nas avulsas) não mora aqui: é a própria embalagem, com
`aplica_as_avulsas` ligado.

Nada disso vale sozinho: cada regra só morde com a chave dela ligada em
Configurações › Regras de Vendas (D16). Sem chave, o cadastro fica guardado e
a venda sai exatamente como antes (B8).
"""

from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.produto import Produto


class ProdutoRegraPreco(Base):
    __tablename__ = "produto_regras_preco"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    produto_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("produtos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Produto dono da regra",
    )
    tipo: Mapped[str] = mapped_column(String(12), nullable=False, doc="FAIXA (R2) ou LEVE_PAGUE (R3)")
    quantidade: Mapped[int] = mapped_column(
        Integer, nullable=False, doc="FAIXA: a partir de N un. LEVE_PAGUE: leve X."
    )
    preco: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, doc="FAIXA: preço de cada unidade na faixa (centavos)"
    )
    pague: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, doc="LEVE_PAGUE: pague Y")
    inicio: Mapped[Optional[date]] = mapped_column(Date, nullable=True, doc="Vale a partir de (inclusive)")
    fim: Mapped[Optional[date]] = mapped_column(Date, nullable=True, doc="Vale até (inclusive)")
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    data_criacao: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    data_atualizacao: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    produto: Mapped["Produto"] = relationship(back_populates="regras_preco")

    def vigente_em(self, dia: date) -> bool:
        if not self.ativo:
            return False
        if self.inicio and dia < self.inicio:
            return False
        if self.fim and dia > self.fim:
            return False
        return True

    def __repr__(self) -> str:
        return f"<ProdutoRegraPreco(id={self.id}, produto_id={self.produto_id}, {self.tipo} {self.quantidade})>"
