"""marcenaria (remodelacao item 20): aditivo do orcamento numa OS existente

Revision ID: a7d1t1v0os01
Revises: 2c4df92b1412
Create Date: 2026-10-14 01:30:00.000000

CONTEXTO: o ADITIVO e um orcamento de moveis a mais para uma OS que ja
existe. A coluna `marcenaria_orcamentos.aditivo_os_id` diz de qual OS ele e;
ao aprovar, os itens somam nessa OS (em vez de criar outra).

MIGRACAO DE DADOS: NENHUMA. Todo orcamento que ja existe e comum (NULL).

SEGURANCA (PR8):
- A coluna so e criada se AUSENTE: o create_all() do startup ja a cria num
  banco novo, mas NAO acrescenta coluna em tabela que ja existe -- e para
  isto que esta migracao existe.
- Sem batch_alter_table no upgrade: recriar a tabela com PRAGMA
  foreign_keys=ON quebraria as FKs que apontam para ela. `ALTER TABLE ADD
  COLUMN ... REFERENCES` e nativo no SQLite.
- Nasce NULL em todas as linhas: nenhum orcamento vira aditivo por acidente.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a7d1t1v0os01'
down_revision: Union[str, Sequence[str], None] = '2c4df92b1412'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABELA = "marcenaria_orcamentos"
COLUNA = "aditivo_os_id"
INDICE = "ix_marcenaria_orcamentos_aditivo_os"


def _tem_coluna(insp) -> bool:
    return any(c["name"] == COLUNA for c in insp.get_columns(TABELA))


def _tem_indice(insp) -> bool:
    return any(i["name"] == INDICE for i in insp.get_indexes(TABELA))


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if not insp.has_table(TABELA):
        return                                            # banco sem marcenaria ainda: o create_all cria completo
    if not _tem_coluna(insp):
        # FK inline no ADD COLUMN: `op.add_column` com ForeignKey tenta um
        # ADD CONSTRAINT separado, que o SQLite nao tem.
        op.execute(f"ALTER TABLE {TABELA} ADD COLUMN {COLUNA} INTEGER REFERENCES ordens_servico (id)")
    if not _tem_indice(sa.inspect(op.get_bind())):
        op.create_index(INDICE, TABELA, [COLUNA])


def downgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if _tem_indice(insp):
        op.drop_index(INDICE, table_name=TABELA)
    if _tem_coluna(insp):
        with op.batch_alter_table(TABELA) as batch_op:
            batch_op.drop_column(COLUNA)
