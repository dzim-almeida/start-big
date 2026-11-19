"""ultimo horario visto na licenca (LIC-02, relogio que voltou no tempo)

Acrescenta `configuracoes_licenca.ultimo_horario_visto` (DateTime, NULL).

Guarda o MAIOR horario ja visto pela instalacao. Se o relogio do computador
recuar, a validacao offline usa este horario e avisa o dono (ACORDO D-05).

MIGRACAO DE DADOS: NENHUMA. A coluna nasce NULA: "ainda nao registrado". O
primeiro uso so grava o horario, sem aviso.

SEGURANCA: decide pela presenca da coluna na tabela que JA EXISTE (schema
antigo). O create_all() do startup roda antes das migracoes, mas ele nao
acrescenta coluna em tabela existente: num banco antigo a coluna falta e a
migracao a cria; num banco novo a tabela ja nasce com ela e nada acontece.
Rodar de novo nao faz nada (idempotente).

Revision ID: l1c02r3l0g10
Revises: l4v4v4g4s005
Create Date: 2026-11-19 18:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'l1c02r3l0g10'
down_revision: Union[str, Sequence[str], None] = 'l4v4v4g4s005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABELA = 'configuracoes_licenca'
COLUNA = 'ultimo_horario_visto'


def _colunas_existentes() -> set[str] | None:
    """Colunas da tabela da licenca, ou None se a tabela ainda nao existe."""
    inspetor = sa.inspect(op.get_bind())   # "olha" o banco real sem mudar nada
    if TABELA not in inspetor.get_table_names():
        return None
    return {c['name'] for c in inspetor.get_columns(TABELA)}


def upgrade() -> None:
    colunas = _colunas_existentes()
    if colunas is None or COLUNA in colunas:
        return   # sem tabela, ou ja tem a coluna: nada a fazer
    op.add_column(TABELA, sa.Column(COLUNA, sa.DateTime(), nullable=True))


def downgrade() -> None:
    colunas = _colunas_existentes()
    if colunas is None or COLUNA not in colunas:
        return
    # batch: o SQLite nao sabe apagar coluna direto; o Alembic recria a tabela.
    with op.batch_alter_table(TABELA) as batch_op:
        batch_op.drop_column(COLUNA)
