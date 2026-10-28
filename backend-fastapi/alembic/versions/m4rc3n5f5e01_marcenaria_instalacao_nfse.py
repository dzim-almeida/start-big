"""marcenaria: instalacao em NFS-e -- o servico da instalacao

Revision ID: m4rc3n5f5e01
Revises: n5f0s3rv1c02
Create Date: 2026-10-28 16:00:00.000000

CONTEXTO (docs/nfse-fase2-plano.md, G5): o terceiro modo da instalacao
(`instalacao_modo = NFSE`) emite uma NFS-e da instalacao por OS, com o codigo
nacional/NBS do servico escolhido aqui. NFSE e so um valor novo na coluna
String(10) que ja existe -- sem migration para ele.

MIGRACAO DE DADOS: NENHUMA. A coluna nasce NULL e o modo de toda loja continua
o que era (EMBUTIDA ou FORA).

SEGURANCA (PR8): so cria se AUSENTE; `ALTER TABLE ADD COLUMN` nativo.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'm4rc3n5f5e01'
down_revision: Union[str, Sequence[str], None] = 'n5f0s3rv1c02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABELA = "configuracoes_marcenaria"
COLUNA = "servico_instalacao_id"


def _tem_coluna(insp) -> bool:
    return any(c["name"] == COLUNA for c in insp.get_columns(TABELA))


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if insp.has_table(TABELA) and not _tem_coluna(insp):
        op.execute(f"ALTER TABLE {TABELA} ADD COLUMN {COLUNA} INTEGER REFERENCES servicos (id) ON DELETE SET NULL")


def downgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if insp.has_table(TABELA) and _tem_coluna(insp):
        with op.batch_alter_table(TABELA) as batch_op:
            batch_op.drop_column(COLUNA)
