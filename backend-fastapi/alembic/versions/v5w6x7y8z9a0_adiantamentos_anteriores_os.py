"""adiciona ordens_servico.adiantamentos_anteriores

Revision ID: v5w6x7y8z9a0
Revises: u4v5w6x7y8z9
Create Date: 2026-09-19 19:00:00.000000

CONTEXTO:
O adiantamento (`valor_entrada`) é zerado a cada reabertura e nada guardava a
soma dos anteriores. Na segunda reabertura o `reabrir` recomputava o crédito
como `pagamentos + valor_entrada` -- e o adiantamento da primeira sessão sumia.
O cliente era cobrado de novo por ele. Esta coluna guarda o que se perdia.

BACKFILL:
OS já reaberta UMA vez tem o adiantamento antigo dentro de `credito_anterior`
(= pagamentos + adiantamento, pela conta antiga). Recupera-se por diferença:
`credito_anterior - soma(pagamentos)`. Sem isto a correção regrediria essas OS:
o `finalizar` novo soma `pagamentos + adiantamentos_anteriores`, e com a coluna
vazia cobraria de novo o adiantamento que o crédito já continha.

OS reaberta DUAS vezes pela conta antiga já perdeu o adiantamento (crédito =
só pagamentos) -- a diferença dá 0, e fica como está: não há de onde recuperar.

SEGURANÇA:
- Decide pela AUSÊNCIA DA COLUNA para o ADD, mas o backfill roda SEMPRE: se o
  `create_all()` do startup já criou a coluna (banco novo), não há linha com
  `credito_anterior` e o UPDATE é vazio. Se o banco é antigo, a coluna nasce
  aqui e o backfill preenche. É a regra do CLAUDE.md (modelo: 965c71a2da9a).
- `ADD COLUMN` direto, não `batch_alter_table`: com PRAGMA foreign_keys=ON o
  batch recria a tabela e o DROP falha pela FK de `ordem_servico_pagamentos`.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'v5w6x7y8z9a0'
down_revision: Union[str, Sequence[str], None] = 'u4v5w6x7y8z9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABELA = "ordens_servico"
COLUNA = "adiantamentos_anteriores"


def _tem_coluna(insp, tabela: str, coluna: str) -> bool:
    return any(c["name"] == coluna for c in insp.get_columns(tabela))


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)

    if not insp.has_table(TABELA):
        return

    if not _tem_coluna(insp, TABELA, COLUNA):
        op.add_column(TABELA, sa.Column(COLUNA, sa.Integer(), nullable=True))

    # Backfill idempotente: só onde a coluna ainda é NULL e há crédito. Rodar
    # duas vezes não muda nada.
    if insp.has_table("ordem_servico_pagamentos"):
        op.execute(sa.text(f"""
            UPDATE {TABELA}
               SET {COLUNA} = MAX(0, credito_anterior - COALESCE((
                       SELECT SUM(p.valor) FROM ordem_servico_pagamentos p
                        WHERE p.ordem_servico_id = {TABELA}.id
                   ), 0))
             WHERE credito_anterior IS NOT NULL
               AND {COLUNA} IS NULL
        """))


def downgrade() -> None:
    with op.batch_alter_table(TABELA) as batch_op:
        batch_op.drop_column(COLUNA)
