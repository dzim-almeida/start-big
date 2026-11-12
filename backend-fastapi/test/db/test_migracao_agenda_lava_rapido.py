# ---------------------------------------------------------------------------
# ARQUIVO: test/db/test_migracao_agenda_lava_rapido.py
# DESCRICAO: A migracao l4v4ag3nd003 (Spec 08A do lava-rapido) num banco de loja.
#
# ⚠️ alembic/env.py le `settings.DATABASE_URL`; o fixture redireciona para o
# tmp_path e o teste se recusa a rodar fora dele. Nunca toca o banco real.
# ---------------------------------------------------------------------------

import os

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from app.core.config import settings

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REVISAO_ANTERIOR = "l4v4ex3c0002"          # lavadores (Spec 10A)
REVISAO = "l4v4ag3nd003"
TABELA = "agendamentos"


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
        conn.execute(sa.text("CREATE TABLE clientes (id INTEGER PRIMARY KEY)"))
        conn.execute(sa.text("CREATE TABLE portes_veiculo (id INTEGER PRIMARY KEY)"))
    command.stamp(_config(url), REVISAO_ANTERIOR)
    yield url, engine
    engine.dispose()


def _inspector(engine) -> sa.Inspector:
    engine.dispose()
    return sa.inspect(engine)


def test_banco_antigo_ganha_a_tabela(banco):
    url, engine = banco
    command.upgrade(_config(url), REVISAO)
    colunas = {c["name"] for c in _inspector(engine).get_columns(TABELA)}
    assert {"inicio", "cliente_nome", "placa", "servicos", "situacao", "numero_os"} <= colunas


def test_ja_criada_pelo_create_all_nao_quebra(banco):
    url, engine = banco
    with engine.begin() as conn:
        conn.execute(sa.text(f"CREATE TABLE {TABELA} (id INTEGER PRIMARY KEY)"))
    command.upgrade(_config(url), REVISAO)
    assert _inspector(engine).has_table(TABELA)


def test_downgrade_e_upgrade_de_novo(banco):
    url, engine = banco
    command.upgrade(_config(url), REVISAO)
    command.downgrade(_config(url), REVISAO_ANTERIOR)
    assert not _inspector(engine).has_table(TABELA)
    command.upgrade(_config(url), REVISAO)
    assert _inspector(engine).has_table(TABELA)
