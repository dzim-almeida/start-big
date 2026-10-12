# ---------------------------------------------------------------------------
# ARQUIVO: test/db/test_migracao_producao_marcenaria.py
# DESCRICAO: A migracao 072437088f6c (Spec 12A da marcenaria) num banco de loja.
#            Nunca toca o banco real da maquina (mesmo padrao das outras).
# ---------------------------------------------------------------------------

import os

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from app.core.config import settings
from app.db.base import Base

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REVISAO_ANTERIOR = "642b2e8f79fa"          # a head antes da Spec 12A (Spec 11A)
REVISAO = "072437088f6c"
TABELA = "marcenaria_etapas"


def _config(url: str) -> Config:
    """Config do Alembic apontada para o banco temporario (e so para ele)."""
    assert url == settings.DATABASE_URL and "loja.db" in url
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    return cfg


@pytest.fixture
def banco(tmp_path, monkeypatch):
    """Loja com um movel ja aprovado, na head antiga."""
    url = f"sqlite:///{tmp_path / 'loja.db'}"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    engine = sa.create_engine(url)
    with engine.begin() as conn:
        conn.execute(sa.text("CREATE TABLE funcionarios (id INTEGER PRIMARY KEY)"))
        conn.execute(sa.text("CREATE TABLE marcenaria_moveis (id INTEGER PRIMARY KEY, nome VARCHAR(120))"))
        conn.execute(sa.text("INSERT INTO marcenaria_moveis (nome) VALUES ('Balcão')"))
    command.stamp(_config(url), REVISAO_ANTERIOR)
    yield url, engine
    engine.dispose()


def _inspector(engine) -> sa.Inspector:
    engine.dispose()
    return sa.inspect(engine)


def test_cria_a_tabela_igual_ao_model(banco):
    url, engine = banco

    command.upgrade(_config(url), REVISAO)

    insp = _inspector(engine)
    assert {c["name"] for c in insp.get_columns(TABELA)} == set(Base.metadata.tables[TABELA].columns.keys())
    assert {"ix_marcenaria_etapas_movel", "ix_marcenaria_etapas_status"} <= {i["name"] for i in insp.get_indexes(TABELA)}
    assert [u["column_names"] for u in insp.get_unique_constraints(TABELA)] == [["movel_id", "nome"]]
    with engine.begin() as conn:
        # O status nasce PENDENTE, e o movel que ja existia segue igual (sem etapas).
        conn.execute(sa.text(f"INSERT INTO {TABELA} (movel_id, nome, ordem) VALUES (1, 'Corte', 1)"))
        assert conn.execute(sa.text(f"SELECT status FROM {TABELA}")).scalar() == "PENDENTE"
        assert conn.execute(sa.text("SELECT nome FROM marcenaria_moveis")).scalar() == "Balcão"


def test_tabela_ja_criada_pelo_startup_nao_quebra(banco):
    url, engine = banco
    with engine.begin() as conn:
        conn.execute(sa.text(f"CREATE TABLE {TABELA} (id INTEGER PRIMARY KEY)"))

    command.upgrade(_config(url), REVISAO)                         # nao pode levantar "already exists"

    assert _inspector(engine).has_table(TABELA)


def test_downgrade_tira_a_tabela(banco):
    url, engine = banco
    command.upgrade(_config(url), REVISAO)

    command.downgrade(_config(url), REVISAO_ANTERIOR)

    insp = _inspector(engine)
    assert not insp.has_table(TABELA) and insp.has_table("marcenaria_moveis")
