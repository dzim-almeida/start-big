"""marcenaria (Spec 04A): parametros padrao do orcamento tecnico

Revision ID: 608dc99a8616
Revises: d7a3e9c2f418
Create Date: 2026-10-09 12:00:00.000000

CONTEXTO (backend-fastapi/docs/marcenaria/SPEC-04A-BASE-BACKEND-MARCENARIA.md):
- `configuracoes_marcenaria`: 1:1 com a empresa. Markup, perda, custo/hora, RT,
  validade, prazo de entrega, etapas de producao e checklist de vistoria que
  todo orcamento novo COPIA. Percentuais em basis points, dinheiro em centavos.
- `produtos.sofre_perda` NAO entra aqui: a migracao f1c7a2d9e3b4 (fabrica F1)
  ja cria a coluna, decidindo pela ausencia dela (SPEC-00, Revisao 15).

MIGRACAO DE DADOS: NENHUMA. A tabela nasce vazia; a linha de cada empresa e
criada na primeira leitura (get-or-create), com os padroes do model.

SEGURANCA:
- Decide pela ausencia da TABELA: o create_all() do startup costuma cria-la
  antes desta migracao rodar; nesse caso nao ha nada a fazer.
- Nenhuma tabela existente e alterada.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '608dc99a8616'
down_revision: Union[str, Sequence[str], None] = 'd7a3e9c2f418'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABELA = "configuracoes_marcenaria"


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())                     # o que o banco tem AGORA
    if insp.has_table(TABELA):                           # create_all ja criou: nada a fazer
        return

    # Mesmas colunas do model (app/db/models/configuracao_marcenaria.py).
    op.create_table(
        TABELA,
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("empresa_id", sa.Integer(), nullable=False),
        sa.Column("markup_padrao_bp", sa.Integer(), nullable=False),
        sa.Column("perda_padrao_bp", sa.Integer(), nullable=False),
        sa.Column("custo_hora_centavos", sa.Integer(), nullable=False),
        sa.Column("rt_padrao_bp", sa.Integer(), nullable=False),
        sa.Column("rt_modo", sa.String(length=10), nullable=False),
        sa.Column("validade_dias", sa.Integer(), nullable=False),
        sa.Column("prazo_entrega_dias", sa.Integer(), nullable=False),
        sa.Column("etapas_producao", sa.JSON(), nullable=False),
        sa.Column("checklist_vistoria", sa.JSON(), nullable=False),
        sa.Column("data_atualizacao", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("empresa_id"),                # uma configuracao por empresa
    )
    op.create_index(f"ix_{TABELA}_id", TABELA, ["id"])


def downgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if insp.has_table(TABELA):                           # nao falha num banco sem a tabela
        op.drop_index(f"ix_{TABELA}_id", table_name=TABELA)
        op.drop_table(TABELA)
