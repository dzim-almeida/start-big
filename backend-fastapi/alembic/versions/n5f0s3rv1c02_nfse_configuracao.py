"""nfse: configuracao da NFS-e (as decisoes do contador viram opcao)

Revision ID: n5f0s3rv1c02
Revises: n5f0s3rv1c01
Create Date: 2026-10-28 15:00:00.000000

CONTEXTO (docs/nfse-fase2-plano.md, G3): retencao de ISS para tomador PJ,
uma NFS-e por codigo nacional na OS, e o IBS/CBS padrao do servico. E
`documento_fiscal.codigo_verificacao` (NFS-e; NULL em toda nota de hoje).

MIGRACAO DE DADOS: NENHUMA. Os booleanos nascem 0 e os codigos NULL -- o
comportamento da fase 1, para quem ja tem a loja configurada.

SEGURANCA (PR8): cada coluna so e criada se AUSENTE; `ALTER TABLE ADD COLUMN`
nativo, sem recriar a tabela.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'n5f0s3rv1c02'
down_revision: Union[str, Sequence[str], None] = 'n5f0s3rv1c01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

COLUNAS = (
    ("empresa_fiscal_settings", "nfse_reter_iss_pj", "BOOLEAN NOT NULL DEFAULT 0"),
    ("empresa_fiscal_settings", "nfse_uma_nota_por_codigo", "BOOLEAN NOT NULL DEFAULT 0"),
    ("empresa_fiscal_settings", "nfse_ibs_cbs_cst", "VARCHAR(3)"),
    ("empresa_fiscal_settings", "nfse_ibs_cbs_cclass", "VARCHAR(6)"),
    # O codigo de verificacao da NFS-e por DOCUMENTO: com uma nota por codigo,
    # a mesma OS tem duas NFS-e, e o espelho da OS so guarda uma.
    ("documento_fiscal", "codigo_verificacao", "VARCHAR(50)"),
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
