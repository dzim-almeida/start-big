"""marcenaria: faturamento dos moveis -- configuracao, produto acabado do movel e o caminho movel -> nota

Revision ID: f4t1m0v3l001
Revises: a7d1t1v0os01
Create Date: 2026-10-24 20:00:00.000000

CONTEXTO (docs/marcenaria-faturamento-plano.md, F1): o movel pronto entra no
estoque como PRODUTO ACABADO e e ele que sai na NF-e.
- `configuracoes_marcenaria` ganha o modo de faturamento, o modo da
  instalacao e os dois produtos acabados (producao propria e revenda);
- `marcenaria_moveis.produto_acabado_id`: o "tipo fiscal" do movel (D3);
- tabela nova `marcenaria_moveis_faturamento`: uma linha por movel (D1).

MIGRACAO DE DADOS: NENHUMA. Toda configuracao que ja existe fica
`DESLIGADO` / `EMBUTIDA` (o comportamento de hoje) e todo movel fica NULL.

SEGURANCA (PR8):
- Cada coluna so e criada se AUSENTE, e a tabela so se AUSENTE: o
  create_all() do startup ja cria a tabela nova (e as colunas, num banco
  novo), mas NAO acrescenta coluna em tabela que ja existe.
- Sem batch_alter_table no upgrade: `ALTER TABLE ADD COLUMN ... REFERENCES`
  e nativo no SQLite e nao recria a tabela.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f4t1m0v3l001'
down_revision: Union[str, Sequence[str], None] = 'a7d1t1v0os01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CONFIG = "configuracoes_marcenaria"
MOVEIS = "marcenaria_moveis"
FATURAMENTO = "marcenaria_moveis_faturamento"

# (tabela, coluna, DDL do ADD COLUMN)
COLUNAS = (
    (CONFIG, "faturamento_modo", "VARCHAR(20) NOT NULL DEFAULT 'DESLIGADO'"),
    (CONFIG, "instalacao_modo", "VARCHAR(10) NOT NULL DEFAULT 'EMBUTIDA'"),
    (CONFIG, "produto_acabado_padrao_id", "INTEGER REFERENCES produtos (id) ON DELETE SET NULL"),
    (CONFIG, "produto_acabado_revenda_id", "INTEGER REFERENCES produtos (id) ON DELETE SET NULL"),
    (MOVEIS, "produto_acabado_id", "INTEGER REFERENCES produtos (id) ON DELETE SET NULL"),
)


def _tem_coluna(insp, tabela: str, coluna: str) -> bool:
    return any(c["name"] == coluna for c in insp.get_columns(tabela))


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    for tabela, coluna, ddl in COLUNAS:
        if insp.has_table(tabela) and not _tem_coluna(insp, tabela, coluna):
            op.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {ddl}")

    insp = sa.inspect(op.get_bind())
    if insp.has_table(MOVEIS) and not insp.has_table(FATURAMENTO):
        op.create_table(
            FATURAMENTO,
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("os_id", sa.Integer(), sa.ForeignKey("ordens_servico.id"), nullable=False),
            sa.Column("movel_id", sa.Integer(), sa.ForeignKey("marcenaria_moveis.id", ondelete="CASCADE"),
                      nullable=False, unique=True),
            sa.Column("produto_id", sa.Integer(), sa.ForeignKey("produtos.id"), nullable=False),
            sa.Column("quantidade", sa.Float(), nullable=False),
            sa.Column("custo_unitario_centavos", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("mov_entrada_id", sa.Integer(),
                      sa.ForeignKey("movimentacoes_estoque.id", ondelete="SET NULL"), nullable=True),
            sa.Column("mov_saida_id", sa.Integer(),
                      sa.ForeignKey("movimentacoes_estoque.id", ondelete="SET NULL"), nullable=True),
            sa.Column("documento_fiscal_id", sa.Integer(),
                      sa.ForeignKey("documento_fiscal.id", ondelete="SET NULL"), nullable=True),
            sa.Column("documento_simples_faturamento_id", sa.Integer(),
                      sa.ForeignKey("documento_fiscal.id", ondelete="SET NULL"), nullable=True),
            sa.Column("situacao", sa.String(12), nullable=False, server_default="NO_ESTOQUE"),
            sa.Column("criado_em", sa.DateTime(), nullable=False),
            sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_marcenaria_moveis_faturamento_os", FATURAMENTO, ["os_id"])
        op.create_index("ix_marcenaria_moveis_faturamento_doc", FATURAMENTO, ["documento_fiscal_id"])


def downgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if insp.has_table(FATURAMENTO):
        op.drop_table(FATURAMENTO)
    for tabela, coluna, _ddl in reversed(COLUNAS):
        insp = sa.inspect(op.get_bind())
        if insp.has_table(tabela) and _tem_coluna(insp, tabela, coluna):
            with op.batch_alter_table(tabela) as batch_op:
                batch_op.drop_column(coluna)
