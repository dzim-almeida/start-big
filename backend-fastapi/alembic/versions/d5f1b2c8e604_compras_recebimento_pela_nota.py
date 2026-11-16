"""compras (fase 4): recebimento ligado à NF-e importada por XML

Revision ID: d5f1b2c8e604
Revises: c3e8a1f5d927
Create Date: 2026-10-04 09:00:00.000000

CONTEXTO (docs/compras-plano.md, fase 4):
- `recebimentos_compra.nota_entrada_id`: quando a mercadoria chega com a XML
  da NF-e e o lojista liga a nota ao pedido, o recebimento aponta a nota.

MIGRAÇÃO DE DADOS: NENHUMA. Coluna nova, nula.

SEGURANÇA: decide pela ausência da COLUNA. Não altera nem apaga nada.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd5f1b2c8e604'
down_revision: Union[str, Sequence[str], None] = 'c3e8a1f5d927'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if not insp.has_table("recebimentos_compra"):
        # Só acontece num banco que pulou a c3e8a1f5d927 — nada a fazer aqui.
        return
    existentes = {c["name"] for c in insp.get_columns("recebimentos_compra")}
    if "nota_entrada_id" not in existentes:
        # FK no próprio ADD COLUMN (o SQLite não aceita ADD CONSTRAINT).
        op.execute(
            "ALTER TABLE recebimentos_compra ADD COLUMN nota_entrada_id "
            "INTEGER REFERENCES notas_entrada (id) ON DELETE SET NULL"
        )


def downgrade() -> None:
    with op.batch_alter_table("recebimentos_compra") as batch_op:
        batch_op.drop_column("nota_entrada_id")
