"""peso da embalagem (A5): a etiqueta de envio soma o peso dos volumes

Revision ID: e4a7c1b93f20
Revises: d2f8b61e9a47
Create Date: 2026-10-01 10:00:00.000000

CONTEXTO (docs/produto-embalagens-plano.md, A5): peso opcional em cada
embalagem, em GRAMAS inteiras (mesma régua dos centavos: nada de float no
banco). A etiqueta de envio de uma venda soma `quantidade × peso` das linhas
de embalagem e sugere volumes e peso — o lojista ainda pode corrigir.

MIGRAÇÃO DE DADOS: NENHUMA. A coluna nasce nula; embalagem sem peso não muda
nada, e a etiqueta continua com o peso digitado à mão.

SEGURANÇA: decide pela ausência da COLUNA (o create_all() pode já tê-la criado).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e4a7c1b93f20'
down_revision: Union[str, Sequence[str], None] = 'd2f8b61e9a47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABELA = "produto_embalagens"
COLUNA = "peso_gramas"


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if not insp.has_table(TABELA):
        return
    if COLUNA not in {c["name"] for c in insp.get_columns(TABELA)}:
        op.execute(f"ALTER TABLE {TABELA} ADD COLUMN {COLUNA} INTEGER")


def downgrade() -> None:
    with op.batch_alter_table(TABELA) as batch_op:
        batch_op.drop_column(COLUNA)
