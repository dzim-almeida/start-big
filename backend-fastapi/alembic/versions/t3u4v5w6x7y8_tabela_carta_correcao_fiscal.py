"""cria tabela carta_correcao_fiscal

Revision ID: t3u4v5w6x7y8
Revises: s2t3u4v5w6x7
Create Date: 2026-09-17 22:30:00.000000

CONTEXTO (TASK002):
Carta de Correção Eletrônica (CC-e) -- evento anexo à NF-e, até 20 por nota,
cada um com protocolo, XML e PDF próprios. Tabela própria, como a
inutilizacao_fiscal; a nota não muda.

SEGURANÇA:
- Decide pela ausência da TABELA: se o create_all() do startup já a criou,
  não há nada a fazer.
- Tabela nova, sem backfill: nenhuma linha existente é tocada.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 't3u4v5w6x7y8'
down_revision: Union[str, Sequence[str], None] = 's2t3u4v5w6x7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABELA = "carta_correcao_fiscal"


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)

    if insp.has_table(TABELA):
        return

    op.create_table(
        TABELA,
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("empresa_id", sa.Integer(), nullable=False),
        sa.Column(
            "documento_id", sa.Integer(), sa.ForeignKey("documento_fiscal.id"), nullable=False,
        ),
        sa.Column("sequencia", sa.Integer(), nullable=True),
        sa.Column("correcao", sa.String(length=1000), nullable=False),
        sa.Column("status", sa.String(length=15), nullable=False),
        sa.Column("protocolo", sa.String(length=20), nullable=True),
        sa.Column("codigo_status_sefaz", sa.Integer(), nullable=True),
        sa.Column("mensagem_sefaz", sa.String(length=500), nullable=True),
        sa.Column("url_xml", sa.String(length=500), nullable=True),
        sa.Column("url_pdf", sa.String(length=500), nullable=True),
        sa.Column("caminho_xml_local", sa.String(length=500), nullable=True),
        sa.Column("caminho_pdf_local", sa.String(length=500), nullable=True),
        sa.Column("ambiente_emissao", sa.Integer(), nullable=True),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("data_evento", sa.DateTime(), nullable=True),
        sa.Column(
            "data_criacao", sa.DateTime(), nullable=False, server_default=sa.func.now(),
        ),
    )
    op.create_index(f"ix_{TABELA}_id", TABELA, ["id"])
    op.create_index(f"ix_{TABELA}_empresa_id", TABELA, ["empresa_id"])
    op.create_index(f"ix_{TABELA}_documento_id", TABELA, ["documento_id"])
    op.create_index(f"ix_{TABELA}_status", TABELA, ["status"])


def downgrade() -> None:
    op.drop_table(TABELA)
