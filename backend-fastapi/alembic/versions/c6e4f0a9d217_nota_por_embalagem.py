"""snapshot da nota guarda o fator da embalagem

Revision ID: c6e4f0a9d217
Revises: f3a8d15c6b92
Create Date: 2026-09-27 21:00:00.000000

CONTEXTO (docs/produto-embalagens-plano.md, fase 4):
A linha "2 FD de 12" vai na nota com uCom = FD/qCom = 2 e uTrib = UN/qTrib = 24.
O snapshot (`documento_fiscal_item`) congela o fator e a unidade/GTIN
tributáveis: é o que faz a devolução de 1 FD voltar 12 un ao estoque e sair com
a mesma unidade tributável da nota original.

MIGRAÇÃO DE DADOS: NENHUMA. `fator_embalagem` nasce 1 (DEFAULT da coluna,
preenchido pelo SQLite nas linhas existentes): todo item de nota antigo continua
significando "N unidades". Os tributáveis nascem nulos.

SEGURANÇA: decide pela ausência de CADA coluna (ver f3a8d15c6b92).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c6e4f0a9d217'
down_revision: Union[str, Sequence[str], None] = 'f3a8d15c6b92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABELA = "documento_fiscal_item"
COLUNAS = {
    "fator_embalagem": "INTEGER NOT NULL DEFAULT 1",
    "unidade_tributavel": "VARCHAR(6)",
    "codigo_barras_tributavel": "VARCHAR(20)",
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
