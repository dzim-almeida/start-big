# ---------------------------------------------------------------------------
# ARQUIVO: app/db/models/produto_embalagem.py
# DESCRIÇÃO: Embalagem de venda/compra de um produto (fardo, caixa, pack).
# ---------------------------------------------------------------------------
"""
Por que a embalagem é filha do produto, e não um produto novo.

Cadastrar "Cerveja lata — fardo 12" como outro produto é o que as lojas fazem
por falta de opção — e é o que separa o estoque: vender o fardo não baixa as
latas. Aqui o ESTOQUE fica sempre na unidade do produto; a embalagem é só uma
forma de vender e de receber, com código de barras, preço e quantidade
(fator) próprios. Ver docs/produto-embalagens-plano.md (D1, D2).

Fator 1 é um código de barras ADICIONAL da unidade (o mesmo refrigerante com
EAN de outra fábrica) — plano, A1.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.produto import Produto


class ProdutoEmbalagem(Base):
    __tablename__ = "produto_embalagens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    produto_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("produtos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Produto dono da embalagem",
    )
    sigla: Mapped[str] = mapped_column(
        String(6), nullable=False, doc="FD, CX, PCT… — vai no uCom da nota (fase 4)"
    )
    descricao: Mapped[Optional[str]] = mapped_column(
        String(60), nullable=True, doc="Como aparece no caixa e na etiqueta ('Fardo com 12')"
    )
    fator: Mapped[int] = mapped_column(
        Integer, nullable=False, doc="Quantas unidades do produto a embalagem tem (1 = código adicional)"
    )
    codigo_barras: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, index=True, doc="EAN/DUN da embalagem — único no sistema inteiro"
    )
    preco: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, doc="Preço próprio (centavos). Nulo = calculado (ver desconto_bp)"
    )
    desconto_bp: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Alternativa ao preço próprio: desconto sobre fator × unidade, em centésimos de % (500 = 5%)",
    )
    vende_no_pdv: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, doc="Aparece e é bipável no caixa"
    )
    usa_na_entrada: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, doc="Oferecida na entrada de estoque"
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    data_criacao: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    data_atualizacao: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    produto: Mapped["Produto"] = relationship(back_populates="embalagens")

    def __repr__(self) -> str:
        return f"<ProdutoEmbalagem(id={self.id}, produto_id={self.produto_id}, {self.sigla} x{self.fator})>"
