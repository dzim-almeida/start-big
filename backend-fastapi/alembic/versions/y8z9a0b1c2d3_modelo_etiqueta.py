"""cria modelo_etiqueta

Revision ID: y8z9a0b1c2d3
Revises: x7y8z9a0b1c2
Create Date: 2026-09-27 12:00:00.000000

CONTEXTO (docs/etiquetas-plano.md, fase 1):
Os modelos de etiqueta que o lojista cria (página + elementos em mm) ficam no
banco para aparecerem em todos os terminais da loja. Os presets de fábrica
ficam no código do frontend e não passam por aqui.

MIGRAÇÃO DE DADOS: NENHUMA. A tabela nasce vazia.

SEGURANÇA:
- Decide pela ausência da TABELA: se o create_all() do startup já a criou,
  não há nada a fazer.
- Nenhuma tabela existente é alterada.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'y8z9a0b1c2d3'
down_revision: Union[str, Sequence[str], None] = 'x7y8z9a0b1c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABELA = "modelo_etiqueta"


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if insp.has_table(TABELA):
        return

    op.create_table(
        TABELA,
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("empresa_id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=80), nullable=False),
        sa.Column("fonte", sa.String(length=20), nullable=False),
        sa.Column("definicao", sa.JSON(), nullable=False),
        sa.Column("data_criacao", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("data_atualizacao", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="CASCADE"),
    )
    op.create_index(f"ix_{TABELA}_id", TABELA, ["id"])
    op.create_index(f"ix_{TABELA}_empresa_id", TABELA, ["empresa_id"])


def downgrade() -> None:
    op.drop_index(f"ix_{TABELA}_empresa_id", table_name=TABELA)
    op.drop_index(f"ix_{TABELA}_id", table_name=TABELA)
    op.drop_table(TABELA)
