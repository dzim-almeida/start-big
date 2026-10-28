# ---------------------------------------------------------------------------
# ARQUIVO: test/db/test_migracao_nfse_servico.py
# DESCRICAO: A migracao n5f0s3rv1c01 (codigo nacional e NBS no servico, F1 do
#            docs/nfse-plano.md) num banco de loja. Nunca toca o banco real.
# ---------------------------------------------------------------------------

import os

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from app.core.config import settings

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REVISAO_ANTERIOR = "f4t1m0v3l002"
REVISAO = "n5f0s3rv1c01"
COLUNAS = {"codigo_tributacao_nacional", "codigo_nbs"}


def _config(url: str) -> Config:
    assert url == settings.DATABASE_URL and "loja.db" in url
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    return cfg


@pytest.fixture
def banco(tmp_path, monkeypatch):
    """Loja com um servico ja classificado pela LC 116, na head de antes."""
    url = f"sqlite:///{tmp_path / 'loja.db'}"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    engine = sa.create_engine(url)
    with engine.begin() as conn:
        conn.execute(sa.text(
            "CREATE TABLE servico_fiscal (id INTEGER PRIMARY KEY, servico_id INTEGER, codigo_servico_lc116 VARCHAR(10))"
        ))
        conn.execute(sa.text("INSERT INTO servico_fiscal (servico_id, codigo_servico_lc116) VALUES (7, '1401')"))
    command.stamp(_config(url), REVISAO_ANTERIOR)
    yield url, engine
    engine.dispose()


def _colunas(engine) -> set[str]:
    engine.dispose()
    return {c["name"] for c in sa.inspect(engine).get_columns("servico_fiscal")}


def test_colunas_novas_nascem_vazias_e_o_servico_continua_igual(banco):
    url, engine = banco

    command.upgrade(_config(url), REVISAO)

    assert COLUNAS <= _colunas(engine)
    with engine.connect() as conn:
        linha = conn.execute(sa.text(
            "SELECT servico_id, codigo_servico_lc116, codigo_tributacao_nacional, codigo_nbs FROM servico_fiscal"
        )).one()
        assert tuple(linha) == (7, "1401", None, None)


def test_colunas_ja_criadas_nao_quebram(banco):
    url, engine = banco
    with engine.begin() as conn:
        conn.execute(sa.text("ALTER TABLE servico_fiscal ADD COLUMN codigo_nbs VARCHAR(9)"))

    command.upgrade(_config(url), REVISAO)              # sem "duplicate column"

    assert COLUNAS <= _colunas(engine)


def test_downgrade_tira_as_colunas(banco):
    url, engine = banco
    command.upgrade(_config(url), REVISAO)

    command.downgrade(_config(url), REVISAO_ANTERIOR)

    assert not COLUNAS & _colunas(engine)


# =========================
# n5f0s3rv1c02: configuracao da NFS-e (G3)
# =========================

def test_configuracao_da_nfse_nasce_desligada(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'loja.db'}"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    engine = sa.create_engine(url)
    with engine.begin() as conn:
        conn.execute(sa.text("CREATE TABLE servico_fiscal (id INTEGER PRIMARY KEY)"))
        conn.execute(sa.text("CREATE TABLE empresa_fiscal_settings (id INTEGER PRIMARY KEY, empresa_id INTEGER)"))
        conn.execute(sa.text("INSERT INTO empresa_fiscal_settings (empresa_id) VALUES (1)"))
    command.stamp(_config(url), REVISAO)

    command.upgrade(_config(url), "n5f0s3rv1c02")

    engine.dispose()
    with engine.connect() as conn:
        linha = conn.execute(sa.text(
            "SELECT nfse_reter_iss_pj, nfse_uma_nota_por_codigo, nfse_ibs_cbs_cst, nfse_ibs_cbs_cclass "
            "FROM empresa_fiscal_settings"
        )).one()
    assert tuple(linha) == (0, 0, None, None)

    command.downgrade(_config(url), REVISAO)
    engine.dispose()
    colunas = {c["name"] for c in sa.inspect(engine).get_columns("empresa_fiscal_settings")}
    assert not {"nfse_reter_iss_pj", "nfse_uma_nota_por_codigo"} & colunas
    engine.dispose()
