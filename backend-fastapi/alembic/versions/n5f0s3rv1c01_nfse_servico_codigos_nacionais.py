"""nfse: codigo de tributacao nacional e NBS no cadastro fiscal do servico

Revision ID: n5f0s3rv1c01
Revises: f4t1m0v3l002
Create Date: 2026-10-28 10:00:00.000000

CONTEXTO (docs/nfse-plano.md, F1): a NFS-e Nacional pede, por servico, o
codigo de tributacao nacional (6 digitos: item + subitem + desdobro da LC 116)
e o NBS (9 digitos). O `codigo_servico_lc116` que ja existe tem 4 digitos e nao
traz o desdobro.

MIGRACAO DE DADOS: NENHUMA. Os campos nascem NULL; a tela sugere o codigo
nacional e o NBS a partir das tabelas oficiais embarcadas.

SEGURANCA (PR8): cada coluna so e criada se AUSENTE; `ALTER TABLE ADD COLUMN`
nativo, sem recriar a tabela.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'n5f0s3rv1c01'
down_revision: Union[str, Sequence[str], None] = 'f4t1m0v3l002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

COLUNAS = (
    ("servico_fiscal", "codigo_tributacao_nacional", "VARCHAR(6)"),
    ("servico_fiscal", "codigo_nbs", "VARCHAR(9)"),
)


def _tem_coluna(insp, tabela: str, coluna: str) -> bool:
    return any(c["name"] == coluna for c in insp.get_columns(tabela))


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    for tabela, coluna, ddl in COLUNAS:
        if insp.has_table(tabela) and not _tem_coluna(insp, tabela, coluna):
            op.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {ddl}")


def downgrade() -> None:
    for tabela, coluna, _ddl in reversed(COLUNAS):
        insp = sa.inspect(op.get_bind())
        if insp.has_table(tabela) and _tem_coluna(insp, tabela, coluna):
            with op.batch_alter_table(tabela) as batch_op:
                batch_op.drop_column(coluna)
