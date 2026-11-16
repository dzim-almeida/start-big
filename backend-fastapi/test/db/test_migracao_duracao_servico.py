# ---------------------------------------------------------------------------
# ARQUIVO: test/db/test_migracao_duracao_servico.py
# DESCRIÇÃO: A migration l4v4dur4c004 — servicos.duracao_minutos, num banco de
#            loja com servicos cadastrados.
#
# ⚠️ alembic/env.py lê `settings.DATABASE_URL`; o fixture redireciona para o
# tmp_path e o teste se recusa a rodar fora dele.
# ---------------------------------------------------------------------------

import os

import pytest
import sqlalchemy as sa
from alembic.config import Config
from alembic import command

from app.core.config import settings

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REVISAO_ANTERIOR = "l4v4ag3nd003"
REVISAO = "l4v4dur4c004"
COLUNA = "duracao_minutos"


def _config(url: str) -> Config:
    assert url == settings.DATABASE_URL and "loja.db" in url
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    return cfg


@pytest.fixture
def banco(tmp_path, monkeypatch):
    """Loja em l4v4ag3nd003, com servicos cadastrados (sem a coluna)."""
    url = f"sqlite:///{tmp_path / 'loja.db'}"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    engine = sa.create_engine(url)
    with engine.begin() as conn:
        conn.execute(sa.text(
            "CREATE TABLE servicos (id INTEGER PRIMARY KEY, descricao VARCHAR(255) NOT NULL, "
            "valor INTEGER NOT NULL, ativo BOOLEAN NOT NULL)"
        ))
        conn.execute(sa.text("INSERT INTO servicos (descricao, valor, ativo) VALUES ('Troca de tela', 30000, 1)"))
    command.stamp(_config(url), REVISAO_ANTERIOR)
    yield url, engine
    engine.dispose()


def _colunas(engine) -> dict[str, dict]:
    engine.dispose()  # descarta o schema em cache
    return {c["name"]: c for c in sa.inspect(engine).get_columns("servicos")}


def test_banco_antigo_ganha_a_coluna_nula_sem_perder_servico(banco):
    url, engine = banco
    command.upgrade(_config(url), REVISAO)
    colunas = _colunas(engine)
    assert COLUNA in colunas and colunas[COLUNA]["nullable"]
    with engine.connect() as conn:
        linha = conn.execute(sa.text(f"SELECT descricao, valor, {COLUNA} FROM servicos")).one()
    assert tuple(linha) == ("Troca de tela", 30000, None)


def test_coluna_ja_criada_pelo_create_all_nao_quebra(banco):
    url, engine = banco
    with engine.begin() as conn:
        conn.execute(sa.text(f"ALTER TABLE servicos ADD COLUMN {COLUNA} INTEGER"))
    command.upgrade(_config(url), REVISAO)  # não pode levantar "duplicate column"
    assert COLUNA in _colunas(engine)


def test_downgrade_remove_a_coluna_e_mantem_os_dados(banco):
    url, engine = banco
    command.upgrade(_config(url), REVISAO)
    command.downgrade(_config(url), REVISAO_ANTERIOR)
    assert COLUNA not in _colunas(engine)
    with engine.connect() as conn:
        assert conn.execute(sa.text("SELECT count(*) FROM servicos")).scalar() == 1
