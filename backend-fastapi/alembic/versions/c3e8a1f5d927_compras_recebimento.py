"""compras (fase 3): recebimento do pedido, elo no livro de estoque e nas contas a pagar

Revision ID: c3e8a1f5d927
Revises: b7d2f4a9c315
Create Date: 2026-10-03 21:00:00.000000

CONTEXTO (docs/compras-plano.md, fase 3):
- `recebimentos_compra`: cada chegada de mercadoria de um pedido (parcial ou
  total), com os valores reais daquela chegada.
- `recebimento_compra_itens`: o que chegou de cada item, o custo real e a
  movimentação de estoque que gerou.
- `movimentacoes_estoque.recebimento_compra_id`: de que recebimento veio a
  entrada (origem COMPRA).
- `contas_pagar.recebimento_compra_id`: de que recebimento veio a conta.

MIGRAÇÃO DE DADOS: NENHUMA. Tabelas novas nascem vazias; colunas nascem nulas.

SEGURANÇA: decide pela ausência de cada TABELA e COLUNA (o create_all() do
startup pode já ter criado as tabelas). Não altera nem apaga nada existente.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3e8a1f5d927'
down_revision: Union[str, Sequence[str], None] = 'b7d2f4a9c315'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())

    if not insp.has_table("recebimentos_compra"):
        op.create_table(
            "recebimentos_compra",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("empresa_id", sa.Integer(), nullable=True),
            sa.Column("pedido_id", sa.Integer(), nullable=False),
            sa.Column("numero_nota", sa.String(length=20), nullable=True),
            sa.Column("observacao", sa.Text(), nullable=True),
            sa.Column("valor_itens", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("valor_ajuste", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("valor_total", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("contas_pagar_lancadas", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("recebido_por_id", sa.Integer(), nullable=True),
            sa.Column("recebido_por_nome", sa.String(length=255), nullable=True),
            sa.Column("recebido_em", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["pedido_id"], ["pedidos_compra.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["recebido_por_id"], ["usuarios.id"], ondelete="SET NULL"),
        )
        op.create_index("ix_recebimentos_compra_id", "recebimentos_compra", ["id"])
        op.create_index("ix_recebimentos_compra_empresa_id", "recebimentos_compra", ["empresa_id"])
        op.create_index("ix_recebimentos_compra_pedido_id", "recebimentos_compra", ["pedido_id"])

    if not insp.has_table("recebimento_compra_itens"):
        op.create_table(
            "recebimento_compra_itens",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("recebimento_id", sa.Integer(), nullable=False),
            sa.Column("pedido_item_id", sa.Integer(), nullable=True),
            sa.Column("produto_id", sa.Integer(), nullable=True),
            sa.Column("descricao", sa.String(length=255), nullable=False),
            sa.Column("unidade_compra", sa.String(length=10), nullable=False, server_default="UN"),
            sa.Column("fator", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("quantidade", sa.Integer(), nullable=False),
            sa.Column("unidades", sa.Float(), nullable=False),
            sa.Column("custo_unitario", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("movimentacao_id", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(["recebimento_id"], ["recebimentos_compra.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["pedido_item_id"], ["pedido_compra_itens.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["produto_id"], ["produtos.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["movimentacao_id"], ["movimentacoes_estoque.id"], ondelete="SET NULL"),
        )
        op.create_index("ix_recebimento_compra_itens_id", "recebimento_compra_itens", ["id"])
        op.create_index("ix_recebimento_compra_itens_recebimento_id", "recebimento_compra_itens", ["recebimento_id"])
        op.create_index("ix_recebimento_compra_itens_pedido_item_id", "recebimento_compra_itens", ["pedido_item_id"])

    if insp.has_table("movimentacoes_estoque"):
        existentes = {c["name"] for c in insp.get_columns("movimentacoes_estoque")}
        if "recebimento_compra_id" not in existentes:
            # Mesmo padrão da f6b3d82a1c47: a FK vai no próprio ADD COLUMN, que o
            # SQLite aceita (ADD CONSTRAINT ele não aceita).
            op.execute(
                "ALTER TABLE movimentacoes_estoque ADD COLUMN recebimento_compra_id "
                "INTEGER REFERENCES recebimentos_compra (id) ON DELETE SET NULL"
            )

    if insp.has_table("contas_pagar"):
        existentes = {c["name"] for c in insp.get_columns("contas_pagar")}
        if "recebimento_compra_id" not in existentes:
            op.add_column("contas_pagar", sa.Column("recebimento_compra_id", sa.Integer(), nullable=True))
            op.create_index("ix_contas_pagar_recebimento_compra_id", "contas_pagar", ["recebimento_compra_id"])


def downgrade() -> None:
    with op.batch_alter_table("contas_pagar") as batch_op:
        batch_op.drop_index("ix_contas_pagar_recebimento_compra_id")
        batch_op.drop_column("recebimento_compra_id")
    with op.batch_alter_table("movimentacoes_estoque") as batch_op:
        batch_op.drop_column("recebimento_compra_id")
    op.drop_table("recebimento_compra_itens")
    op.drop_table("recebimentos_compra")
