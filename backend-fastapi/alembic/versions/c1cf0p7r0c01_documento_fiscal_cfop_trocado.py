"""fiscal: CFOP trocado na conferencia da NF-e

Revision ID: c1cf0p7r0c01
Revises: n5f0m2padr01
Create Date: 2026-11-01 10:00:00.000000

CONTEXTO (docs/nfe-cfop-e-notas-da-os-plano.md, C1; pedido do Alan em
01/11/2026): o CFOP pode ser trocado na hora da nota, sem mexer no cadastro.
O documento guarda o que foi trocado e por quem -- e a reemissao de uma nota
recusada repete a mesma troca.

MIGRACAO DE DADOS: NENHUMA. A coluna nasce NULL -- toda nota antiga saiu com o
CFOP sugerido, que e exatamente o que NULL quer dizer.

SEGURANCA (PR8): a coluna so e criada se AUSENTE; `ALTER TABLE ADD COLUMN`
nativo, sem recriar a tabela.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c1cf0p7r0c01'
down_revision: Union[str, Sequence[str], None] = 'n5f0m2padr01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABELA = "documento_fiscal"
COLUNA = "cfop_trocado"


def _tem_coluna(insp, tabela: str, coluna: str) -> bool:
    return any(c["name"] == coluna for c in insp.get_columns(tabela))


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if insp.has_table(TABELA) and not _tem_coluna(insp, TABELA, COLUNA):
        op.execute(f"ALTER TABLE {TABELA} ADD COLUMN {COLUNA} TEXT")


def downgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if insp.has_table(TABELA) and _tem_coluna(insp, TABELA, COLUNA):
        with op.batch_alter_table(TABELA) as batch_op:
            batch_op.drop_column(COLUNA)
