"""entrada por XML da NF-e: notas importadas, De-Para do fornecedor e vínculo no livro

Revision ID: f6b3d82a1c47
Revises: e4a7c1b93f20
Create Date: 2026-10-01 14:00:00.000000

CONTEXTO (docs/entrada-xml-nfe-plano.md):
- `notas_entrada`: uma linha por NF-e de compra importada. A `chave` é ÚNICA —
  é o que impede importar a mesma nota duas vezes e dobrar o estoque.
- `produto_codigos_fornecedor`: o código do fornecedor (cProd) → produto,
  embalagem e fator. A próxima nota do mesmo fornecedor vem reconhecida.
- `movimentacoes_estoque.nota_entrada_id`: de que nota veio a entrada.

MIGRAÇÃO DE DADOS: NENHUMA. Tabelas novas nascem vazias; a coluna nasce nula.

SEGURANÇA: decide pela ausência de cada TABELA e COLUNA (o create_all() do
startup pode já ter criado as tabelas).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f6b3d82a1c47'
down_revision: Union[str, Sequence[str], None] = 'e4a7c1b93f20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())

    if not insp.has_table("notas_entrada"):
        op.create_table(
            "notas_entrada",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("empresa_id", sa.Integer(), nullable=True),
            sa.Column("chave", sa.String(length=44), nullable=False),
            sa.Column("numero", sa.String(length=9), nullable=False),
            sa.Column("serie", sa.String(length=3), nullable=False),
            sa.Column("emissao", sa.Date(), nullable=True),
            sa.Column("valor_total", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("fornecedor_id", sa.Integer(), nullable=True),
            sa.Column("fornecedor_nome", sa.String(length=255), nullable=True),
            sa.Column("itens_lancados", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("contas_pagar_lancadas", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("usuario_nome", sa.String(length=255), nullable=True),
            sa.Column("importada_em", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["fornecedor_id"], ["fornecedores.id"], ondelete="SET NULL"),
            sa.UniqueConstraint("chave"),
        )
        op.create_index("ix_notas_entrada_id", "notas_entrada", ["id"])
        op.create_index("ix_notas_entrada_empresa_id", "notas_entrada", ["empresa_id"])
        op.create_index("ix_notas_entrada_fornecedor_id", "notas_entrada", ["fornecedor_id"])

    if not insp.has_table("produto_codigos_fornecedor"):
        op.create_table(
            "produto_codigos_fornecedor",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("fornecedor_id", sa.Integer(), nullable=False),
            sa.Column("codigo_fornecedor", sa.String(length=60), nullable=False),
            sa.Column("produto_id", sa.Integer(), nullable=False),
            sa.Column("embalagem_id", sa.Integer(), nullable=True),
            sa.Column("fator", sa.Integer(), nullable=False, server_default="1"),
            sa.ForeignKeyConstraint(["fornecedor_id"], ["fornecedores.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["produto_id"], ["produtos.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["embalagem_id"], ["produto_embalagens.id"], ondelete="SET NULL"),
            sa.UniqueConstraint("fornecedor_id", "codigo_fornecedor", name="uq_produto_codigo_fornecedor"),
        )
        op.create_index("ix_produto_codigos_fornecedor_id", "produto_codigos_fornecedor", ["id"])
        op.create_index("ix_produto_codigos_fornecedor_fornecedor_id", "produto_codigos_fornecedor", ["fornecedor_id"])
        op.create_index("ix_produto_codigos_fornecedor_produto_id", "produto_codigos_fornecedor", ["produto_id"])

    if insp.has_table("movimentacoes_estoque"):
        existentes = {c["name"] for c in insp.get_columns("movimentacoes_estoque")}
        if "nota_entrada_id" not in existentes:
            # Mesmo padrão da e7b2c9d41f60: a FK vai no próprio ADD COLUMN,
            # que o SQLite aceita (ADD CONSTRAINT ele não aceita).
            op.execute(
                "ALTER TABLE movimentacoes_estoque ADD COLUMN nota_entrada_id "
                "INTEGER REFERENCES notas_entrada (id) ON DELETE SET NULL"
            )


def downgrade() -> None:
    with op.batch_alter_table("movimentacoes_estoque") as batch_op:
        batch_op.drop_column("nota_entrada_id")
    op.drop_table("produto_codigos_fornecedor")
    op.drop_table("notas_entrada")
