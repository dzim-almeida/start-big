"""linha da venda e do orçamento guarda a embalagem vendida

Revision ID: f3a8d15c6b92
Revises: e7b2c9d41f60
Create Date: 2026-09-27 20:00:00.000000

CONTEXTO (docs/produto-embalagens-plano.md, fase 3):
O caixa vende "2 FD" de 12. A linha congela a embalagem, o fator e a sigla
(D6); o estoque baixa `quantidade × fator_embalagem`. E o produto ganha
`so_embalagem_fechada` (A3): o caixa recusa a unidade avulsa.

MIGRAÇÃO DE DADOS: NENHUMA. `fator_embalagem` nasce 1 (DEFAULT da coluna,
preenchido pelo próprio SQLite nas linhas existentes): toda linha antiga
continua significando exatamente "N unidades". `so_embalagem_fechada` nasce 0.

SEGURANÇA:
- Decide pela ausência de CADA coluna (o create_all() não altera tabela que
  já existe, então numa base antiga elas faltam; numa nova, já vêm criadas).
- A FK vai inline no ADD COLUMN: o SQLite não tem ADD CONSTRAINT.
- NOT NULL com DEFAULT é aceito pelo ADD COLUMN do SQLite.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f3a8d15c6b92'
down_revision: Union[str, Sequence[str], None] = 'e7b2c9d41f60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


COLUNAS_DA_LINHA = {
    "embalagem_id": "INTEGER REFERENCES produto_embalagens (id) ON DELETE SET NULL",
    "fator_embalagem": "INTEGER NOT NULL DEFAULT 1",
    "sigla_embalagem": "VARCHAR(6)",
}

COLUNAS = {
    "produtos_venda": COLUNAS_DA_LINHA,
    "orcamentos_produtos": COLUNAS_DA_LINHA,
    "produtos": {"so_embalagem_fechada": "BOOLEAN NOT NULL DEFAULT 0"},
}


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
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
