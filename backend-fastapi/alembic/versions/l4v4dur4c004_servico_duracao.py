"""servicos.duracao_minutos (lava-rapido: previsao no patio)

Revision ID: l4v4dur4c004
Revises: l4v4ag3nd003
Create Date: 2026-11-13 22:00:00.000000

CONTEXTO: a grade de preco por porte saiu do cadastro de servico (13/11/2026)
e levou junto a unica duracao que existia. O patio ("Pronto as 10:40") e o
agendamento precisam dela: volta como um campo simples do servico.

MIGRACAO DE DADOS: NENHUMA. Coluna opcional, nasce NULL nas linhas existentes.

SEGURANCA: decide pela presenca da COLUNA (o create_all() do startup roda
antes e, num banco novo, a tabela ja chega com ela). Nenhuma outra coluna e
alterada.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'l4v4dur4c004'
down_revision: Union[str, Sequence[str], None] = 'l4v4ag3nd003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABELA = "servicos"
COLUNA = "duracao_minutos"


def _colunas_existentes() -> set[str]:
    insp = sa.inspect(op.get_bind())
    if not insp.has_table(TABELA):
        return set()
    return {c["name"] for c in insp.get_columns(TABELA)}


def upgrade() -> None:
    existentes = _colunas_existentes()
    if not existentes or COLUNA in existentes:
        return  # tabela ainda nao existe (create_all cuida) ou coluna ja criada
    op.add_column(TABELA, sa.Column(COLUNA, sa.Integer(), nullable=True))


def downgrade() -> None:
    if COLUNA in _colunas_existentes():
        with op.batch_alter_table(TABELA) as batch:
            batch.drop_column(COLUNA)
