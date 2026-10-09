"""marcenaria (Spec 08A): aprovacao do orcamento e geracao da OS

Revision ID: 971eb6cc5a33
Revises: 683ff38df873
Create Date: 2026-10-09 18:00:00.000000

CONTEXTO (backend-fastapi/docs/marcenaria/SPEC-08A-APROVACAO-OS-BACKEND-MARCENARIA.md):
- `ordem_servico_itens.origem` (⚠️ unica tabela EXISTENTE alterada): de que
  documento o item veio. Nula = item comum, que e o caso de TODOS os itens que
  ja existem; o servico da OS so recusa editar/remover item com origem (D18).
- `marcenaria_moveis.os_item_id`: o item da OS que o movel virou (D7).
- `marcenaria_orcamentos`: instalacao aprovada e o resumo do que foi aprovado
  (total, sinal combinado, sinal recebido).

MIGRACAO DE DADOS: NENHUMA. Toda coluna nova nasce nula.

SEGURANCA (PR8):
- Cada coluna so e criada se FALTAR: o create_all() do startup nao altera
  tabela existente, mas numa instalacao nova ja cria as tabelas da marcenaria
  com as colunas desta spec.
- `ADD COLUMN` direto, sem `batch_alter_table`: a tabela de itens da OS e
  grande nas lojas antigas, e o batch a recriaria inteira.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '971eb6cc5a33'
down_revision: Union[str, Sequence[str], None] = '683ff38df873'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (tabela, coluna, como criar). Escritas aqui de proposito: a migracao e uma
# foto de hoje, e mudar um model amanha nao pode muda-la.
COLUNAS = (
    ("ordem_servico_itens", "origem", "VARCHAR(30)"),
    # ADD COLUMN com REFERENCES funciona no SQLite quando a coluna nasce nula.
    ("marcenaria_moveis", "os_item_id", "INTEGER REFERENCES ordem_servico_itens(id) ON DELETE SET NULL"),
    ("marcenaria_orcamentos", "instalacao_aprovada", "BOOLEAN"),
    ("marcenaria_orcamentos", "resumo_aprovado_total_centavos", "INTEGER"),
    ("marcenaria_orcamentos", "resumo_aprovado_sinal_centavos", "INTEGER"),
    ("marcenaria_orcamentos", "sinal_recebido_centavos", "INTEGER"),
)

INDICES = (
    ("ix_marcenaria_moveis_os_item", "marcenaria_moveis", "os_item_id"),
    ("ix_marcenaria_orcamentos_os", "marcenaria_orcamentos", "os_id"),
)


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())                      # o que o banco tem AGORA
    for tabela, coluna, tipo in COLUNAS:
        if not insp.has_table(tabela):                    # banco sem a tabela (nada a fazer)
            continue
        existentes = {c["name"] for c in insp.get_columns(tabela)}
        if coluna not in existentes:                      # so cria o que falta
            op.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo}")

    insp = sa.inspect(op.get_bind())                      # rele depois das colunas novas
    for nome, tabela, coluna in INDICES:
        if not insp.has_table(tabela):
            continue
        if nome not in {i["name"] for i in insp.get_indexes(tabela)}:
            op.create_index(nome, tabela, [coluna])


def downgrade() -> None:
    insp = sa.inspect(op.get_bind())
    for nome, tabela, _coluna in INDICES:
        if insp.has_table(tabela) and nome in {i["name"] for i in insp.get_indexes(tabela)}:
            op.drop_index(nome, table_name=tabela)
    # No SQLite, tirar coluna so pelo batch (recria a tabela). Na volta, aceita-se.
    por_tabela: dict[str, list[str]] = {}
    for tabela, coluna, _tipo in COLUNAS:
        por_tabela.setdefault(tabela, []).append(coluna)
    for tabela, colunas in por_tabela.items():
        if not insp.has_table(tabela):
            continue
        existentes = {c["name"] for c in insp.get_columns(tabela)}
        with op.batch_alter_table(tabela) as batch:
            for coluna in colunas:
                if coluna in existentes:
                    batch.drop_column(coluna)
