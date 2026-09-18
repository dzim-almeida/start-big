"""campos da NF-e de devolucao em documento_fiscal e documento_fiscal_item

Revision ID: u4v5w6x7y8z9
Revises: t3u4v5w6x7y8
Create Date: 2026-09-17 23:30:00.000000

CONTEXTO (TASK003):
A NF-e de devolução (finalidade 4) é uma emissão nova que aponta para a nota
devolvida e, quando autorizada, incrementa o "já devolvido" de cada item da
origem -- é esse acumulado que impede devolver duas vezes a mesma peça.

SEGURANÇA:
- Cada coluna é adicionada só se AUSENTE: o create_all() do startup pode já
  tê-las criado num banco novo.
- `finalidade_emissao` nasce 1 (normal) e `quantidade_devolvida_acumulada`
  nasce 0 nas linhas existentes -- nenhum documento antigo vira devolução.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'u4v5w6x7y8z9'
down_revision: Union[str, Sequence[str], None] = 't3u4v5w6x7y8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


COLUNAS_DOCUMENTO = [
    sa.Column("finalidade_emissao", sa.Integer(), nullable=False, server_default=sa.text("1")),
    sa.Column("documento_referenciado_id", sa.Integer(), nullable=True),
    sa.Column("chave_documento_referenciado", sa.String(length=44), nullable=True),
    sa.Column("devolver_estoque", sa.Boolean(), nullable=True),
]
COLUNAS_ITEM = [
    sa.Column("quantidade_devolvida_acumulada", sa.Integer(), nullable=False, server_default=sa.text("0")),
]


def _tem_coluna(insp, tabela: str, coluna: str) -> bool:
    return any(c["name"] == coluna for c in insp.get_columns(tabela))


def _adicionar_faltantes(insp, tabela: str, colunas: list) -> list[str]:
    faltantes = [c for c in colunas if not _tem_coluna(insp, tabela, c.name)]
    if faltantes:
        with op.batch_alter_table(tabela) as batch_op:
            for coluna in faltantes:
                batch_op.add_column(coluna)
    return [c.name for c in faltantes]


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)

    novas = _adicionar_faltantes(insp, "documento_fiscal", COLUNAS_DOCUMENTO)
    _adicionar_faltantes(insp, "documento_fiscal_item", COLUNAS_ITEM)

    # Índices só quando a coluna acabou de nascer (o create_all já os cria).
    if "documento_referenciado_id" in novas:
        op.create_index(
            "ix_documento_fiscal_documento_referenciado_id",
            "documento_fiscal", ["documento_referenciado_id"],
        )
    if "chave_documento_referenciado" in novas:
        op.create_index(
            "ix_documento_fiscal_chave_documento_referenciado",
            "documento_fiscal", ["chave_documento_referenciado"],
        )


def downgrade() -> None:
    with op.batch_alter_table("documento_fiscal_item") as batch_op:
        batch_op.drop_column("quantidade_devolvida_acumulada")
    with op.batch_alter_table("documento_fiscal") as batch_op:
        for coluna in COLUNAS_DOCUMENTO:
            batch_op.drop_column(coluna.name)
