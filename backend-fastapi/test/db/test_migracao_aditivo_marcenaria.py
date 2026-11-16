# ---------------------------------------------------------------------------
# ARQUIVO: test/db/test_migracao_aditivo_marcenaria.py
# DESCRICAO: A migracao a7d1t1v0os01 (aditivo do orcamento, remodelacao item 20)
#            num banco de loja. Nunca toca o banco real da maquina (mesmo
#            padrao das outras migracoes da marcenaria).
# ---------------------------------------------------------------------------

import os

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from app.core.config import settings

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REVISAO_ANTERIOR = "2c4df92b1412"          # a head antes do aditivo (Spec 13A)
REVISAO = "a7d1t1v0os01"


def _config(url: str) -> Config:
    """Config do Alembic apontada para o banco temporario (e so para ele)."""
    assert url == settings.DATABASE_URL and "loja.db" in url
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    return cfg


@pytest.fixture
def banco(tmp_path, monkeypatch):
    """Loja com um orcamento aprovado, na head de antes do aditivo."""
    url = f"sqlite:///{tmp_path / 'loja.db'}"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    engine = sa.create_engine(url)
    with engine.begin() as conn:
        conn.execute(sa.text("CREATE TABLE ordens_servico (id INTEGER PRIMARY KEY)"))
        conn.execute(sa.text("INSERT INTO ordens_servico (id) VALUES (7)"))
        conn.execute(sa.text(
            "CREATE TABLE marcenaria_orcamentos (id INTEGER PRIMARY KEY, codigo VARCHAR(20), status VARCHAR(12), "
            "os_id INTEGER REFERENCES ordens_servico (id))"
        ))
        conn.execute(sa.text("INSERT INTO marcenaria_orcamentos (codigo, status, os_id) VALUES ('ORC-2026-000001', 'APROVADO', 7)"))
    command.stamp(_config(url), REVISAO_ANTERIOR)
    yield url, engine
    engine.dispose()


def _colunas(engine) -> set[str]:
    engine.dispose()                                     # o Alembic mexeu no banco por outra engine
    return {c["name"] for c in sa.inspect(engine).get_columns("marcenaria_orcamentos")}


def test_coluna_nova_e_orcamentos_antigos_continuam_comuns(banco):
    url, engine = banco

    command.upgrade(_config(url), REVISAO)

    assert "aditivo_os_id" in _colunas(engine)
    with engine.connect() as conn:
        # O orcamento que ja existia e COMUM (nao vira aditivo) e o resto fica como estava.
        assert tuple(conn.execute(sa.text("SELECT codigo, os_id, aditivo_os_id FROM marcenaria_orcamentos")).one()) == \
            ("ORC-2026-000001", 7, None)


def test_coluna_ja_criada_pelo_create_all_nao_quebra(banco):
    url, engine = banco
    with engine.begin() as conn:
        conn.execute(sa.text("ALTER TABLE marcenaria_orcamentos ADD COLUMN aditivo_os_id INTEGER"))

    command.upgrade(_config(url), REVISAO)              # nao pode levantar "duplicate column"

    assert "aditivo_os_id" in _colunas(engine)


def test_downgrade_tira_a_coluna(banco):
    url, engine = banco
    command.upgrade(_config(url), REVISAO)

    command.downgrade(_config(url), REVISAO_ANTERIOR)

    assert "aditivo_os_id" not in _colunas(engine)
