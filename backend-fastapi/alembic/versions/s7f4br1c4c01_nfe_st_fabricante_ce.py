"""fiscal: opcao do fabricante do CE com ICMS-ST recolhido em DAE

Revision ID: s7f4br1c4c01
Revises: c1cf0p7r0c01
Create Date: 2026-11-05 10:00:00.000000

CONTEXTO: orientacao do contador da marcenaria do Junior em 05/11/2026 (Decreto
CE 32.900/2018). Ver `services/fiscal/derivacao/st_fabricante_ce.py`.

MIGRACAO DE DADOS: NENHUMA. A coluna nasce 0 (desligada) em toda loja, e a nota
continua a mesma de antes.

SEGURANCA (PR8): a coluna so e criada se AUSENTE; `ALTER TABLE ADD COLUMN`
nativo, sem recriar a tabela.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 's7f4br1c4c01'
down_revision: Union[str, Sequence[str], None] = 'c1cf0p7r0c01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABELA = "empresa_fiscal_settings"
COLUNA = "nfe_st_fabricante_ce"


def _tem_coluna(insp, tabela: str, coluna: str) -> bool:
    return any(c["name"] == coluna for c in insp.get_columns(tabela))


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if insp.has_table(TABELA) and not _tem_coluna(insp, TABELA, COLUNA):
        op.execute(f"ALTER TABLE {TABELA} ADD COLUMN {COLUNA} BOOLEAN NOT NULL DEFAULT 0")


def downgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if insp.has_table(TABELA) and _tem_coluna(insp, TABELA, COLUNA):
        with op.batch_alter_table(TABELA) as batch_op:
            batch_op.drop_column(COLUNA)
