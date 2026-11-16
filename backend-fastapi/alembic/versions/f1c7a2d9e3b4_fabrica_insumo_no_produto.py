"""fabrica (F1): o produto como insumo da marcenaria-fábrica

Revision ID: f1c7a2d9e3b4
Revises: e8a3c6d1f702
Create Date: 2026-10-05 10:00:00.000000

CONTEXTO (docs/marcenaria-fabrica-plano.md, F1, D2/D3):
- `produtos.unidade_consumo`     M2 | M | UN, nulo = não é insumo;
- `produtos.consumo_por_unidade` quanto uma unidade de estoque rende, em
  inteiro (mm² por chapa, mm por rolo, unidades por UN);
- `produtos.sofre_perda`         a perda do orçamento entra na quantidade.

MIGRAÇÃO DE DADOS: NENHUMA. Nulos/false = produto comum, como sempre foi.

SEGURANÇA: decide COLUNA A COLUNA pela ausência. O `create_all()` do startup
não acrescenta coluna em tabela que já existe, então aqui é o único caminho
num cliente que atualiza; e rodar de novo não faz nada.
`ADD COLUMN` direto, não `batch_alter_table`: o batch recria a tabela, e
`produtos` é alvo de FK de meio sistema (estoque, venda, OS, compras) — com
PRAGMA foreign_keys=ON o DROP da tabela antiga falha (ver x7y8z9a0b1c2).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f1c7a2d9e3b4'
down_revision: Union[str, Sequence[str], None] = 'e8a3c6d1f702'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


COLUNAS = (
    ("unidade_consumo", lambda: sa.Column("unidade_consumo", sa.String(length=4), nullable=True)),
    ("consumo_por_unidade", lambda: sa.Column("consumo_por_unidade", sa.Integer(), nullable=True)),
    ("sofre_perda", lambda: sa.Column("sofre_perda", sa.Boolean(), nullable=False, server_default="0")),
)


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if not insp.has_table("produtos"):
        return
    existentes = {c["name"] for c in insp.get_columns("produtos")}
    for nome, fabrica in COLUNAS:
        if nome not in existentes:
            op.add_column("produtos", fabrica())


def downgrade() -> None:
    with op.batch_alter_table("produtos") as batch:
        for nome, _ in reversed(COLUNAS):
            batch.drop_column(nome)
