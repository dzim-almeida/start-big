# ---------------------------------------------------------------------------
# ARQUIVO: app/db/models/produto_codigo_fornecedor.py
# DESCRIÇÃO: O "De-Para" da entrada por XML: código do fornecedor → produto.
# ---------------------------------------------------------------------------
"""
Cada fornecedor chama o produto por um código próprio (`cProd` da nota). Na
primeira nota o lojista diz "o CERV-CX12 dele é a minha Cerveja Lata, caixa
de 12"; daí em diante o item vem reconhecido sozinho (X4). Guarda também a
embalagem e o fator, porque o mesmo produto chega em caixa de um fornecedor e
em fardo de outro.
"""

from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProdutoCodigoFornecedor(Base):
    __tablename__ = "produto_codigos_fornecedor"
    __table_args__ = (
        UniqueConstraint("fornecedor_id", "codigo_fornecedor", name="uq_produto_codigo_fornecedor"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    fornecedor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fornecedores.id", ondelete="CASCADE"), nullable=False, index=True
    )
    codigo_fornecedor: Mapped[str] = mapped_column(String(60), nullable=False, doc="cProd da nota")
    produto_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("produtos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    embalagem_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("produto_embalagens.id", ondelete="SET NULL"), nullable=True
    )
    fator: Mapped[int] = mapped_column(Integer, nullable=False, default=1, doc="Unidades do produto por item da nota")
