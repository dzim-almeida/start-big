"""fiscal (F3): piso da numeração — de onde a sequência é do StartBig

Revision ID: d7a3e9c2f418
Revises: c6f2d8a4b915
Create Date: 2026-10-06 18:00:00.000000

CONTEXTO (docs/fiscal-refatoracao-plano.md, F3):
- `empresa_fiscal_settings.numeracao_piso_nfe`: o último número informado À MÃO
  (configuração da numeração ou ajuste depois de uma Rejeição 539). Abaixo dele,
  número sem nota é do sistema anterior e NÃO é buraco a inutilizar — a SEFAZ
  recusa inutilizar número usado. Acima, vale a regra de sempre.

MIGRAÇÃO DE DADOS: NENHUMA. 0 = a regra de hoje, idêntica (todo número sem nota
de 1 até o contador é buraco). O piso só passa a valer quando alguém ajustar a
numeração à mão depois desta versão.

SEGURANÇA: pela ausência da COLUNA (o create_all pode já tê-la criado).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd7a3e9c2f418'
down_revision: Union[str, Sequence[str], None] = 'c6f2d8a4b915'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABELA = "empresa_fiscal_settings"
COLUNA = "numeracao_piso_nfe"


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if not insp.has_table(TABELA):
        return
    if COLUNA not in {c["name"] for c in insp.get_columns(TABELA)}:
        op.execute(f"ALTER TABLE {TABELA} ADD COLUMN {COLUNA} INTEGER NOT NULL DEFAULT 0")


def downgrade() -> None:
    with op.batch_alter_table(TABELA) as batch:
        batch.drop_column(COLUNA)
