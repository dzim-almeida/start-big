"""marcenaria (Spec 13A): entrega por ambiente, pendencias, fotos e agendamentos

Revision ID: 2c4df92b1412
Revises: 072437088f6c
Create Date: 2026-10-10 03:00:00.000000

CONTEXTO (backend-fastapi/docs/marcenaria/SPEC-13A-ENTREGA-BACKEND-MARCENARIA.md):
- `marcenaria_entregas`: a entrega de cada ambiente aprovado (checklist,
  situacao, data, montadores, quem recebeu). Nasce na aprovacao (D1).
- `marcenaria_pendencias`: o que ficou por fazer na obra (D6).
- `marcenaria_entrega_fotos`: o vinculo entre a foto da OS e a entrega (D7).
- `marcenaria_agendamentos`: as visitas de instalacao (D9).

MIGRACAO DE DADOS: NENHUMA. OS aprovadas antes desta versao ficam sem
entregas (a aba mostra "sem entrega"); nada e inventado para elas.

SEGURANCA (PR8): so CRIA tabelas novas, e so as que FALTAREM (o create_all do
startup ja as cria numa instalacao nova). Nenhuma tabela existente e alterada:
a `ordens_servico.data_instalacao` (I5b) ja existe desde a fabrica (F3).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '2c4df92b1412'
down_revision: Union[str, Sequence[str], None] = '072437088f6c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# A ordem importa: as filhas (pendencias, fotos) apontam para a entrega.
ENTREGAS = "marcenaria_entregas"
PENDENCIAS = "marcenaria_pendencias"
FOTOS = "marcenaria_entrega_fotos"
AGENDAMENTOS = "marcenaria_agendamentos"


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())                      # o que o banco tem AGORA
    # Escritas aqui de proposito (foto de hoje), sem importar os models.
    if not insp.has_table(ENTREGAS):
        op.create_table(
            ENTREGAS,
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("os_id", sa.Integer(), sa.ForeignKey("ordens_servico.id"), nullable=False),
            sa.Column("ambiente_id", sa.Integer(), sa.ForeignKey("marcenaria_ambientes.id"), nullable=False),
            sa.Column("checklist", sa.JSON(), nullable=False),
            sa.Column("situacao", sa.String(14), nullable=False, server_default="PENDENTE"),
            sa.Column("data_entrega", sa.Date(), nullable=True),
            sa.Column("montadores", sa.JSON(), nullable=True),
            sa.Column("recebido_por", sa.String(150), nullable=True),
            sa.Column("observacoes", sa.String(1000), nullable=True),
            sa.Column("registrado_por_nome", sa.String(150), nullable=True),
            sa.Column("registrado_em", sa.DateTime(), nullable=True),
            sa.UniqueConstraint("os_id", "ambiente_id", name="uq_marcenaria_entregas_os_ambiente"),
        )
    if not insp.has_table(PENDENCIAS):
        op.create_table(
            PENDENCIAS,
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("entrega_id", sa.Integer(), sa.ForeignKey(f"{ENTREGAS}.id", ondelete="CASCADE"), nullable=False),
            sa.Column("descricao", sa.String(300), nullable=False),
            sa.Column("situacao", sa.String(10), nullable=False, server_default="ABERTA"),
            sa.Column("criada_em", sa.DateTime(), nullable=False),
            sa.Column("criada_por_nome", sa.String(150), nullable=True),
            sa.Column("resolucao", sa.String(300), nullable=True),
            sa.Column("resolvida_em", sa.Date(), nullable=True),
            sa.Column("resolvida_por_nome", sa.String(150), nullable=True),
        )
        op.create_index("ix_marcenaria_pendencias_aberta", PENDENCIAS, ["situacao"])
    if not insp.has_table(FOTOS):
        op.create_table(
            FOTOS,
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("entrega_id", sa.Integer(), sa.ForeignKey(f"{ENTREGAS}.id", ondelete="CASCADE"), nullable=False),
            sa.Column("os_foto_id", sa.Integer(), sa.ForeignKey("ordem_servico_fotos.id", ondelete="CASCADE"),
                      nullable=False),
            sa.Column("tipo", sa.String(10), nullable=False),
        )
    if not insp.has_table(AGENDAMENTOS):
        op.create_table(
            AGENDAMENTOS,
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("os_id", sa.Integer(), sa.ForeignKey("ordens_servico.id"), nullable=False),
            sa.Column("data", sa.Date(), nullable=False),
            sa.Column("hora_inicio", sa.String(5), nullable=True),
            sa.Column("ambiente_ids", sa.JSON(), nullable=False),
            sa.Column("montadores", sa.JSON(), nullable=False),
            sa.Column("observacao", sa.String(300), nullable=True),
            sa.Column("criado_por_nome", sa.String(150), nullable=True),
            sa.Column("criado_em", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_marcenaria_agendamentos_data", AGENDAMENTOS, ["data"])


def downgrade() -> None:
    insp = sa.inspect(op.get_bind())
    # As filhas antes da mae (as tabelas levam os indices junto).
    for tabela in (FOTOS, PENDENCIAS, AGENDAMENTOS, ENTREGAS):
        if insp.has_table(tabela):
            op.drop_table(tabela)
