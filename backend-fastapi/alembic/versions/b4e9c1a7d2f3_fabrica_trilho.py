"""fabrica (F3): o trilho — etapas, sinal, instalação e log

Revision ID: b4e9c1a7d2f3
Revises: a2d8b3e5f107
Create Date: 2026-10-05 20:00:00.000000

CONTEXTO (docs/marcenaria-fabrica-plano.md, F3, §6):
- `ordens_servico.data_instalacao`              a fila de Compras (RC12);
- `ordens_servico.compra_liberada_em/_por/_motivo` compra antes do sinal (RC04);
- `configuracoes_os.fabrica_travar_etapas`      trava × aviso (D0b), padrão false;
- tabela `fabrica_fases_log`                    o histórico do trilho (RC18).

MIGRAÇÃO DE DADOS: NENHUMA. Nulos/false = como sempre foi.

SEGURANÇA: tabela pela ausência da TABELA; colunas pela ausência da COLUNA,
com `ADD COLUMN` direto (sem `batch_alter_table`, ver x7y8z9a0b1c2).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b4e9c1a7d2f3'
down_revision: Union[str, Sequence[str], None] = 'a2d8b3e5f107'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


COLUNAS = (
    ("ordens_servico", lambda: sa.Column("data_instalacao", sa.Date(), nullable=True)),
    ("ordens_servico", lambda: sa.Column("compra_liberada_em", sa.DateTime(), nullable=True)),
    ("ordens_servico", lambda: sa.Column("compra_liberada_por", sa.String(length=100), nullable=True)),
    ("ordens_servico", lambda: sa.Column("compra_liberada_motivo", sa.Text(), nullable=True)),
    ("configuracoes_os", lambda: sa.Column("fabrica_travar_etapas", sa.Boolean(), nullable=False, server_default="0")),
)


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    for tabela, fabrica in COLUNAS:
        if not insp.has_table(tabela):
            continue
        coluna = fabrica()
        if coluna.name not in {c["name"] for c in insp.get_columns(tabela)}:
            op.add_column(tabela, coluna)

    if insp.has_table("ordens_servico") and not insp.has_table("fabrica_fases_log"):
        op.create_table(
            "fabrica_fases_log",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("os_id", sa.Integer(), nullable=False),
            sa.Column("fase_anterior", sa.String(length=30), nullable=True),
            sa.Column("fase_nova", sa.String(length=30), nullable=True),
            sa.Column("evento", sa.String(length=30), nullable=False),
            sa.Column("motivo", sa.Text(), nullable=True),
            sa.Column("usuario", sa.String(length=255), nullable=True),
            sa.Column("ocorrido_em", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["os_id"], ["ordens_servico.id"], ondelete="CASCADE"),
        )
        op.create_index("ix_fabrica_fases_log_id", "fabrica_fases_log", ["id"])
        op.create_index("ix_fabrica_fases_log_os_id", "fabrica_fases_log", ["os_id"])


def downgrade() -> None:
    op.drop_table("fabrica_fases_log")
    for tabela, fabrica in reversed(COLUNAS):
        with op.batch_alter_table(tabela) as batch:
            batch.drop_column(fabrica().name)
