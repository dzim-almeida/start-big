# ---------------------------------------------------------------------------
# ARQUIVO: app/db/models/produto_fornecedor.py
# DESCRIÇÃO: De quem a loja compra cada produto (módulo Compras, fase 1).
# ---------------------------------------------------------------------------
"""
Um produto pode ser comprado de vários fornecedores, cada um com o seu
código, a sua embalagem (a Ambev manda fardo de 12; o atacado, caixa de 24),
o seu prazo e o último preço pago. É a base das Necessidades de compra e do
aviso de fornecedor mais barato (docs/compras-plano.md, D13 e D18).

O FORNECEDOR PADRÃO NÃO MORA AQUI: é o `produtos.fornecedor_id` que o
cadastro do produto já tinha ("fornecedor principal"). Guardar um `padrao`
nesta tabela criaria uma segunda verdade, e as duas divergiriam no primeiro
cadastro feito pela tela antiga.

POR QUE NÃO REUSAR `produto_codigos_fornecedor` (o De-Para da XML): ele é
indexado pelo código do fornecedor (`cProd`), que é obrigatório lá e que o
cadastro manual muitas vezes não tem. Mexer nele arriscaria a entrada por XML,
que já está em produção. A XML continua usando o De-Para e, além disso,
alimenta o último preço daqui (services/compras/fornecedores_produto.py).

Preço em centavos por UNIDADE DE COMPRA (o fardo, se compra em fardo). O
preço por unidade do produto é `ultimo_preco ÷ fator`, calculado na hora.
"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ProdutoFornecedor(Base):
    __tablename__ = "produto_fornecedores"
    __table_args__ = (
        # Um fornecedor aparece uma vez por produto. Se ele vende em fardo E em
        # caixa, vale a embalagem em que a loja compra dele.
        UniqueConstraint("produto_id", "fornecedor_id", name="uq_produto_fornecedor"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    produto_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("produtos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fornecedor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fornecedores.id", ondelete="CASCADE"), nullable=False, index=True
    )
    codigo_fornecedor: Mapped[Optional[str]] = mapped_column(
        String(60), nullable=True, doc="Como o fornecedor chama o produto (cProd da nota)"
    )
    embalagem_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("produto_embalagens.id", ondelete="SET NULL"), nullable=True,
        doc="Unidade de compra; nula = compra na unidade do produto",
    )
    fator: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, doc="Unidades do produto por unidade de compra"
    )
    ultimo_preco: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, doc="Último preço pago, em centavos por UNIDADE DE COMPRA"
    )
    ultima_compra_em: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    prazo_dias: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, doc="Prazo de entrega combinado, em dias"
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    fornecedor = relationship("Fornecedor", lazy="joined")
    embalagem = relationship("ProdutoEmbalagem", lazy="joined")
