"""cria produto_embalagens e a chave usar_embalagens

Revision ID: a0b1c2d3e4f5
Revises: z9a0b1c2d3e4
Create Date: 2026-09-27 16:00:00.000000

CONTEXTO (docs/produto-embalagens-plano.md, fase 1):
Embalagens do produto (fardo, caixa, pack) com fator, código e preço, e a
chave "Usar embalagens" nas configurações de produto (desligada por padrão).

MIGRAÇÃO DE DADOS: NENHUMA. A tabela nasce vazia; a chave nasce FALSA — quem
não liga continua exatamente como antes.

SEGURANÇA:
- Tabela: decide pela ausência da TABELA (o create_all() do startup pode já
  tê-la criado).
- Coluna: decide pela ausência da COLUNA, e nasce com default 0 — as
  configurações existentes ficam com a chave desligada.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a0b1c2d3e4f5'
down_revision: Union[str, Sequence[str], None] = 'z9a0b1c2d3e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABELA = "produto_embalagens"
CONFIG = "configuracoes_produtos"
COLUNA = "usar_embalagens"


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())

    if not insp.has_table(TABELA):
        op.create_table(
            TABELA,
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("produto_id", sa.Integer(), nullable=False),
            sa.Column("sigla", sa.String(length=6), nullable=False),
            sa.Column("descricao", sa.String(length=60), nullable=True),
            sa.Column("fator", sa.Integer(), nullable=False),
            sa.Column("codigo_barras", sa.String(length=20), nullable=True),
            sa.Column("preco", sa.Integer(), nullable=True),
            sa.Column("desconto_bp", sa.Integer(), nullable=True),
            sa.Column("vende_no_pdv", sa.Boolean(), nullable=False, server_default=sa.text("1")),
            sa.Column("usa_na_entrada", sa.Boolean(), nullable=False, server_default=sa.text("1")),
            sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("1")),
            sa.Column("data_criacao", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("data_atualizacao", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["produto_id"], ["produtos.id"], ondelete="CASCADE"),
        )
        op.create_index(f"ix_{TABELA}_id", TABELA, ["id"])
        op.create_index(f"ix_{TABELA}_produto_id", TABELA, ["produto_id"])
        op.create_index(f"ix_{TABELA}_codigo_barras", TABELA, ["codigo_barras"])

    if insp.has_table(CONFIG) and COLUNA not in {c["name"] for c in insp.get_columns(CONFIG)}:
        op.execute(f"ALTER TABLE {CONFIG} ADD COLUMN {COLUNA} BOOLEAN NOT NULL DEFAULT 0")


def downgrade() -> None:
    op.drop_index(f"ix_{TABELA}_codigo_barras", table_name=TABELA)
    op.drop_index(f"ix_{TABELA}_produto_id", table_name=TABELA)
    op.drop_index(f"ix_{TABELA}_id", table_name=TABELA)
    op.drop_table(TABELA)
    with op.batch_alter_table(CONFIG) as batch_op:
        batch_op.drop_column(COLUNA)
