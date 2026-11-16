"""perfil_tributario_id em produto_fiscal

Revision ID: w6x7y8z9a0b1
Revises: v5w6x7y8z9a0
Create Date: 2026-09-18 23:30:00.000000

CONTEXTO (TASK006):
O produto aponta para um perfil tributário (TASK004) para as operações
interestaduais. Coluna nullable com ON DELETE SET NULL: apagar um perfil
nunca apaga produto -- ele só volta a "sem perfil".

SEGURANÇA:
- A coluna é adicionada só se AUSENTE: o create_all() do startup pode já
  tê-la criado num banco novo.
- Sem batch_alter_table no upgrade: o boot roda com PRAGMA foreign_keys=ON e
  recriar `produto_fiscal` (referenciada por `produtos`) falha no DROP (ver
  u4v5w6x7y8z9). `ALTER TABLE ADD COLUMN ... REFERENCES` é nativo no SQLite.
- Nasce NULL em todas as linhas: nenhum produto ganha perfil por acidente.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'w6x7y8z9a0b1'
down_revision: Union[str, Sequence[str], None] = 'v5w6x7y8z9a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABELA = "produto_fiscal"
COLUNA = "perfil_tributario_id"
INDICE = f"ix_{TABELA}_{COLUNA}"


def _tem_coluna(insp) -> bool:
    return any(c["name"] == COLUNA for c in insp.get_columns(TABELA))


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if _tem_coluna(insp):
        return

    # `op.add_column` com ForeignKey tenta um ADD CONSTRAINT separado, que o
    # SQLite não tem; a forma nativa é a FK inline no próprio ADD COLUMN.
    op.execute(
        f"ALTER TABLE {TABELA} ADD COLUMN {COLUNA} INTEGER "
        f"REFERENCES perfil_tributario (id) ON DELETE SET NULL"
    )
    op.create_index(INDICE, TABELA, [COLUNA])


def downgrade() -> None:
    op.drop_index(INDICE, table_name=TABELA)
    with op.batch_alter_table(TABELA) as batch_op:
        batch_op.drop_column(COLUNA)
