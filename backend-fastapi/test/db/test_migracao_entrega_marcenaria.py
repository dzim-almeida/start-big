# ---------------------------------------------------------------------------
# ARQUIVO: test/db/test_migracao_entrega_marcenaria.py
# DESCRICAO: A migracao 2c4df92b1412 (Spec 13A da marcenaria) num banco de loja.
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
REVISAO_ANTERIOR = "072437088f6c"          # a head antes da Spec 13A (Spec 12A)
REVISAO = "2c4df92b1412"
TABELAS = ("marcenaria_entregas", "marcenaria_pendencias", "marcenaria_entrega_fotos", "marcenaria_agendamentos")


def _config(url: str) -> Config:
    """Config do Alembic apontada para o banco temporario (e so para ele)."""
    assert url == settings.DATABASE_URL and "loja.db" in url
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    return cfg


@pytest.fixture
def banco(tmp_path, monkeypatch):
    """Loja com uma OS ja com data de instalacao (fabrica F3), na head antiga."""
    url = f"sqlite:///{tmp_path / 'loja.db'}"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    engine = sa.create_engine(url)
    with engine.begin() as conn:
        conn.execute(sa.text("CREATE TABLE ordens_servico (id INTEGER PRIMARY KEY, data_instalacao DATE)"))
        conn.execute(sa.text("CREATE TABLE marcenaria_ambientes (id INTEGER PRIMARY KEY)"))
        conn.execute(sa.text("CREATE TABLE ordem_servico_fotos (id INTEGER PRIMARY KEY)"))
        conn.execute(sa.text("INSERT INTO ordens_servico (data_instalacao) VALUES ('2026-11-03')"))
    command.stamp(_config(url), REVISAO_ANTERIOR)
    yield url, engine
    engine.dispose()


def _inspector(engine) -> sa.Inspector:
    engine.dispose()
    return sa.inspect(engine)


def test_cria_as_tabelas_iguais_aos_models(banco):
    url, engine = banco

    command.upgrade(_config(url), REVISAO)

    insp = _inspector(engine)
    for tabela in TABELAS:
        assert {c["name"] for c in insp.get_columns(tabela)} == set(Base.metadata.tables[tabela].columns.keys())
    assert "ix_marcenaria_pendencias_aberta" in {i["name"] for i in insp.get_indexes("marcenaria_pendencias")}
    assert "ix_marcenaria_agendamentos_data" in {i["name"] for i in insp.get_indexes("marcenaria_agendamentos")}
    assert [u["column_names"] for u in insp.get_unique_constraints("marcenaria_entregas")] == [["os_id", "ambiente_id"]]
    with engine.begin() as conn:
        # A situacao nasce PENDENTE, e a OS que ja existia segue igual.
        conn.execute(sa.text("INSERT INTO marcenaria_ambientes (id) VALUES (1)"))
        conn.execute(sa.text("INSERT INTO marcenaria_entregas (os_id, ambiente_id, checklist) VALUES (1, 1, '[]')"))
        assert conn.execute(sa.text("SELECT situacao FROM marcenaria_entregas")).scalar() == "PENDENTE"
        assert conn.execute(sa.text("SELECT data_instalacao FROM ordens_servico")).scalar() == "2026-11-03"


def test_tabelas_ja_criadas_pelo_startup_nao_quebram(banco):
    url, engine = banco
    with engine.begin() as conn:
        conn.execute(sa.text("CREATE TABLE marcenaria_entregas (id INTEGER PRIMARY KEY)"))

    command.upgrade(_config(url), REVISAO)                         # nao pode levantar "already exists"

    insp = _inspector(engine)
    assert {c["name"] for c in insp.get_columns("marcenaria_entregas")} == {"id"}   # a que existia fica
    assert all(insp.has_table(t) for t in TABELAS)                                  # as que faltavam nascem


def test_downgrade_tira_as_tabelas(banco):
    url, engine = banco
    command.upgrade(_config(url), REVISAO)

    command.downgrade(_config(url), REVISAO_ANTERIOR)

    insp = _inspector(engine)
    assert not any(insp.has_table(t) for t in TABELAS)
    assert insp.has_table("ordens_servico")
