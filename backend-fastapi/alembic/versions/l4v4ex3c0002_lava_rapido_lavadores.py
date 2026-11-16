"""lava-rapido (Spec 10A): executores da OS (lavadores) e divisao da comissao

Revision ID: l4v4ex3c0002
Revises: l4v4p0r7e001
Create Date: 2026-11-12 20:00:00.000000

CONTEXTO (backend-fastapi/docs/lava-rapido/SPEC-10A-LAVADORES-BACKEND-LAVA-RAPIDO.md):
- `ordem_servico_executores`: quem executa a OS alem do responsavel (O7a).
- `cargos.comissao_divisao` e `funcionarios.comissao_divisao`: 'dividir' |
  'inteira' quando a OS tem mais de um executor (O7c), em cascata
  funcionario -> cargo -> padrao 'dividir', como o `comissao_modo`.

MIGRACAO DE DADOS: NENHUMA. A tabela nasce vazia (OS sem executor = regra de
sempre) e as colunas nascem NULL (= padrao).

SEGURANCA (PR8):
- Decide pela ausencia da TABELA e de CADA coluna; o create_all() do startup
  costuma criar antes.
- Colunas: `ADD COLUMN` nullable, nativo do SQLite -- nao recria `cargos` nem
  `funcionarios`, nenhuma linha e tocada.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'l4v4ex3c0002'
down_revision: Union[str, Sequence[str], None] = 'l4v4p0r7e001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABELA = "ordem_servico_executores"
COLUNA = "comissao_divisao"
TABELAS_COLUNA = ("cargos", "funcionarios")


def _tem_coluna(insp, tabela: str, coluna: str) -> bool:
    return any(c["name"] == coluna for c in insp.get_columns(tabela))


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())

    if not insp.has_table(TABELA):
        op.create_table(
            TABELA,
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("ordem_servico_id", sa.Integer(), nullable=False),
            sa.Column("funcionario_id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["ordem_servico_id"], ["ordens_servico.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["funcionario_id"], ["funcionarios.id"]),
            sa.UniqueConstraint("ordem_servico_id", "funcionario_id", name="uq_os_executor"),
        )
        op.create_index(f"ix_{TABELA}_id", TABELA, ["id"])
        op.create_index(f"ix_{TABELA}_ordem_servico_id", TABELA, ["ordem_servico_id"])
        op.create_index(f"ix_{TABELA}_funcionario_id", TABELA, ["funcionario_id"])

    for tabela in TABELAS_COLUNA:
        if insp.has_table(tabela) and not _tem_coluna(insp, tabela, COLUNA):
            op.execute(f"ALTER TABLE {tabela} ADD COLUMN {COLUNA} VARCHAR(10)")


def downgrade() -> None:
    insp = sa.inspect(op.get_bind())
    for tabela in TABELAS_COLUNA:
        if insp.has_table(tabela) and _tem_coluna(insp, tabela, COLUNA):
            with op.batch_alter_table(tabela) as batch_op:
                batch_op.drop_column(COLUNA)
    if insp.has_table(TABELA):
        op.drop_table(TABELA)
