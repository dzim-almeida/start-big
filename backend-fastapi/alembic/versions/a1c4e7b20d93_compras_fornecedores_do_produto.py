"""compras (fase 1): fornecedores do produto

Revision ID: a1c4e7b20d93
Revises: f6b3d82a1c47
Create Date: 2026-10-03 15:00:00.000000

CONTEXTO (docs/compras-plano.md, fase 1):
- `produto_fornecedores`: de quem a loja compra cada produto — código do
  fornecedor, embalagem de compra (fator), prazo e último preço pago. Base das
  Necessidades de compra e do aviso de fornecedor mais barato (D13, D18).

MIGRAÇÃO DE DADOS: NENHUMA. A tabela nasce vazia e se preenche sozinha a cada
nota importada por XML (e pela aba Fornecedores do produto, com o módulo).

SEGURANÇA: decide pela ausência da TABELA (o create_all() do startup pode já
tê-la criado). Não toca tabela existente. Rodar de novo não muda nada.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1c4e7b20d93'
down_revision: Union[str, Sequence[str], None] = 'f6b3d82a1c47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())

    if not insp.has_table("produto_fornecedores"):
        op.create_table(
            "produto_fornecedores",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("produto_id", sa.Integer(), nullable=False),
            sa.Column("fornecedor_id", sa.Integer(), nullable=False),
            sa.Column("codigo_fornecedor", sa.String(length=60), nullable=True),
            sa.Column("embalagem_id", sa.Integer(), nullable=True),
            sa.Column("fator", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("ultimo_preco", sa.Integer(), nullable=True),
            sa.Column("ultima_compra_em", sa.Date(), nullable=True),
            sa.Column("prazo_dias", sa.Integer(), nullable=True),
            sa.Column("criado_em", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("atualizado_em", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["produto_id"], ["produtos.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["fornecedor_id"], ["fornecedores.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["embalagem_id"], ["produto_embalagens.id"], ondelete="SET NULL"),
            sa.UniqueConstraint("produto_id", "fornecedor_id", name="uq_produto_fornecedor"),
        )
        op.create_index("ix_produto_fornecedores_id", "produto_fornecedores", ["id"])
        op.create_index("ix_produto_fornecedores_produto_id", "produto_fornecedores", ["produto_id"])
        op.create_index("ix_produto_fornecedores_fornecedor_id", "produto_fornecedores", ["fornecedor_id"])


def downgrade() -> None:
    op.drop_table("produto_fornecedores")
