"""marcenaria (Spec 12A): etapas de producao por movel

Revision ID: 072437088f6c
Revises: 642b2e8f79fa
Create Date: 2026-10-10 00:30:00.000000

CONTEXTO (backend-fastapi/docs/marcenaria/SPEC-12A-PRODUCAO-BACKEND-MARCENARIA.md):
- `marcenaria_etapas`: as etapas de producao de cada movel interno aprovado
  (Corte, Borda, Furacao, Montagem, Embalagem...), com status, responsavel e
  datas. Nasce na aprovacao do orcamento (copia da configuracao, D1).

MIGRACAO DE DADOS: NENHUMA. OS aprovadas antes desta versao ficam com os
moveis "sem etapas"; a tela oferece "aplicar o padrao" (D6).

SEGURANCA (PR8): so CRIA uma tabela nova, e so se ela FALTAR (o create_all do
startup ja a cria numa instalacao nova). Nenhuma tabela existente e alterada.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '072437088f6c'
down_revision: Union[str, Sequence[str], None] = '642b2e8f79fa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABELA = "marcenaria_etapas"


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())                      # o que o banco tem AGORA
    if insp.has_table(TABELA):
        return                                            # o create_all ja criou: nada a fazer
    # Escrita aqui de proposito (foto de hoje), sem importar o model.
    op.create_table(
        TABELA,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("movel_id", sa.Integer(), sa.ForeignKey("marcenaria_moveis.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nome", sa.String(60), nullable=False),
        sa.Column("ordem", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(12), nullable=False, server_default="PENDENTE"),
        sa.Column("responsavel_funcionario_id", sa.Integer(), sa.ForeignKey("funcionarios.id"), nullable=True),
        sa.Column("responsavel_nome", sa.String(150), nullable=True),
        sa.Column("iniciada_em", sa.DateTime(), nullable=True),
        sa.Column("concluida_em", sa.DateTime(), nullable=True),
        sa.Column("concluida_por_nome", sa.String(150), nullable=True),
        sa.UniqueConstraint("movel_id", "nome", name="uq_marcenaria_etapas_movel_nome"),
    )
    op.create_index("ix_marcenaria_etapas_movel", TABELA, ["movel_id", "ordem"])
    op.create_index("ix_marcenaria_etapas_status", TABELA, ["status"])


def downgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if insp.has_table(TABELA):
        op.drop_table(TABELA)                              # leva os indices junto
