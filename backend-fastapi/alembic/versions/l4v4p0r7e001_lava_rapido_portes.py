"""lava-rapido (Spec 02A): portes da loja e preco/duracao por porte

Revision ID: l4v4p0r7e001
Revises: s7f4br1c4c01
Create Date: 2026-11-12 18:00:00.000000

CONTEXTO (backend-fastapi/docs/lava-rapido/SPEC-02A-PRECO-POR-PORTE-BACKEND-LAVA-RAPIDO.md):
- `portes_veiculo`: a lista de portes da loja, por tipo de veiculo (P2a).
- `servico_precos_porte`: preco em centavos e duracao em minutos de cada
  servico para cada porte (P1, P5).

MIGRACAO DE DADOS: NENHUMA. As duas tabelas nascem vazias; a lista inicial de
portes e gravada na primeira leitura, so no segmento com `preco_por_porte`.

SEGURANCA:
- Decide pela ausencia de CADA tabela: o create_all() do startup costuma
  cria-las antes desta migracao rodar; nesse caso nao ha nada a fazer.
- Nenhuma tabela existente e alterada (`servicos` continua igual).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'l4v4p0r7e001'
down_revision: Union[str, Sequence[str], None] = 's7f4br1c4c01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PORTES = "portes_veiculo"
PRECOS = "servico_precos_porte"


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())                     # o que o banco tem AGORA

    # Mesmas colunas do model (app/db/models/lava_rapido/porte.py).
    if not insp.has_table(PORTES):
        op.create_table(
            PORTES,
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("tipo_veiculo", sa.String(length=30), nullable=False),
            sa.Column("nome", sa.String(length=60), nullable=False),
            sa.Column("ordem", sa.Integer(), nullable=False),
            sa.Column("ativo", sa.Boolean(), nullable=False),
            sa.UniqueConstraint("tipo_veiculo", "nome", name="uq_portes_veiculo_tipo_nome"),
        )
        op.create_index(f"ix_{PORTES}_id", PORTES, ["id"])
        op.create_index(f"ix_{PORTES}_tipo_veiculo", PORTES, ["tipo_veiculo"])

    if not insp.has_table(PRECOS):
        op.create_table(
            PRECOS,
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("servico_id", sa.Integer(), nullable=False),
            sa.Column("porte_id", sa.Integer(), nullable=False),
            sa.Column("valor", sa.Integer(), nullable=False),
            sa.Column("duracao_minutos", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(["servico_id"], ["servicos.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["porte_id"], [f"{PORTES}.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("servico_id", "porte_id", name="uq_servico_precos_porte"),
        )
        op.create_index(f"ix_{PRECOS}_id", PRECOS, ["id"])
        op.create_index(f"ix_{PRECOS}_servico_id", PRECOS, ["servico_id"])
        op.create_index(f"ix_{PRECOS}_porte_id", PRECOS, ["porte_id"])


def downgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if insp.has_table(PRECOS):                           # filha primeiro (FK)
        op.drop_table(PRECOS)
    if insp.has_table(PORTES):
        op.drop_table(PORTES)
