# ---------------------------------------------------------------------------
# ARQUIVO: test/db/test_migracao_portes_lava_rapido.py
# DESCRICAO: A migracao l4v4p0r7e001 (Spec 02A do lava-rapido) num banco de loja.
#
# ⚠️ alembic/env.py le `settings.DATABASE_URL`; o fixture redireciona para o
# tmp_path e o teste se recusa a rodar fora dele (mesmo padrao de
# test_migracao_base_marcenaria.py). Nunca toca o banco real da maquina.
# ---------------------------------------------------------------------------

import os

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from app.core.config import settings

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REVISAO_ANTERIOR = "s7f4br1c4c01"          # a head antes da Spec 02A (ST do fabricante CE)
REVISAO = "l4v4p0r7e001"
PORTES = "portes_veiculo"
PRECOS = "servico_precos_porte"


def _config(url: str) -> Config:
    """Config do Alembic apontada para o banco temporario (e so para ele)."""
    assert url == settings.DATABASE_URL and "loja.db" in url
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    return cfg


@pytest.fixture
def banco(tmp_path, monkeypatch):
    """Banco de loja de antes da Spec 02A: servicos cadastrados e nada de porte."""
    url = f"sqlite:///{tmp_path / 'loja.db'}"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    engine = sa.create_engine(url)
    with engine.begin() as conn:
        conn.execute(sa.text(
            "CREATE TABLE servicos (id INTEGER PRIMARY KEY, descricao VARCHAR(255) NOT NULL, "
            "valor INTEGER NOT NULL, ativo BOOLEAN NOT NULL DEFAULT 1)"
        ))
        conn.execute(sa.text("INSERT INTO servicos (descricao, valor) VALUES ('Troca de óleo', 8000), ('Alinhamento', 6000)"))
    command.stamp(_config(url), REVISAO_ANTERIOR)        # "este banco esta na head antiga"
    yield url, engine
    engine.dispose()


def _inspector(engine) -> sa.Inspector:
    """Inspector numa conexao nova (o Alembic mexeu no banco por outra engine)."""
    engine.dispose()
    return sa.inspect(engine)


def _servicos(engine) -> list[tuple]:
    with engine.connect() as conn:
        return [tuple(l) for l in conn.execute(sa.text("SELECT id, descricao, valor, ativo FROM servicos ORDER BY id"))]


def test_banco_antigo_ganha_as_tabelas_e_servicos_ficam_intactos(banco):
    url, engine = banco
    antes = _servicos(engine)

    command.upgrade(_config(url), REVISAO)

    insp = _inspector(engine)
    assert {c["name"] for c in insp.get_columns(PORTES)} == {"id", "tipo_veiculo", "nome", "ordem", "ativo"}
    assert {c["name"] for c in insp.get_columns(PRECOS)} == {
        "id", "servico_id", "porte_id", "valor", "duracao_minutos",
    }
    fks = {fk["referred_table"]: fk["options"].get("ondelete") for fk in insp.get_foreign_keys(PRECOS)}
    assert fks == {"servicos": "CASCADE", PORTES: "CASCADE"}
    assert _servicos(engine) == antes                    # a tabela de servicos nao muda (PR1)
    with engine.connect() as conn:                       # nascem vazias: lista inicial so na 1a leitura
        assert conn.execute(sa.text(f"SELECT COUNT(*) FROM {PORTES}")).scalar() == 0


def test_tabelas_ja_criadas_pelo_create_all_nao_quebram(banco):
    """O startup roda create_all ANTES das migracoes."""
    url, engine = banco
    with engine.begin() as conn:
        conn.execute(sa.text(f"CREATE TABLE {PORTES} (id INTEGER PRIMARY KEY, tipo_veiculo VARCHAR(30))"))
        conn.execute(sa.text(f"CREATE TABLE {PRECOS} (id INTEGER PRIMARY KEY, servico_id INTEGER)"))

    command.upgrade(_config(url), REVISAO)               # nao pode levantar "already exists"

    insp = _inspector(engine)
    assert insp.has_table(PORTES) and insp.has_table(PRECOS)


def test_downgrade_e_upgrade_de_novo(banco):
    url, engine = banco
    command.upgrade(_config(url), REVISAO)
    command.downgrade(_config(url), REVISAO_ANTERIOR)
    insp = _inspector(engine)
    assert not insp.has_table(PORTES) and not insp.has_table(PRECOS)
    assert _servicos(engine)                              # servicos continuam la
    command.upgrade(_config(url), REVISAO)
    assert _inspector(engine).has_table(PRECOS)
