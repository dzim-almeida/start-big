# ---------------------------------------------------------------------------
# ARQUIVO: test/db/test_migracao_numeracao_confirmada.py
# DESCRIÇÃO: A migration s2t3u4v5w6x7 num banco de loja já em operação.
#
# Roda a migration ISOLADA (upgrade de r1s2t3u4v5w6 para s2t3u4v5w6x7) num
# SQLite de arquivo temporário, em três cenários: banco antigo sem a coluna,
# banco onde o create_all() já criou a coluna, e loja com nota autorizada.
#
# ⚠️ ARMADILHA: alembic/env.py IGNORA `sqlalchemy.url` do Config e lê
# `settings.DATABASE_URL` -- que nesta máquina aponta para o banco real da
# loja. A primeira versão deste teste carimbou e migrou o banco de verdade.
# Por isso o fixture redireciona `settings.DATABASE_URL` e o teste se recusa
# a rodar se a URL não estiver no diretório temporário.
# ---------------------------------------------------------------------------

import os

import pytest
import sqlalchemy as sa
from alembic.config import Config
from alembic import command

from app.core.config import settings

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REVISAO_ANTERIOR = "r1s2t3u4v5w6"
REVISAO = "s2t3u4v5w6x7"


def _config(url: str) -> Config:
    assert url == settings.DATABASE_URL and "loja.db" in url, (
        "env.py usa settings.DATABASE_URL; sem o redirecionamento a migration "
        "rodaria no banco real"
    )
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    return cfg


@pytest.fixture
def banco(tmp_path, monkeypatch):
    """Banco 'antigo': só as tabelas que a migration toca, sem a coluna nova."""
    url = f"sqlite:///{tmp_path / 'loja.db'}"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    engine = sa.create_engine(url)
    with engine.begin() as conn:
        conn.execute(sa.text(
            "CREATE TABLE empresa_fiscal_settings ("
            " id INTEGER PRIMARY KEY, empresa_id INTEGER NOT NULL,"
            " serie_nfe INTEGER NOT NULL DEFAULT 1, ultimo_numero_nfe INTEGER NOT NULL DEFAULT 0)"
        ))
        conn.execute(sa.text(
            "CREATE TABLE documento_fiscal (id INTEGER PRIMARY KEY, status VARCHAR(15) NOT NULL)"
        ))
        conn.execute(sa.text("INSERT INTO empresa_fiscal_settings (empresa_id) VALUES (1)"))
    command.stamp(_config(url), REVISAO_ANTERIOR)
    yield url, engine
    engine.dispose()


def _coluna(engine) -> list:
    with engine.connect() as conn:
        return conn.execute(sa.text(
            "SELECT numeracao_confirmada FROM empresa_fiscal_settings"
        )).scalars().all()


def test_banco_antigo_ganha_a_coluna_em_false(banco):
    url, engine = banco
    command.upgrade(_config(url), REVISAO)
    assert _coluna(engine) == [0]


def test_loja_com_nota_autorizada_nasce_confirmada(banco):
    url, engine = banco
    with engine.begin() as conn:
        conn.execute(sa.text("INSERT INTO documento_fiscal (status) VALUES ('AUTORIZADA')"))
    command.upgrade(_config(url), REVISAO)
    assert _coluna(engine) == [1]


def test_nota_rejeitada_nao_conta_como_historico(banco):
    url, engine = banco
    with engine.begin() as conn:
        conn.execute(sa.text("INSERT INTO documento_fiscal (status) VALUES ('REJEITADA')"))
    command.upgrade(_config(url), REVISAO)
    assert _coluna(engine) == [0]


def test_coluna_ja_criada_pelo_create_all_nao_quebra(banco):
    """Cenário real do startup: create_all() roda antes e já cria a coluna."""
    url, engine = banco
    with engine.begin() as conn:
        conn.execute(sa.text(
            "ALTER TABLE empresa_fiscal_settings ADD COLUMN numeracao_confirmada BOOLEAN NOT NULL DEFAULT 0"
        ))
        conn.execute(sa.text("INSERT INTO documento_fiscal (status) VALUES ('AUTORIZADA')"))
    command.upgrade(_config(url), REVISAO)  # não pode levantar "duplicate column"
    assert _coluna(engine) == [1]
