"""nfse: padrao fiscal da loja para servicos novos

Revision ID: n5f0m2padr01
Revises: m4rc3n5f5e01
Create Date: 2026-10-29 15:00:00.000000

CONTEXTO (docs/nfse-melhorias-plano.md, M2; decisao do Alan em 29/10/2026):
"um padrao da loja + copiar de outro servico". Servico novo nasce com o
codigo nacional, o NBS e a aliquota de ISS que a loja usa mais, e a pessoa
so troca o que muda.

MIGRACAO DE DADOS: NENHUMA. As colunas nascem NULL -- sem padrao, o cadastro
do servico fica exatamente como hoje.

SEGURANCA (PR8): cada coluna so e criada se AUSENTE; `ALTER TABLE ADD COLUMN`
nativo, sem recriar a tabela.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'n5f0m2padr01'
down_revision: Union[str, Sequence[str], None] = 'm4rc3n5f5e01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

COLUNAS = (
    ("empresa_fiscal_settings", "nfse_padrao_codigo_nacional", "VARCHAR(6)"),
    ("empresa_fiscal_settings", "nfse_padrao_nbs", "VARCHAR(9)"),
    ("empresa_fiscal_settings", "nfse_padrao_aliquota_iss", "INTEGER"),
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
