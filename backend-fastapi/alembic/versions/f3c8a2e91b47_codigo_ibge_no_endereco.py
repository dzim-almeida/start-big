"""codigo IBGE do municipio no endereco

Revision ID: f3c8a2e91b47
Revises: e5b7d1c3a920
Create Date: 2026-09-08 10:15:00.000000

CONTEXTO:
O `cMun` (codigo IBGE do municipio) e obrigatorio no XML da NF-e/NFC-e, e o
payload nunca o enviou: mandava so `cidade` e `uf`, e quem resolvia o codigo
era a integradora, pelo NOME do municipio. E ai que ela erra — homonimos entre
estados tem codigos diferentes, e o Ceara tem os seus.

Pior: a consulta de CNPJ (BrasilAPI) JA RECEBIA `codigo_ibge` na resposta e o
descartava, porque nao havia coluna para guardar.

BACKFILL:
Preenche a partir da tabela dos 184 municipios do Ceara, embarcada em
`app/services/fiscal/derivacao/bases/municipios_ce.py` e gerada da API oficial
do IBGE. So toca linha com o campo NULO e com UF = CE — endereco de outro
estado fica vazio de proposito: uma tabela estadual respondendo sobre outro
estado e pior que nao responder, porque devolveria o codigo do municipio
homonimo errado. Esses enderecos continuam caindo no comportamento atual.

SEGURANCA:
- Decide pela AUSENCIA da coluna: o create_all() do startup roda ANTES das
  migracoes e pode te-la criado numa instalacao nova. Ver CLAUDE.md.
- Rodar de novo e inocuo: o backfill so preenche o que esta NULO.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f3c8a2e91b47'
down_revision: Union[str, Sequence[str], None] = 'e5b7d1c3a920'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABELA = "enderecos"
COLUNA = "codigo_ibge"


def _tabela_municipios() -> dict:
    """
    Carrega a base embarcada SEM passar pelo pacote `app.services.fiscal`.

    O import direto dispararia o __init__ daquele pacote, que puxa models e
    cria um ciclo durante a migracao. Aqui so interessa o dicionario.
    """
    import importlib.util
    import os

    raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    caminho = os.path.join(
        raiz, "app", "services", "fiscal", "derivacao", "bases", "municipios_ce.py",
    )
    if not os.path.exists(caminho):
        return {}

    spec = importlib.util.spec_from_file_location("_municipios_ce_mig", caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return {
        "mapa": modulo.MUNICIPIOS_CE,
        "normalizar": modulo._normalizar,
    }


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)

    if not insp.has_table(TABELA):
        return

    colunas = {c["name"] for c in insp.get_columns(TABELA)}
    if COLUNA not in colunas:
        op.add_column(TABELA, sa.Column(COLUNA, sa.String(7), nullable=True))

    base = _tabela_municipios()
    if not base:
        return

    mapa, normalizar = base["mapa"], base["normalizar"]

    # So enderecos do Ceara, e so os que ainda estao sem codigo.
    linhas = conn.execute(
        sa.text(
            f"SELECT id, cidade FROM {TABELA} "
            f"WHERE {COLUNA} IS NULL AND UPPER(TRIM(COALESCE(estado, ''))) = 'CE'"
        )
    ).fetchall()

    for endereco_id, cidade in linhas:
        codigo = mapa.get(normalizar(cidade or ""))
        if not codigo:
            continue
        conn.execute(
            sa.text(f"UPDATE {TABELA} SET {COLUNA} = :cod WHERE id = :id"),
            {"cod": codigo, "id": endereco_id},
        )


def downgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)

    if not insp.has_table(TABELA):
        return
    if COLUNA in {c["name"] for c in insp.get_columns(TABELA)}:
        op.drop_column(TABELA, COLUNA)
