"""venda no atacado: chave e pedido mínimo nas configurações, modo na venda

Revision ID: e3b7c1a9f205
Revises: d7a3e9c2f418
Create Date: 2026-10-10 20:00:00.000000

CONTEXTO: o produto já tinha `estoque.valor_atacado`, mas o PDV nunca o usava.
- `configuracoes_vendas.atacado_habilitado`: mostra a chave "Atacado" no PDV.
- `configuracoes_vendas.atacado_pedido_minimo`: abaixo dele a venda em
  atacado não finaliza (centavos; 0 = sem mínimo).
- `vendas.modo_atacado`: a venda está no preço de atacado. A linha marcada
  usa as colunas que já existem (`regra_preco = 'ATACADO'`, preço de varejo em
  `valor_unitario_tabela`) — nenhuma coluna nova em `produtos_venda`.

MIGRAÇÃO DE DADOS: NENHUMA. Tudo nasce desligado/0: nenhuma venda antiga muda
de valor e quem não liga a chave vende exatamente como antes.

SEGURANÇA: decide pela ausência de CADA coluna (o create_all/reconciliação
pode já tê-la criado). NOT NULL com DEFAULT é aceito pelo ADD COLUMN do SQLite.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e3b7c1a9f205'
down_revision: Union[str, Sequence[str], None] = 'd7a3e9c2f418'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


COLUNAS = {
    "configuracoes_vendas": {
        "atacado_habilitado": "BOOLEAN NOT NULL DEFAULT 0",
        "atacado_pedido_minimo": "INTEGER NOT NULL DEFAULT 0",
    },
    "vendas": {"modo_atacado": "BOOLEAN NOT NULL DEFAULT 0"},
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
