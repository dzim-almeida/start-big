"""movimentação de estoque guarda a embalagem da entrada

Revision ID: e7b2c9d41f60
Revises: a0b1c2d3e4f5
Create Date: 2026-09-27 17:00:00.000000

CONTEXTO (docs/produto-embalagens-plano.md, fase 2):
Entrada por embalagem ("3 CX de 24"). A quantidade e o custo da movimentação
continuam na UNIDADE (72 un a R$ 5,00); estas colunas só registram como a
mercadoria entrou, congelando sigla e fator.

MIGRAÇÃO DE DADOS: NENHUMA. As colunas nascem nulas: toda movimentação antiga
continua significando "em unidade", como sempre foi.

SEGURANÇA:
- Decide pela ausência de CADA coluna (o create_all() não altera tabela que
  já existe, então numa base antiga elas faltam; numa nova, já vêm criadas).
- A FK vai inline no ADD COLUMN: o SQLite não tem ADD CONSTRAINT.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e7b2c9d41f60'
down_revision: Union[str, Sequence[str], None] = 'a0b1c2d3e4f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABELA = "movimentacoes_estoque"
COLUNAS = {
    "embalagem_id": "INTEGER REFERENCES produto_embalagens (id) ON DELETE SET NULL",
    "embalagem_sigla": "VARCHAR(6)",
    "embalagem_fator": "INTEGER",
    "quantidade_embalagem": "INTEGER",
}


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if not insp.has_table(TABELA):
        return
    existentes = {c["name"] for c in insp.get_columns(TABELA)}
    for coluna, tipo in COLUNAS.items():
        if coluna not in existentes:
            op.execute(f"ALTER TABLE {TABELA} ADD COLUMN {coluna} {tipo}")


def downgrade() -> None:
    with op.batch_alter_table(TABELA) as batch_op:
        for coluna in reversed(list(COLUNAS)):
            batch_op.drop_column(coluna)
