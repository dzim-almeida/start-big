# ---------------------------------------------------------------------------
# ARQUIVO: test/db/test_migracao_ultimo_horario_visto.py
# DESCRICAO: LIC-02 (CA-06) -- a migracao l1c02r3l0g10 acrescenta
#            configuracoes_licenca.ultimo_horario_visto uma vez, num banco de
#            loja com a licenca ja ativada, e rodar de novo nao faz nada.
#
# alembic/env.py le `settings.DATABASE_URL`; o fixture redireciona para o
# tmp_path e o teste se recusa a rodar fora dele (nunca no banco da loja).
# ---------------------------------------------------------------------------

import os

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from app.core.config import settings

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REVISAO_ANTERIOR = "l4v4v4g4s005"
REVISAO = "l1c02r3l0g10"
COLUNA = "ultimo_horario_visto"


def _config(url: str) -> Config:
    # Trava de seguranca: so roda no banco descartavel do tmp_path.
    assert url == settings.DATABASE_URL and "loja.db" in url
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    return cfg


@pytest.fixture
def banco(tmp_path, monkeypatch):
    """Loja em l4v4v4g4s005, com a licenca ativada (tabela sem a coluna nova)."""
    url = f"sqlite:///{tmp_path / 'loja.db'}"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    engine = sa.create_engine(url)
    with engine.begin() as conn:
        conn.execute(sa.text(
            "CREATE TABLE configuracoes_licenca (id INTEGER PRIMARY KEY, "
            "licenca_id VARCHAR(36) NOT NULL, token TEXT NOT NULL)"
        ))
        conn.execute(sa.text(
            "INSERT INTO configuracoes_licenca (licenca_id, token) VALUES ('lic-abc', 'dpapi:v1:x')"
        ))
    command.stamp(_config(url), REVISAO_ANTERIOR)
    yield url, engine
    engine.dispose()


def _colunas(engine) -> dict[str, dict]:
    engine.dispose()  # descarta o schema em cache
    return {c["name"]: c for c in sa.inspect(engine).get_columns("configuracoes_licenca")}


def test_banco_antigo_ganha_a_coluna_nula_sem_perder_a_licenca(banco):
    url, engine = banco

    command.upgrade(_config(url), REVISAO)

    colunas = _colunas(engine)
    assert COLUNA in colunas and colunas[COLUNA]["nullable"]
    with engine.connect() as conn:
        linha = conn.execute(sa.text(
            f"SELECT licenca_id, token, {COLUNA} FROM configuracoes_licenca"
        )).one()
    assert tuple(linha) == ("lic-abc", "dpapi:v1:x", None)


def test_rodar_de_novo_com_a_coluna_ja_criada_nao_faz_nada(banco):
    """O create_all do startup pode ter criado a coluna antes (banco novo)."""
    url, engine = banco
    with engine.begin() as conn:
        conn.execute(sa.text(f"ALTER TABLE configuracoes_licenca ADD COLUMN {COLUNA} DATETIME"))

    command.upgrade(_config(url), REVISAO)   # nao pode explodir com "duplicate column"

    assert COLUNA in _colunas(engine)


def test_downgrade_remove_so_a_coluna_e_upgrade_repete(banco):
    url, engine = banco
    command.upgrade(_config(url), REVISAO)

    command.downgrade(_config(url), REVISAO_ANTERIOR)
    assert COLUNA not in _colunas(engine)

    command.upgrade(_config(url), REVISAO)
    assert COLUNA in _colunas(engine)
