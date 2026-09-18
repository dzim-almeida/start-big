# ---------------------------------------------------------------------------
# ARQUIVO: test/db/test_migracao_campos_devolucao.py
# DESCRIÇÃO: A migration u4v5w6x7y8z9 num banco de loja em operação.
#
# ⚠️ alembic/env.py lê `settings.DATABASE_URL`; o fixture redireciona para o
# tmp_path e o teste se recusa a rodar fora dele (ver
# test_migracao_numeracao_confirmada.py).
# ---------------------------------------------------------------------------

import os

import pytest
import sqlalchemy as sa
from alembic.config import Config
from alembic import command

from app.core.config import settings

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REVISAO_ANTERIOR = "t3u4v5w6x7y8"
REVISAO = "u4v5w6x7y8z9"


def _config(url: str) -> Config:
    assert url == settings.DATABASE_URL and "loja.db" in url
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    return cfg


@pytest.fixture
def banco(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'loja.db'}"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    engine = sa.create_engine(url)
    with engine.begin() as conn:
        conn.execute(sa.text(
            "CREATE TABLE documento_fiscal (id INTEGER PRIMARY KEY, status VARCHAR(15) NOT NULL)"
        ))
        conn.execute(sa.text(
            "CREATE TABLE documento_fiscal_item (id INTEGER PRIMARY KEY, "
            "documento_fiscal_id INTEGER NOT NULL, quantidade_milesimos INTEGER NOT NULL)"
        ))
        conn.execute(sa.text("INSERT INTO documento_fiscal (status) VALUES ('AUTORIZADA')"))
        conn.execute(sa.text(
            "INSERT INTO documento_fiscal_item (documento_fiscal_id, quantidade_milesimos) VALUES (1, 2000)"
        ))
    command.stamp(_config(url), REVISAO_ANTERIOR)
    yield url, engine
    engine.dispose()


def _colunas(engine, tabela) -> set[str]:
    return {c["name"] for c in sa.inspect(engine).get_columns(tabela)}


def test_banco_antigo_ganha_as_colunas_com_defaults_neutros(banco):
    url, engine = banco
    command.upgrade(_config(url), REVISAO)

    assert {"finalidade_emissao", "documento_referenciado_id", "chave_documento_referenciado", "devolver_estoque"} <= _colunas(engine, "documento_fiscal")
    assert "quantidade_devolvida_acumulada" in _colunas(engine, "documento_fiscal_item")
    with engine.connect() as conn:
        assert conn.execute(sa.text("SELECT finalidade_emissao FROM documento_fiscal")).scalar() == 1
        assert conn.execute(sa.text("SELECT quantidade_devolvida_acumulada FROM documento_fiscal_item")).scalar() == 0


def test_colunas_ja_criadas_pelo_create_all_nao_quebram(banco):
    url, engine = banco
    with engine.begin() as conn:
        conn.execute(sa.text("ALTER TABLE documento_fiscal ADD COLUMN finalidade_emissao INTEGER NOT NULL DEFAULT 1"))
        conn.execute(sa.text("ALTER TABLE documento_fiscal ADD COLUMN documento_referenciado_id INTEGER"))
        conn.execute(sa.text("ALTER TABLE documento_fiscal ADD COLUMN chave_documento_referenciado VARCHAR(44)"))
        conn.execute(sa.text("ALTER TABLE documento_fiscal ADD COLUMN devolver_estoque BOOLEAN"))
        conn.execute(sa.text("ALTER TABLE documento_fiscal_item ADD COLUMN quantidade_devolvida_acumulada INTEGER NOT NULL DEFAULT 0"))
    command.upgrade(_config(url), REVISAO)  # não pode levantar "duplicate column"
    assert "devolver_estoque" in _colunas(engine, "documento_fiscal")
