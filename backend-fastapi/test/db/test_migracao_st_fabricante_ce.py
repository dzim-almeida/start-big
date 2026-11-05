# ---------------------------------------------------------------------------
# ARQUIVO: test/db/test_migracao_st_fabricante_ce.py
# DESCRICAO: A migracao s7f4br1c4c01 (opcao do fabricante do CE) num banco de
#            loja ANTIGO. Nunca toca o banco real.
# ---------------------------------------------------------------------------

import os

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from app.core.config import settings

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REVISAO_ANTERIOR = "c1cf0p7r0c01"
REVISAO = "s7f4br1c4c01"
COLUNA = "nfe_st_fabricante_ce"


def _config(url: str) -> Config:
    assert url == settings.DATABASE_URL and "loja.db" in url
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    return cfg


@pytest.fixture
def banco(tmp_path, monkeypatch):
    """Loja ja configurada, na head de antes."""
    url = f"sqlite:///{tmp_path / 'loja.db'}"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    engine = sa.create_engine(url)
    with engine.begin() as conn:
        conn.execute(sa.text(
            "CREATE TABLE empresa_fiscal_settings (id INTEGER PRIMARY KEY, empresa_id INTEGER, serie_nfe INTEGER)"
        ))
        conn.execute(sa.text("INSERT INTO empresa_fiscal_settings (empresa_id, serie_nfe) VALUES (1, 2)"))
    command.stamp(_config(url), REVISAO_ANTERIOR)
    yield url, engine
    engine.dispose()


def _colunas(engine) -> set[str]:
    engine.dispose()
    return {c["name"] for c in sa.inspect(engine).get_columns("empresa_fiscal_settings")}


def test_loja_antiga_nasce_com_a_opcao_desligada(banco):
    url, engine = banco

    command.upgrade(_config(url), REVISAO)

    with engine.connect() as conn:
        linha = conn.execute(sa.text(
            f"SELECT empresa_id, serie_nfe, {COLUNA} FROM empresa_fiscal_settings"
        )).one()
    assert tuple(linha) == (1, 2, 0)


def test_coluna_ja_criada_nao_quebra(banco):
    url, engine = banco
    with engine.begin() as conn:
        conn.execute(sa.text(f"ALTER TABLE empresa_fiscal_settings ADD COLUMN {COLUNA} BOOLEAN NOT NULL DEFAULT 0"))

    command.upgrade(_config(url), REVISAO)              # sem "duplicate column"

    assert COLUNA in _colunas(engine)


def test_downgrade_tira_a_coluna(banco):
    url, engine = banco
    command.upgrade(_config(url), REVISAO)

    command.downgrade(_config(url), REVISAO_ANTERIOR)

    assert COLUNA not in _colunas(engine)
