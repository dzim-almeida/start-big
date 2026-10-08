"""compras (fase 2): pedido de compra, itens, parcelas e histórico

Revision ID: b7d2f4a9c315
Revises: a1c4e7b20d93
Create Date: 2026-10-03 18:00:00.000000

CONTEXTO (docs/compras-plano.md, fase 2):
- `pedidos_compra`: o compromisso com o fornecedor (situação, previsão,
  condição de pagamento, totais). `numero` ÚNICO → "PC-000123".
- `pedido_compra_itens`: o que foi pedido, na unidade de compra (fator).
- `pedido_compra_parcelas`: a condição combinada (NÃO é conta a pagar; a
  conta nasce no recebimento, fase 3).
- `compras_log`: histórico só de INSERT (quem, quando, por quê).

MIGRAÇÃO DE DADOS: NENHUMA. Tabelas novas nascem vazias.

SEGURANÇA: decide pela ausência de cada TABELA (o create_all() do startup pode
já tê-las criado). Não toca tabela existente. Rodar de novo não muda nada.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b7d2f4a9c315'
down_revision: Union[str, Sequence[str], None] = 'a1c4e7b20d93'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())

    if not insp.has_table("pedidos_compra"):
        op.create_table(
            "pedidos_compra",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("empresa_id", sa.Integer(), nullable=True),
            sa.Column("numero", sa.Integer(), nullable=False),
            sa.Column("tipo", sa.String(length=20), nullable=False, server_default="MATERIAL"),
            sa.Column("situacao", sa.String(length=20), nullable=False, server_default="RASCUNHO"),
            sa.Column("fornecedor_id", sa.Integer(), nullable=True),
            sa.Column("fornecedor_nome", sa.String(length=255), nullable=False),
            sa.Column("previsao_entrega", sa.Date(), nullable=True),
            sa.Column("condicao_pagamento", sa.String(length=60), nullable=True),
            sa.Column("frete", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("desconto", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("valor_itens", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("valor_total", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("observacao", sa.Text(), nullable=True),
            sa.Column("enviado_em", sa.DateTime(), nullable=True),
            sa.Column("cancelado_em", sa.DateTime(), nullable=True),
            sa.Column("motivo_cancelamento", sa.String(length=255), nullable=True),
            sa.Column("criado_por_id", sa.Integer(), nullable=True),
            sa.Column("criado_por_nome", sa.String(length=255), nullable=True),
            sa.Column("criado_em", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("atualizado_em", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["fornecedor_id"], ["fornecedores.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["criado_por_id"], ["usuarios.id"], ondelete="SET NULL"),
            sa.UniqueConstraint("numero", name="uq_pedido_compra_numero"),
        )
        op.create_index("ix_pedidos_compra_id", "pedidos_compra", ["id"])
        op.create_index("ix_pedidos_compra_empresa_id", "pedidos_compra", ["empresa_id"])
        op.create_index("ix_pedidos_compra_situacao", "pedidos_compra", ["situacao"])
        op.create_index("ix_pedidos_compra_fornecedor_id", "pedidos_compra", ["fornecedor_id"])

    if not insp.has_table("pedido_compra_itens"):
        op.create_table(
            "pedido_compra_itens",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("pedido_id", sa.Integer(), nullable=False),
            sa.Column("produto_id", sa.Integer(), nullable=True),
            sa.Column("descricao", sa.String(length=255), nullable=False),
            sa.Column("codigo_fornecedor", sa.String(length=60), nullable=True),
            sa.Column("embalagem_id", sa.Integer(), nullable=True),
            sa.Column("unidade_compra", sa.String(length=10), nullable=False, server_default="UN"),
            sa.Column("fator", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("quantidade", sa.Integer(), nullable=False),
            sa.Column("quantidade_recebida", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("quantidade_cancelada", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("custo_unitario", sa.Integer(), nullable=False, server_default="0"),
            sa.ForeignKeyConstraint(["pedido_id"], ["pedidos_compra.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["produto_id"], ["produtos.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["embalagem_id"], ["produto_embalagens.id"], ondelete="SET NULL"),
        )
        op.create_index("ix_pedido_compra_itens_id", "pedido_compra_itens", ["id"])
        op.create_index("ix_pedido_compra_itens_pedido_id", "pedido_compra_itens", ["pedido_id"])
        op.create_index("ix_pedido_compra_itens_produto_id", "pedido_compra_itens", ["produto_id"])

    if not insp.has_table("pedido_compra_parcelas"):
        op.create_table(
            "pedido_compra_parcelas",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("pedido_id", sa.Integer(), nullable=False),
            sa.Column("numero", sa.Integer(), nullable=False),
            sa.Column("dias", sa.Integer(), nullable=False),
            sa.Column("valor", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["pedido_id"], ["pedidos_compra.id"], ondelete="CASCADE"),
        )
        op.create_index("ix_pedido_compra_parcelas_id", "pedido_compra_parcelas", ["id"])
        op.create_index("ix_pedido_compra_parcelas_pedido_id", "pedido_compra_parcelas", ["pedido_id"])

    if not insp.has_table("compras_log"):
        op.create_table(
            "compras_log",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("objeto", sa.String(length=20), nullable=False),
            sa.Column("objeto_id", sa.Integer(), nullable=False),
            sa.Column("acao", sa.String(length=40), nullable=False),
            sa.Column("situacao_anterior", sa.String(length=20), nullable=True),
            sa.Column("situacao_nova", sa.String(length=20), nullable=True),
            sa.Column("motivo", sa.String(length=255), nullable=True),
            sa.Column("usuario_id", sa.Integer(), nullable=True),
            sa.Column("usuario_nome", sa.String(length=255), nullable=True),
            sa.Column("ocorrido_em", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="SET NULL"),
        )
        op.create_index("ix_compras_log_id", "compras_log", ["id"])
        op.create_index("ix_compras_log_objeto_id", "compras_log", ["objeto_id"])


def downgrade() -> None:
    op.drop_table("compras_log")
    op.drop_table("pedido_compra_parcelas")
    op.drop_table("pedido_compra_itens")
    op.drop_table("pedidos_compra")
