"""marcenaria (Spec 11A): moveis terceirizados (pedido a central parceira)

Revision ID: 642b2e8f79fa
Revises: 195109da93f7
Create Date: 2026-10-09 23:00:00.000000

CONTEXTO (backend-fastapi/docs/marcenaria/SPEC-11A-TERCEIRIZADOS-BACKEND-MARCENARIA.md):
- `marcenaria_moveis.pedido_compra_id`: o pedido de SERVICO do Compras que
  pediu o movel a central (D9, D11).
- `terc_situacao`, `terc_pedido`, `terc_enviado_em`, `terc_previsao`,
  `terc_recebido_em`: o acompanhamento A MAO, para a loja sem o modulo
  Compras (D3).
- `terc_conferido_em`, `terc_problema`: conferencia e problema, nos dois
  modos (D2, D4).

MIGRACAO DE DADOS: NENHUMA. Tudo nasce nulo (nulo = "A pedir").

SEGURANCA (PR8): so a tabela `marcenaria_moveis` (da marcenaria) muda; cada
coluna e cada indice so sao criados se FALTAREM (o create_all do startup ja
cria a tabela com eles numa instalacao nova); `ADD COLUMN` direto, sem
`batch_alter_table`. Nenhuma tabela compartilhada e alterada.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '642b2e8f79fa'
down_revision: Union[str, Sequence[str], None] = '195109da93f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABELA = "marcenaria_moveis"

# (coluna, como criar) -- escritas aqui de proposito (foto de hoje).
COLUNAS = (
    ("pedido_compra_id", "INTEGER REFERENCES pedidos_compra(id) ON DELETE SET NULL"),
    ("terc_situacao", "VARCHAR(10)"),
    ("terc_pedido", "VARCHAR(60)"),
    ("terc_enviado_em", "DATE"),
    ("terc_previsao", "DATE"),
    ("terc_recebido_em", "DATE"),
    ("terc_conferido_em", "DATE"),
    ("terc_problema", "VARCHAR(500)"),
)

# (nome, colunas) dos indices novos.
INDICES = (
    ("ix_marcenaria_moveis_pedido", ("pedido_compra_id",)),
    ("ix_marcenaria_moveis_terc", ("terc_situacao", "terc_previsao")),
)


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())                      # o que o banco tem AGORA
    if not insp.has_table(TABELA):
        return                                            # loja sem a marcenaria ainda: o create_all cria
    existentes = {c["name"] for c in insp.get_columns(TABELA)}
    for coluna, tipo in COLUNAS:
        if coluna not in existentes:                      # so cria o que falta
            op.execute(f"ALTER TABLE {TABELA} ADD COLUMN {coluna} {tipo}")
    indices = {i["name"] for i in insp.get_indexes(TABELA)}
    for nome, colunas in INDICES:
        if nome not in indices:
            op.create_index(nome, TABELA, list(colunas))


def downgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if not insp.has_table(TABELA):
        return
    indices = {i["name"] for i in insp.get_indexes(TABELA)}
    for nome, _colunas in INDICES:
        if nome in indices:
            op.drop_index(nome, table_name=TABELA)
    existentes = {c["name"] for c in insp.get_columns(TABELA)}
    with op.batch_alter_table(TABELA) as batch:           # no SQLite, tirar coluna so pelo batch
        for coluna, _tipo in COLUNAS:
            if coluna in existentes:
                batch.drop_column(coluna)
