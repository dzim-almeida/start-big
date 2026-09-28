"""regras de preço por quantidade (R1 fardo nas avulsas, R2 faixas, R3 leve-pague)

Revision ID: d2f8b61e9a47
Revises: c6e4f0a9d217
Create Date: 2026-09-28 10:00:00.000000

CONTEXTO (docs/produto-embalagens-plano.md, §6.1, fase 5):
- `produto_regras_preco`: faixas "a partir de N" (R2) e "leve X pague Y" (R3).
- `produto_embalagens.aplica_as_avulsas`: a R1 é da embalagem.
- `produtos_venda`: a linha congela a regra aplicada. R1/R3 entram em
  `desconto_regra`, SEPARADO do `desconto` do operador (o rateio e o limite de
  desconto mexem nele); R2 muda o preço e guarda o cheio em
  `valor_unitario_tabela`.
- `configuracoes_vendas`: as chaves de cada regra, o critério de conflito e a
  trava de desconto manual.

MIGRAÇÃO DE DADOS: NENHUMA. Toda chave nasce DESLIGADA, `desconto_regra` nasce
0 e o resto nulo: nenhuma venda antiga muda de valor, e quem não liga nada
vende exatamente como antes (B8).

SEGURANÇA:
- Tabela: decide pela ausência da TABELA (o create_all() pode já tê-la criado).
- Colunas: decide pela ausência de CADA coluna.
- NOT NULL com DEFAULT é aceito pelo ADD COLUMN do SQLite.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd2f8b61e9a47'
down_revision: Union[str, Sequence[str], None] = 'c6e4f0a9d217'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABELA = "produto_regras_preco"

COLUNAS = {
    "produto_embalagens": {"aplica_as_avulsas": "BOOLEAN NOT NULL DEFAULT 0"},
    "produtos_venda": {
        "desconto_regra": "INTEGER NOT NULL DEFAULT 0",
        "regra_preco": "VARCHAR(12)",
        "regra_descricao": "VARCHAR(80)",
        "valor_unitario_tabela": "INTEGER",
    },
    "configuracoes_vendas": {
        "regra_embalagem_avulsas": "BOOLEAN NOT NULL DEFAULT 0",
        "regra_faixas_quantidade": "BOOLEAN NOT NULL DEFAULT 0",
        "regra_leve_pague": "BOOLEAN NOT NULL DEFAULT 0",
        "regra_conflito": "VARCHAR(12) NOT NULL DEFAULT 'MENOR_PRECO'",
        "regra_ordem": "VARCHAR(20) NOT NULL DEFAULT 'R1,R2,R3'",
        "bloquear_desconto_com_regra": "BOOLEAN NOT NULL DEFAULT 0",
    },
}


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())

    if not insp.has_table(TABELA):
        op.create_table(
            TABELA,
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("produto_id", sa.Integer(), nullable=False),
            sa.Column("tipo", sa.String(length=12), nullable=False),
            sa.Column("quantidade", sa.Integer(), nullable=False),
            sa.Column("preco", sa.Integer(), nullable=True),
            sa.Column("pague", sa.Integer(), nullable=True),
            sa.Column("inicio", sa.Date(), nullable=True),
            sa.Column("fim", sa.Date(), nullable=True),
            sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("1")),
            sa.Column("data_criacao", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("data_atualizacao", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["produto_id"], ["produtos.id"], ondelete="CASCADE"),
        )
        op.create_index(f"ix_{TABELA}_id", TABELA, ["id"])
        op.create_index(f"ix_{TABELA}_produto_id", TABELA, ["produto_id"])

    for tabela, colunas in COLUNAS.items():
        if not insp.has_table(tabela):
            continue
        existentes = {c["name"] for c in insp.get_columns(tabela)}
        for coluna, tipo in colunas.items():
            if coluna not in existentes:
                op.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo}")


def downgrade() -> None:
    for tabela, colunas in COLUNAS.items():
        with op.batch_alter_table(tabela) as batch_op:
            for coluna in reversed(list(colunas)):
                batch_op.drop_column(coluna)
    op.drop_index(f"ix_{TABELA}_produto_id", table_name=TABELA)
    op.drop_index(f"ix_{TABELA}_id", table_name=TABELA)
    op.drop_table(TABELA)
