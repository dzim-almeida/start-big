# ---------------------------------------------------------------------------
# ARQUIVO: test/db/test_migracao_perfil_no_produto.py
# DESCRIÇÃO: A migration w6x7y8z9a0b1 (TASK006) — perfil_tributario_id em
#            produto_fiscal, num banco de loja com produtos cadastrados.
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
REVISAO_ANTERIOR = "v5w6x7y8z9a0"
REVISAO = "w6x7y8z9a0b1"
COLUNA = "perfil_tributario_id"


def _config(url: str) -> Config:
    assert url == settings.DATABASE_URL and "loja.db" in url
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    return cfg


@pytest.fixture
def banco(tmp_path, monkeypatch):
    """Loja em v5w6x7y8z9a0: perfil_tributario existe, produto_fiscal tem linhas."""
    url = f"sqlite:///{tmp_path / 'loja.db'}"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    engine = sa.create_engine(url)
    with engine.begin() as conn:
        conn.execute(sa.text("CREATE TABLE empresas (id INTEGER PRIMARY KEY)"))
        conn.execute(sa.text(
            "CREATE TABLE perfil_tributario (id INTEGER PRIMARY KEY, empresa_id INTEGER NOT NULL, "
            "descricao VARCHAR(120) NOT NULL)"
        ))
        conn.execute(sa.text(
            "CREATE TABLE produto_fiscal (id INTEGER PRIMARY KEY, produto_id INTEGER NOT NULL, ncm VARCHAR(8))"
        ))
        conn.execute(sa.text("INSERT INTO produto_fiscal (produto_id, ncm) VALUES (1, '85171200')"))
    command.stamp(_config(url), REVISAO_ANTERIOR)
    yield url, engine
    engine.dispose()


def _inspector(engine) -> sa.Inspector:
    engine.dispose()  # descarta a conexão com o schema em cache (ver test_migracao_perfil_tributario.py)
    return sa.inspect(engine)


def _colunas(engine) -> dict[str, dict]:
    return {c["name"]: c for c in _inspector(engine).get_columns("produto_fiscal")}


def test_banco_antigo_ganha_a_coluna_nula_com_fk_e_indice(banco):
    url, engine = banco
    command.upgrade(_config(url), REVISAO)

    colunas = _colunas(engine)
    assert COLUNA in colunas and colunas[COLUNA]["nullable"]
    with engine.connect() as conn:
        assert conn.execute(sa.text(f"SELECT {COLUNA} FROM produto_fiscal")).scalar() is None

    # PRAGMA, não o inspector: o parser do SQLAlchemy não lê ON DELETE de uma
    # FK inline acrescentada por ADD COLUMN, mas é o PRAGMA que o SQLite aplica.
    with engine.connect() as conn:
        fks = conn.execute(sa.text("PRAGMA foreign_key_list(produto_fiscal)")).all()
    fk = next(f for f in fks if f[3] == COLUNA)
    assert (fk[2], fk[6]) == ("perfil_tributario", "SET NULL")
    assert "ix_produto_fiscal_perfil_tributario_id" in {i["name"] for i in _inspector(engine).get_indexes("produto_fiscal")}


def test_coluna_ja_criada_pelo_create_all_nao_quebra(banco):
    url, engine = banco
    with engine.begin() as conn:
        conn.execute(sa.text(f"ALTER TABLE produto_fiscal ADD COLUMN {COLUNA} INTEGER"))
    command.upgrade(_config(url), REVISAO)  # não pode levantar "duplicate column"
    assert COLUNA in _colunas(engine)


def test_downgrade_remove_a_coluna(banco):
    url, engine = banco
    command.upgrade(_config(url), REVISAO)
    command.downgrade(_config(url), REVISAO_ANTERIOR)
    assert COLUNA not in _colunas(engine)
    with engine.connect() as conn:  # a linha antiga sobrevive
        assert conn.execute(sa.text("SELECT ncm FROM produto_fiscal")).scalar() == "85171200"
