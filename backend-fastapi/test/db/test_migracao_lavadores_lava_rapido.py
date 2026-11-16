# ---------------------------------------------------------------------------
# ARQUIVO: test/db/test_migracao_lavadores_lava_rapido.py
# DESCRICAO: A migracao l4v4ex3c0002 (Spec 10A do lava-rapido) num banco de loja.
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
REVISAO_ANTERIOR = "l4v4p0r7e001"          # portes (Spec 02A)
REVISAO = "l4v4ex3c0002"
TABELA = "ordem_servico_executores"


def _config(url: str) -> Config:
    assert url == settings.DATABASE_URL and "loja.db" in url
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    return cfg


@pytest.fixture
def banco(tmp_path, monkeypatch):
    """Loja de antes da Spec 10A: cargos e funcionarios com comissao configurada."""
    url = f"sqlite:///{tmp_path / 'loja.db'}"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    engine = sa.create_engine(url)
    with engine.begin() as conn:
        conn.execute(sa.text(
            "CREATE TABLE cargos (id INTEGER PRIMARY KEY, nome VARCHAR(50), "
            "comissao_servico_percentual INTEGER, comissao_modo VARCHAR(10))"
        ))
        conn.execute(sa.text(
            "CREATE TABLE funcionarios (id INTEGER PRIMARY KEY, nome VARCHAR(100), cargo_id INTEGER, "
            "comissao_modo VARCHAR(10))"
        ))
        conn.execute(sa.text("CREATE TABLE ordens_servico (id INTEGER PRIMARY KEY, numero_os VARCHAR(30))"))
        conn.execute(sa.text("INSERT INTO cargos (nome, comissao_servico_percentual, comissao_modo) VALUES ('Técnico', 500, 'meta')"))
        conn.execute(sa.text("INSERT INTO funcionarios (nome, cargo_id) VALUES ('Alan', 1)"))
    command.stamp(_config(url), REVISAO_ANTERIOR)
    yield url, engine
    engine.dispose()


def _inspector(engine) -> sa.Inspector:
    engine.dispose()
    return sa.inspect(engine)


def _cargos(engine):
    with engine.connect() as conn:
        return [tuple(l) for l in conn.execute(sa.text(
            "SELECT id, nome, comissao_servico_percentual, comissao_modo FROM cargos"))]


def test_banco_antigo_ganha_tabela_e_colunas_sem_tocar_nos_dados(banco):
    url, engine = banco
    antes = _cargos(engine)
    command.upgrade(_config(url), REVISAO)

    insp = _inspector(engine)
    assert {c["name"] for c in insp.get_columns(TABELA)} == {"id", "ordem_servico_id", "funcionario_id"}
    for tabela in ("cargos", "funcionarios"):
        assert "comissao_divisao" in {c["name"] for c in insp.get_columns(tabela)}, tabela
    assert _cargos(engine) == antes                       # comissao de quem ja roda intacta
    with engine.connect() as conn:                        # nasce NULL = 'dividir'
        assert conn.execute(sa.text("SELECT comissao_divisao FROM cargos")).scalar() is None


def test_ja_criado_pelo_create_all_nao_quebra(banco):
    url, engine = banco
    with engine.begin() as conn:
        conn.execute(sa.text(f"CREATE TABLE {TABELA} (id INTEGER PRIMARY KEY)"))
        conn.execute(sa.text("ALTER TABLE cargos ADD COLUMN comissao_divisao VARCHAR(10)"))
    command.upgrade(_config(url), REVISAO)                # nao pode levantar "already exists"
    insp = _inspector(engine)
    assert "comissao_divisao" in {c["name"] for c in insp.get_columns("funcionarios")}


def test_downgrade_e_upgrade_de_novo(banco):
    url, engine = banco
    command.upgrade(_config(url), REVISAO)
    command.downgrade(_config(url), REVISAO_ANTERIOR)
    insp = _inspector(engine)
    assert not insp.has_table(TABELA)
    assert "comissao_divisao" not in {c["name"] for c in insp.get_columns("cargos")}
    assert _cargos(engine)                                 # cargos continuam la
    command.upgrade(_config(url), REVISAO)
    assert _inspector(engine).has_table(TABELA)
