"""marcenaria (Spec 09A): conta a pagar do RT do arquiteto

Revision ID: 195109da93f7
Revises: 971eb6cc5a33
Create Date: 2026-10-09 21:00:00.000000

CONTEXTO (backend-fastapi/docs/marcenaria/SPEC-09A-RT-ARQUITETO-BACKEND-MARCENARIA.md):
- `marcenaria_orcamento_rt.conta_pagar_id`: a conta ATUAL do RT de cada
  arquiteto, criada na finalizacao da OS (D11).
- `configuracoes_marcenaria.rt_vencimento_dias` (padrao 30) e
  `rt_plano_conta_id` (a categoria "Comissao de arquitetos (RT)", D5/D6).

MIGRACAO DE DADOS: NENHUMA. As colunas nascem nulas, salvo
`rt_vencimento_dias`, que nasce com 30 (o padrao aprovado, C5e).

SEGURANCA (PR8): cada coluna so e criada se FALTAR (o create_all do startup ja
cria as tabelas da marcenaria com elas numa instalacao nova); `ADD COLUMN`
direto, sem `batch_alter_table`. Nenhuma tabela fora da marcenaria e alterada.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '195109da93f7'
down_revision: Union[str, Sequence[str], None] = '971eb6cc5a33'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (tabela, coluna, como criar) -- escritas aqui de proposito (foto de hoje).
COLUNAS = (
    ("marcenaria_orcamento_rt", "conta_pagar_id", "INTEGER REFERENCES contas_pagar(id)"),
    ("configuracoes_marcenaria", "rt_vencimento_dias", "INTEGER NOT NULL DEFAULT 30"),
    ("configuracoes_marcenaria", "rt_plano_conta_id", "INTEGER REFERENCES planos_conta(id) ON DELETE SET NULL"),
)


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())                      # o que o banco tem AGORA
    for tabela, coluna, tipo in COLUNAS:
        if not insp.has_table(tabela):
            continue
        if coluna not in {c["name"] for c in insp.get_columns(tabela)}:   # so cria o que falta
            op.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo}")


def downgrade() -> None:
    insp = sa.inspect(op.get_bind())
    por_tabela: dict[str, list[str]] = {}
    for tabela, coluna, _tipo in COLUNAS:
        por_tabela.setdefault(tabela, []).append(coluna)
    for tabela, colunas in por_tabela.items():
        if not insp.has_table(tabela):
            continue
        existentes = {c["name"] for c in insp.get_columns(tabela)}
        with op.batch_alter_table(tabela) as batch:       # no SQLite, tirar coluna so pelo batch
            for coluna in colunas:
                if coluna in existentes:
                    batch.drop_column(coluna)
