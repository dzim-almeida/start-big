"""cria perfil_tributario e regra_perfil_tributario

Revision ID: v5w6x7y8z9a0
Revises: u4v5w6x7y8z9
Create Date: 2026-09-18 22:00:00.000000

CONTEXTO (TASK004):
Operação interestadual precisa de alíquotas que variam por UF de destino
(interestadual, interna do destino, FCP, MVA-ST). O perfil tributário agrupa
essas regras uma vez e N produtos apontam para ele -- complementa a cascata
de `tributacao.py`, não a substitui.

MIGRAÇÃO DE DADOS: NENHUMA. As duas tabelas nascem vazias; nada do sistema
existente lê delas ainda (o vínculo com o produto é a TASK006).

SEGURANÇA:
- Decide pela ausência da TABELA: se o create_all() do startup já as criou,
  não há nada a fazer.
- Nenhuma tabela existente é alterada.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'v5w6x7y8z9a0'
down_revision: Union[str, Sequence[str], None] = 'u4v5w6x7y8z9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PERFIL = "perfil_tributario"
REGRA = "regra_perfil_tributario"


def _criar_perfil() -> None:
    op.create_table(
        PERFIL,
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("empresa_id", sa.Integer(), nullable=False),
        sa.Column("descricao", sa.String(length=120), nullable=False),
        sa.Column("data_criacao", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("data_atualizacao", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="CASCADE"),
    )
    op.create_index(f"ix_{PERFIL}_id", PERFIL, ["id"])
    op.create_index(f"ix_{PERFIL}_empresa_id", PERFIL, ["empresa_id"])


def _criar_regra() -> None:
    op.create_table(
        REGRA,
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("perfil_id", sa.Integer(), nullable=False),
        sa.Column("uf_destino", sa.String(length=2), nullable=True),
        sa.Column("ncm_excecao", sa.String(length=8), nullable=True),
        sa.Column("aliquota_interestadual", sa.Integer(), nullable=False),
        sa.Column("aliquota_interna_destino", sa.Integer(), nullable=False),
        sa.Column("percentual_fcp", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("calculo_base_dupla", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("mva_st", sa.Integer(), nullable=True),
        sa.Column("reducao_base_calculo", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["perfil_id"], [f"{PERFIL}.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("perfil_id", "uf_destino", "ncm_excecao", name="uq_regra_perfil_uf_ncm"),
    )
    op.create_index(f"ix_{REGRA}_id", REGRA, ["id"])
    op.create_index(f"ix_{REGRA}_perfil_id", REGRA, ["perfil_id"])


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())

    if not insp.has_table(PERFIL):
        _criar_perfil()
    if not insp.has_table(REGRA):
        _criar_regra()


def downgrade() -> None:
    # A regra referencia o perfil: cai primeiro.
    op.drop_table(REGRA)
    op.drop_table(PERFIL)
