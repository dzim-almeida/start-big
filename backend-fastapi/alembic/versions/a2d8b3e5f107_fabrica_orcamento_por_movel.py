"""fabrica (F2): orçamento por móvel que gera a OS

Revision ID: a2d8b3e5f107
Revises: f1c7a2d9e3b4
Create Date: 2026-10-05 15:00:00.000000

CONTEXTO (docs/marcenaria-fabrica-plano.md, F2, §4):
- tabelas `fabrica_orcamentos`, `fabrica_ambientes`, `fabrica_moveis`,
  `fabrica_materiais` (a árvore versão → ambiente → móvel → material);
- `configuracoes_os.modo_fabrica`        a chave da loja (D0), padrão false;
- `ordens_servico.fase_fabrica`          nulo = OS comum (D5);
- `ordem_servico_itens.fabrica_orcamento_id` / `fabrica_movel_id`
                                         o item foi gerado pela aprovação (D12).

MIGRAÇÃO DE DADOS: NENHUMA. Tudo nulo/false/vazio = como sempre foi.

SEGURANÇA:
- Tabelas: pela ausência da TABELA (o `create_all()` do startup costuma
  chegar antes e criá-las vazias — aí não há o que fazer).
- Colunas: pela ausência da COLUNA, uma a uma. `ADD COLUMN` direto, sem
  `batch_alter_table`: as três tabelas são alvo de FK (com
  PRAGMA foreign_keys=ON o batch quebra; ver x7y8z9a0b1c2).
- As colunas de FK do item entram como INTEGER simples: o SQLite não
  acrescenta constraint a tabela existente. A FK existe no modelo e vale em
  banco novo; aqui o código é quem garante (o item só recebe ids que acabou
  de criar).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a2d8b3e5f107'
down_revision: Union[str, Sequence[str], None] = 'f1c7a2d9e3b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


COLUNAS = (
    ("configuracoes_os", lambda: sa.Column("modo_fabrica", sa.Boolean(), nullable=False, server_default="0")),
    ("ordens_servico", lambda: sa.Column("fase_fabrica", sa.String(length=30), nullable=True)),
    ("ordem_servico_itens", lambda: sa.Column("fabrica_orcamento_id", sa.Integer(), nullable=True)),
    ("ordem_servico_itens", lambda: sa.Column("fabrica_movel_id", sa.Integer(), nullable=True)),
)


def _criar_tabelas(insp) -> None:
    if not insp.has_table("fabrica_orcamentos"):
        op.create_table(
            "fabrica_orcamentos",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("os_id", sa.Integer(), nullable=False),
            sa.Column("versao", sa.Integer(), nullable=False),
            sa.Column("situacao", sa.String(length=20), nullable=False),
            sa.Column("perda_bp", sa.Integer(), nullable=False),
            sa.Column("sinal_bp", sa.Integer(), nullable=False),
            sa.Column("validade", sa.Date(), nullable=True),
            sa.Column("total", sa.Integer(), nullable=False),
            sa.Column("custo_total", sa.Integer(), nullable=False),
            sa.Column("observacao", sa.Text(), nullable=True),
            sa.Column("enviado_em", sa.DateTime(), nullable=True),
            sa.Column("aprovado_em", sa.DateTime(), nullable=True),
            sa.Column("aprovado_por", sa.String(length=255), nullable=True),
            sa.Column("recusado_motivo", sa.String(length=255), nullable=True),
            sa.Column("criado_em", sa.DateTime(), nullable=False),
            sa.Column("atualizado_em", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["os_id"], ["ordens_servico.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("os_id", "versao", name="uq_fabrica_orcamento_os_versao"),
        )
        op.create_index("ix_fabrica_orcamentos_id", "fabrica_orcamentos", ["id"])
        op.create_index("ix_fabrica_orcamentos_os_id", "fabrica_orcamentos", ["os_id"])

    if not insp.has_table("fabrica_ambientes"):
        op.create_table(
            "fabrica_ambientes",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("orcamento_id", sa.Integer(), nullable=False),
            sa.Column("nome", sa.String(length=60), nullable=False),
            sa.Column("ordem", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["orcamento_id"], ["fabrica_orcamentos.id"], ondelete="CASCADE"),
        )
        op.create_index("ix_fabrica_ambientes_id", "fabrica_ambientes", ["id"])
        op.create_index("ix_fabrica_ambientes_orcamento_id", "fabrica_ambientes", ["orcamento_id"])

    if not insp.has_table("fabrica_moveis"):
        op.create_table(
            "fabrica_moveis",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("ambiente_id", sa.Integer(), nullable=False),
            sa.Column("nome", sa.String(length=120), nullable=False),
            sa.Column("largura_mm", sa.Integer(), nullable=True),
            sa.Column("altura_mm", sa.Integer(), nullable=True),
            sa.Column("profundidade_mm", sa.Integer(), nullable=True),
            sa.Column("preco_venda", sa.Integer(), nullable=False),
            sa.Column("terceirizado", sa.Boolean(), nullable=False),
            sa.Column("custo_terceiro", sa.Integer(), nullable=True),
            sa.Column("ordem", sa.Integer(), nullable=False),
            sa.Column("pedido_compra_id", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(["ambiente_id"], ["fabrica_ambientes.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["pedido_compra_id"], ["pedidos_compra.id"], ondelete="SET NULL"),
        )
        op.create_index("ix_fabrica_moveis_id", "fabrica_moveis", ["id"])
        op.create_index("ix_fabrica_moveis_ambiente_id", "fabrica_moveis", ["ambiente_id"])

    if not insp.has_table("fabrica_materiais"):
        op.create_table(
            "fabrica_materiais",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("movel_id", sa.Integer(), nullable=False),
            sa.Column("produto_id", sa.Integer(), nullable=True),
            sa.Column("descricao", sa.String(length=255), nullable=False),
            sa.Column("consumo", sa.Integer(), nullable=False),
            sa.Column("custo_unitario", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["movel_id"], ["fabrica_moveis.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["produto_id"], ["produtos.id"], ondelete="SET NULL"),
        )
        op.create_index("ix_fabrica_materiais_id", "fabrica_materiais", ["id"])
        op.create_index("ix_fabrica_materiais_movel_id", "fabrica_materiais", ["movel_id"])
        op.create_index("ix_fabrica_materiais_produto_id", "fabrica_materiais", ["produto_id"])


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    for tabela, fabrica in COLUNAS:
        if not insp.has_table(tabela):
            continue
        coluna = fabrica()
        if coluna.name not in {c["name"] for c in insp.get_columns(tabela)}:
            op.add_column(tabela, coluna)
    if insp.has_table("ordens_servico"):
        _criar_tabelas(insp)


def downgrade() -> None:
    for tabela in ("fabrica_materiais", "fabrica_moveis", "fabrica_ambientes", "fabrica_orcamentos"):
        op.drop_table(tabela)
    for tabela, fabrica in reversed(COLUNAS):
        with op.batch_alter_table(tabela) as batch:
            batch.drop_column(fabrica().name)
