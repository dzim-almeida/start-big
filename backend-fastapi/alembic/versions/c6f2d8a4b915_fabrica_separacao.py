"""fabrica (F4): separação bipada e custo real no item da OS

Revision ID: c6f2d8a4b915
Revises: b4e9c1a7d2f3
Create Date: 2026-10-06 10:00:00.000000

CONTEXTO (docs/marcenaria-fabrica-plano.md, F4, D6/D7):
- `ordem_servico_itens.quantidade_separada`  o que já saiu do estoque na
  separação (a baixa acontece ali; o finalizar baixa só o resto);
- `ordem_servico_itens.custo_real`           custo médio do estoque no momento
  da separação, para a margem real (o `custo_unitario` congelado não muda).

MIGRAÇÃO DE DADOS: NENHUMA. Nulo = nada separado = a conta de sempre.

SEGURANÇA: pela ausência da COLUNA, `ADD COLUMN` direto (ver x7y8z9a0b1c2).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c6f2d8a4b915'
down_revision: Union[str, Sequence[str], None] = 'b4e9c1a7d2f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


COLUNAS = (
    ("ordem_servico_itens", lambda: sa.Column("quantidade_separada", sa.Float(), nullable=True)),
    ("ordem_servico_itens", lambda: sa.Column("custo_real", sa.Integer(), nullable=True)),
)


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    for tabela, fabrica in COLUNAS:
        if not insp.has_table(tabela):
            continue
        coluna = fabrica()
        if coluna.name not in {c["name"] for c in insp.get_columns(tabela)}:
            op.add_column(tabela, coluna)


def downgrade() -> None:
    for tabela, fabrica in reversed(COLUNAS):
        with op.batch_alter_table(tabela) as batch:
            batch.drop_column(fabrica().name)
