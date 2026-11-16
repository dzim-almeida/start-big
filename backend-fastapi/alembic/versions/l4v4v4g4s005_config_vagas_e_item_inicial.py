"""configuracoes_os.vagas_agenda + configuracoes_os.item_os_abre_em

Revision ID: l4v4v4g4s005
Revises: l4v4dur4c004
Create Date: 2026-11-14 10:00:00.000000

CONTEXTO (14/11/2026):
- vagas_agenda: SPEC-00 O11 do lava-rapido -- a agenda avisa, sem travar,
  quando um horario passa do numero de boxes/vagas da loja. 0 = sem limite.
- item_os_abre_em: em qual aba ("SERVICO" ou "PRODUTO") o "Adicionar Item"
  da OS abre. Loja que vende mais produto quer a de produto primeiro.
  Padrao "SERVICO" = o comportamento de sempre.

MIGRACAO DE DADOS: NENHUMA. As duas colunas sao NOT NULL com server_default
igual ao comportamento atual: as linhas existentes ficam como estavam.

SEGURANCA: decide pela presenca de CADA coluna (o create_all() do startup
roda antes e, num banco novo, a tabela ja chega com elas). Nenhuma outra
coluna e alterada.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'l4v4v4g4s005'
down_revision: Union[str, Sequence[str], None] = 'l4v4dur4c004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABELA = "configuracoes_os"
COLUNAS = {
    "vagas_agenda": lambda: sa.Column("vagas_agenda", sa.Integer(), nullable=False, server_default="0"),
    "item_os_abre_em": lambda: sa.Column(
        "item_os_abre_em", sa.String(10), nullable=False, server_default="SERVICO"),
}


def _colunas_existentes() -> set[str]:
    insp = sa.inspect(op.get_bind())
    if not insp.has_table(TABELA):
        return set()
    return {c["name"] for c in insp.get_columns(TABELA)}


def upgrade() -> None:
    existentes = _colunas_existentes()
    if not existentes:
        return  # tabela ainda nao existe (create_all cuida)
    for nome, coluna in COLUNAS.items():
        if nome not in existentes:
            op.add_column(TABELA, coluna())


def downgrade() -> None:
    existentes = _colunas_existentes()
    remover = [nome for nome in COLUNAS if nome in existentes]
    if remover:
        with op.batch_alter_table(TABELA) as batch:
            for nome in remover:
                batch.drop_column(nome)
