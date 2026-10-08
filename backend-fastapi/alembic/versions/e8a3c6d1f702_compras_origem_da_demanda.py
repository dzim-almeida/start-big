"""compras (fase 6): de onde veio a demanda de cada item do pedido (OS)

Revision ID: e8a3c6d1f702
Revises: d5f1b2c8e604
Create Date: 2026-10-04 15:00:00.000000

CONTEXTO (docs/compras-plano.md, fase 6; RC06 do resumo da marcenaria):
- `pedido_compra_origens`: a fatia da quantidade de um item do pedido que veio
  de uma OS aberta ("esta chapa é da OS 123"). Em unidades do produto.

MIGRAÇÃO DE DADOS: NENHUMA. Tabela nova, vazia.

SEGURANÇA: decide pela ausência da TABELA. Não toca nada existente.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e8a3c6d1f702'
down_revision: Union[str, Sequence[str], None] = 'd5f1b2c8e604'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if not insp.has_table("pedido_compra_origens"):
        op.create_table(
            "pedido_compra_origens",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("pedido_item_id", sa.Integer(), nullable=False),
            sa.Column("origem", sa.String(length=20), nullable=False),
            sa.Column("origem_id", sa.Integer(), nullable=True),
            sa.Column("quantidade", sa.Float(), nullable=False),
            sa.ForeignKeyConstraint(["pedido_item_id"], ["pedido_compra_itens.id"], ondelete="CASCADE"),
        )
        op.create_index("ix_pedido_compra_origens_id", "pedido_compra_origens", ["id"])
        op.create_index("ix_pedido_compra_origens_pedido_item_id", "pedido_compra_origens", ["pedido_item_id"])
        op.create_index("ix_pedido_compra_origens_origem_id", "pedido_compra_origens", ["origem_id"])


def downgrade() -> None:
    op.drop_table("pedido_compra_origens")
