"""marcenaria: venda para entrega futura -- o papel da nota e o simples faturamento de cada movel

Revision ID: f4t1m0v3l002
Revises: f4t1m0v3l001
Create Date: 2026-10-24 23:00:00.000000

CONTEXTO (docs/marcenaria-faturamento-plano.md, F4): no modo ENTREGA_FUTURA a
OS tem uma nota de SIMPLES FATURAMENTO (5922) e uma nota de REMESSA (5116/5117)
a cada entrega, que aponta para a primeira.
- `documento_fiscal.papel`: NULL em toda nota de hoje (o comportamento de
  sempre) | SIMPLES_FATURAMENTO | REMESSA_ENTREGA_FUTURA | VENDA_MARCENARIA;
- `marcenaria_moveis.simples_faturamento_id`: a 5922 que cobre o movel (o
  aditivo, aprovado depois, ganha a sua).

MIGRACAO DE DADOS: NENHUMA. Toda nota existente fica com papel NULL.

SEGURANCA (PR8): cada coluna so e criada se AUSENTE; `ALTER TABLE ADD COLUMN`
nativo, sem recriar a tabela (documento_fiscal e grande e e referenciada).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f4t1m0v3l002'
down_revision: Union[str, Sequence[str], None] = 'f4t1m0v3l001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

COLUNAS = (
    ("documento_fiscal", "papel", "VARCHAR(25)"),
    ("marcenaria_moveis", "simples_faturamento_id", "INTEGER REFERENCES documento_fiscal (id) ON DELETE SET NULL"),
)


def _tem_coluna(insp, tabela: str, coluna: str) -> bool:
    return any(c["name"] == coluna for c in insp.get_columns(tabela))


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    for tabela, coluna, ddl in COLUNAS:
        if insp.has_table(tabela) and not _tem_coluna(insp, tabela, coluna):
            op.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {ddl}")


def downgrade() -> None:
    for tabela, coluna, _ddl in reversed(COLUNAS):
        insp = sa.inspect(op.get_bind())
        if insp.has_table(tabela) and _tem_coluna(insp, tabela, coluna):
            with op.batch_alter_table(tabela) as batch_op:
                batch_op.drop_column(coluna)
