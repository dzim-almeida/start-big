"""adiciona empresa_fiscal_settings.numeracao_confirmada

Revision ID: s2t3u4v5w6x7
Revises: r1s2t3u4v5w6
Create Date: 2026-09-17 21:00:00.000000

CONTEXTO (TASK001):
Trava contra a Rejeição 204. Uma loja que vem de outro ERP entra com
"último número 0" e emitiria a nota 1 de novo. A coluna fica False até o
operador confirmar série e último número na tela de Emissão Estadual, e
`verificar_emitente` barra qualquer emissão enquanto isso.

BACKFILL:
Quem já tem documento AUTORIZADO neste banco emitiu por aqui -- a numeração
está, por definição, em dia. Essas lojas nascem confirmadas para não travar
o caixa na atualização. A spec previa filtrar por `documento_fiscal.empresa_id`,
mas a tabela não tem essa coluna (o banco é de uma empresa só); o critério é
a existência de qualquer documento autorizado.

SEGURANÇA:
- Decide pela AUSÊNCIA DA COLUNA: se o create_all() do startup já a criou, a
  coluna existe e a linha de backfill ainda roda (é idempotente).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 's2t3u4v5w6x7'
down_revision: Union[str, Sequence[str], None] = 'r1s2t3u4v5w6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABELA = "empresa_fiscal_settings"
COLUNA = "numeracao_confirmada"


def _tem_coluna(insp, tabela: str, coluna: str) -> bool:
    return any(c["name"] == coluna for c in insp.get_columns(tabela))


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)

    # ADD COLUMN direto: o batch recria a tabela e, com PRAGMA foreign_keys=ON
    # no boot, isso pode falhar no DROP (ver u4v5w6x7y8z9). ALTER TABLE ADD
    # COLUMN é nativo no SQLite.
    if not _tem_coluna(insp, TABELA, COLUNA):
        op.add_column(TABELA, sa.Column(
            COLUNA, sa.Boolean(), nullable=False, server_default=sa.text("0"),
        ))

    if "documento_fiscal" in insp.get_table_names():
        op.execute(sa.text(
            f"UPDATE {TABELA} SET {COLUNA} = 1 "
            "WHERE EXISTS (SELECT 1 FROM documento_fiscal WHERE status = 'AUTORIZADA')"
        ))


def downgrade() -> None:
    with op.batch_alter_table(TABELA) as batch_op:
        batch_op.drop_column(COLUNA)
