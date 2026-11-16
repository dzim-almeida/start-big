# ---------------------------------------------------------------------------
# ARQUIVO: test/db/test_migracao_nfse_padrao.py
# DESCRICAO: A migracao n5f0m2padr01 (padrao fiscal da loja para servicos
#            novos, M2 do docs/nfse-melhorias-plano.md) num banco de loja
#            ANTIGO. Nunca toca o banco real.
# ---------------------------------------------------------------------------

import os

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from app.core.config import settings

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REVISAO_ANTERIOR = "m4rc3n5f5e01"
REVISAO = "n5f0m2padr01"
COLUNAS = {"nfse_padrao_codigo_nacional", "nfse_padrao_nbs", "nfse_padrao_aliquota_iss"}


def _config(url: str) -> Config:
    assert url == settings.DATABASE_URL and "loja.db" in url
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    return cfg


@pytest.fixture
def banco(tmp_path, monkeypatch):
    """Loja ja configurada (retencao ligada), na head de antes."""
    url = f"sqlite:///{tmp_path / 'loja.db'}"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    engine = sa.create_engine(url)
    with engine.begin() as conn:
        conn.execute(sa.text(
            "CREATE TABLE empresa_fiscal_settings (id INTEGER PRIMARY KEY, empresa_id INTEGER, "
            "nfse_reter_iss_pj BOOLEAN NOT NULL DEFAULT 0)"
        ))
        conn.execute(sa.text("INSERT INTO empresa_fiscal_settings (empresa_id, nfse_reter_iss_pj) VALUES (1, 1)"))
    command.stamp(_config(url), REVISAO_ANTERIOR)
    yield url, engine
    engine.dispose()


def _colunas(engine) -> set[str]:
    engine.dispose()
    return {c["name"] for c in sa.inspect(engine).get_columns("empresa_fiscal_settings")}


def test_colunas_novas_nascem_vazias_e_a_configuracao_continua_igual(banco):
    url, engine = banco

    command.upgrade(_config(url), REVISAO)

    assert COLUNAS <= _colunas(engine)
    with engine.connect() as conn:
        linha = conn.execute(sa.text(
            "SELECT empresa_id, nfse_reter_iss_pj, nfse_padrao_codigo_nacional, nfse_padrao_nbs, "
            "nfse_padrao_aliquota_iss FROM empresa_fiscal_settings"
        )).one()
        assert tuple(linha) == (1, 1, None, None, None)


def test_colunas_ja_criadas_nao_quebram(banco):
    url, engine = banco
    with engine.begin() as conn:
        conn.execute(sa.text("ALTER TABLE empresa_fiscal_settings ADD COLUMN nfse_padrao_nbs VARCHAR(9)"))

    command.upgrade(_config(url), REVISAO)              # sem "duplicate column"

    assert COLUNAS <= _colunas(engine)


def test_downgrade_tira_as_colunas(banco):
    url, engine = banco
    command.upgrade(_config(url), REVISAO)

    command.downgrade(_config(url), REVISAO_ANTERIOR)

    assert not COLUNAS & _colunas(engine)
