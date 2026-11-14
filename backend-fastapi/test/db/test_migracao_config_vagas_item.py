# ---------------------------------------------------------------------------
# ARQUIVO: test/db/test_migracao_config_vagas_item.py
# DESCRIÇÃO: A migration l4v4v4g4s005 — configuracoes_os.vagas_agenda e
#            configuracoes_os.item_os_abre_em, num banco de loja que já tem a
#            configuração de OS gravada.
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
REVISAO_ANTERIOR = "l4v4dur4c004"
REVISAO = "l4v4v4g4s005"


def _config(url: str) -> Config:
    assert url == settings.DATABASE_URL and "loja.db" in url
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    return cfg


@pytest.fixture
def banco(tmp_path, monkeypatch):
    """Loja em l4v4dur4c004, com a configuração de OS já gravada (sem as colunas)."""
    url = f"sqlite:///{tmp_path / 'loja.db'}"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    engine = sa.create_engine(url)
    with engine.begin() as conn:
        conn.execute(sa.text(
            "CREATE TABLE configuracoes_os (id INTEGER PRIMARY KEY, empresa_id INTEGER NOT NULL, "
            "prazo_abandono_dias INTEGER NOT NULL)"
        ))
        conn.execute(sa.text("INSERT INTO configuracoes_os (empresa_id, prazo_abandono_dias) VALUES (1, 45)"))
    command.stamp(_config(url), REVISAO_ANTERIOR)
    yield url, engine
    engine.dispose()


def _colunas(engine) -> set[str]:
    engine.dispose()  # descarta o schema em cache
    return {c["name"] for c in sa.inspect(engine).get_columns("configuracoes_os")}


def test_banco_antigo_ganha_as_colunas_com_o_comportamento_de_sempre(banco):
    url, engine = banco
    command.upgrade(_config(url), REVISAO)
    with engine.connect() as conn:
        linha = conn.execute(sa.text(
            "SELECT prazo_abandono_dias, vagas_agenda, item_os_abre_em FROM configuracoes_os")).one()
    assert tuple(linha) == (45, 0, "SERVICO")


def test_coluna_ja_criada_pelo_create_all_nao_quebra(banco):
    url, engine = banco
    with engine.begin() as conn:
        conn.execute(sa.text("ALTER TABLE configuracoes_os ADD COLUMN vagas_agenda INTEGER NOT NULL DEFAULT 0"))
    command.upgrade(_config(url), REVISAO)  # não pode levantar "duplicate column"
    assert {"vagas_agenda", "item_os_abre_em"} <= _colunas(engine)


def test_downgrade_remove_as_colunas_e_mantem_os_dados(banco):
    url, engine = banco
    command.upgrade(_config(url), REVISAO)
    command.downgrade(_config(url), REVISAO_ANTERIOR)
    assert not ({"vagas_agenda", "item_os_abre_em"} & _colunas(engine))
    with engine.connect() as conn:
        assert conn.execute(sa.text("SELECT prazo_abandono_dias FROM configuracoes_os")).scalar() == 45
