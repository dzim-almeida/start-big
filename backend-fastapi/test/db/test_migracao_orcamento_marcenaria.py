# ---------------------------------------------------------------------------
# ARQUIVO: test/db/test_migracao_orcamento_marcenaria.py
# DESCRICAO: A migracao 683ff38df873 (Spec 06A da marcenaria) num banco de loja.
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
from app.db.base import Base

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REVISAO_ANTERIOR = "608dc99a8616"          # a head antes da Spec 06A (Spec 04A)
REVISAO = "683ff38df873"
TABELAS = (
    "marcenaria_orcamentos", "marcenaria_orcamento_rt", "marcenaria_ambientes", "marcenaria_moveis",
    "marcenaria_movel_insumos", "marcenaria_orcamento_anexos", "marcenaria_eventos",
)


def _config(url: str) -> Config:
    """Config do Alembic apontada para o banco temporario (e so para ele)."""
    assert url == settings.DATABASE_URL and "loja.db" in url
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    return cfg


@pytest.fixture
def banco(tmp_path, monkeypatch):
    """Banco de loja de antes da Spec 06A: so as tabelas que o orcamento referencia."""
    url = f"sqlite:///{tmp_path / 'loja.db'}"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    engine = sa.create_engine(url)
    with engine.begin() as conn:
        for tabela in ("clientes", "funcionarios", "objetos_servico", "ordens_servico", "fornecedores", "produtos"):
            conn.execute(sa.text(f"CREATE TABLE {tabela} (id INTEGER PRIMARY KEY, nome VARCHAR(50))"))
        conn.execute(sa.text("INSERT INTO clientes (nome) VALUES ('Dona Marta')"))
    command.stamp(_config(url), REVISAO_ANTERIOR)        # "este banco esta na head antiga"
    yield url, engine
    engine.dispose()


def _inspector(engine) -> sa.Inspector:
    """Inspector numa conexao nova (o Alembic mexeu no banco por outra engine)."""
    engine.dispose()
    return sa.inspect(engine)


def test_banco_antigo_ganha_as_tabelas_iguais_aos_models(banco):
    url, engine = banco

    command.upgrade(_config(url), REVISAO)

    insp = _inspector(engine)
    for tabela in TABELAS:
        assert insp.has_table(tabela), tabela
        # A migracao e uma foto dos models de HOJE: mesmas colunas.
        colunas = {c["name"] for c in insp.get_columns(tabela)}
        assert colunas == set(Base.metadata.tables[tabela].columns.keys()), tabela
    unicos = insp.get_unique_constraints("marcenaria_orcamentos")
    assert [u["column_names"] for u in unicos] == [["codigo", "versao"]]
    with engine.connect() as conn:                       # dados antigos intactos
        assert conn.execute(sa.text("SELECT nome FROM clientes")).scalar() == "Dona Marta"


def test_tabelas_ja_criadas_pelo_create_all_nao_quebram(banco):
    """O startup roda create_all ANTES das migracoes."""
    url, engine = banco
    with engine.begin() as conn:
        conn.execute(sa.text("CREATE TABLE marcenaria_orcamentos (id INTEGER PRIMARY KEY, codigo VARCHAR(20))"))
        conn.execute(sa.text("CREATE TABLE marcenaria_eventos (id INTEGER PRIMARY KEY)"))

    command.upgrade(_config(url), REVISAO)              # nao pode levantar "already exists"

    insp = _inspector(engine)
    assert all(insp.has_table(t) for t in TABELAS)
    # A que ja existia ficou como estava (a migracao nao mexe no que existe).
    assert {c["name"] for c in insp.get_columns("marcenaria_eventos")} == {"id"}


def test_downgrade_remove_as_tabelas(banco):
    url, engine = banco
    command.upgrade(_config(url), REVISAO)

    command.downgrade(_config(url), REVISAO_ANTERIOR)

    insp = _inspector(engine)
    assert not any(insp.has_table(t) for t in TABELAS)
    assert insp.has_table("clientes")
