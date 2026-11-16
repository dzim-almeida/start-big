"""lava-rapido (Spec 08A): agendamentos

Revision ID: l4v4ag3nd003
Revises: l4v4ex3c0002
Create Date: 2026-11-12 22:00:00.000000

CONTEXTO (backend-fastapi/docs/lava-rapido/SPEC-08A-AGENDA-BACKEND-LAVA-RAPIDO.md):
- `agendamentos`: o horario marcado ANTES da OS (SPEC-00 O11); vira OS quando
  o cliente chega (`numero_os`).

MIGRACAO DE DADOS: NENHUMA. A tabela nasce vazia.

SEGURANCA (PR8): decide pela ausencia da TABELA (o create_all() do startup
costuma cria-la antes). Nenhuma tabela existente e alterada.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'l4v4ag3nd003'
down_revision: Union[str, Sequence[str], None] = 'l4v4ex3c0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABELA = "agendamentos"


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if insp.has_table(TABELA):
        return
    # Mesmas colunas do model (app/db/models/lava_rapido/agendamento.py).
    op.create_table(
        TABELA,
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("inicio", sa.DateTime(), nullable=False),
        sa.Column("duracao_minutos", sa.Integer(), nullable=True),
        sa.Column("cliente_id", sa.Integer(), nullable=True),
        sa.Column("cliente_nome", sa.String(length=255), nullable=False),
        sa.Column("cliente_contato", sa.String(length=20), nullable=True),
        sa.Column("placa", sa.String(length=20), nullable=True),
        sa.Column("veiculo", sa.String(length=120), nullable=True),
        sa.Column("tipo_veiculo", sa.String(length=30), nullable=True),
        sa.Column("porte_id", sa.Integer(), nullable=True),
        sa.Column("servicos", sa.JSON(), nullable=False),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("situacao", sa.String(length=15), nullable=False),
        sa.Column("numero_os", sa.String(length=20), nullable=True),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cliente_id"], ["clientes.id"]),
        sa.ForeignKeyConstraint(["porte_id"], ["portes_veiculo.id"], ondelete="SET NULL"),
    )
    op.create_index(f"ix_{TABELA}_id", TABELA, ["id"])
    op.create_index(f"ix_{TABELA}_inicio", TABELA, ["inicio"])
    op.create_index(f"ix_{TABELA}_situacao", TABELA, ["situacao"])


def downgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if insp.has_table(TABELA):
        op.drop_table(TABELA)
