# ---------------------------------------------------------------------------
# ARQUIVO: test/db/test_migracao_rt_marcenaria.py
# DESCRICAO: A migracao 195109da93f7 (Spec 09A da marcenaria) num banco de loja.
#            Nunca toca o banco real da maquina (mesmo padrao das outras).
# ---------------------------------------------------------------------------

import os

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from app.core.config import settings
from app.db.base import Base

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REVISAO_ANTERIOR = "971eb6cc5a33"          # a head antes da Spec 09A (Spec 08A)
REVISAO = "195109da93f7"


def _config(url: str) -> Config:
    """Config do Alembic apontada para o banco temporario (e so para ele)."""
    assert url == settings.DATABASE_URL and "loja.db" in url
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    return cfg


@pytest.fixture
def banco(tmp_path, monkeypatch):
    """Loja com a configuracao da marcenaria preenchida, na head antiga."""
    url = f"sqlite:///{tmp_path / 'loja.db'}"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    engine = sa.create_engine(url)
    with engine.begin() as conn:
        # As tabelas que as colunas novas referenciam (existem em toda loja).
        conn.execute(sa.text("CREATE TABLE contas_pagar (id INTEGER PRIMARY KEY)"))
        conn.execute(sa.text("CREATE TABLE planos_conta (id INTEGER PRIMARY KEY)"))
        conn.execute(sa.text("CREATE TABLE configuracoes_marcenaria (id INTEGER PRIMARY KEY, markup_padrao_bp INTEGER)"))
        conn.execute(sa.text("INSERT INTO configuracoes_marcenaria (markup_padrao_bp) VALUES (9000)"))
        conn.execute(sa.text("CREATE TABLE marcenaria_orcamento_rt (id INTEGER PRIMARY KEY, rt_bp INTEGER)"))
        conn.execute(sa.text("INSERT INTO marcenaria_orcamento_rt (rt_bp) VALUES (800)"))
    command.stamp(_config(url), REVISAO_ANTERIOR)
    yield url, engine
    engine.dispose()


def _inspector(engine) -> sa.Inspector:
    engine.dispose()
    return sa.inspect(engine)


def test_colunas_novas_e_prazo_padrao_30(banco):
    url, engine = banco

    command.upgrade(_config(url), REVISAO)

    insp = _inspector(engine)
    assert {"rt_vencimento_dias", "rt_plano_conta_id"} <= {c["name"] for c in insp.get_columns("configuracoes_marcenaria")}
    assert "conta_pagar_id" in {c["name"] for c in insp.get_columns("marcenaria_orcamento_rt")}
    with engine.connect() as conn:
        # A loja que ja existia ganha o prazo padrao; o resto fica como estava.
        assert tuple(conn.execute(sa.text("SELECT markup_padrao_bp, rt_vencimento_dias FROM configuracoes_marcenaria")).one()) == (9000, 30)
        assert conn.execute(sa.text("SELECT rt_bp, conta_pagar_id FROM marcenaria_orcamento_rt")).one() == (800, None)


def test_colunas_ja_criadas_nao_quebram(banco):
    url, engine = banco
    with engine.begin() as conn:
        conn.execute(sa.text("ALTER TABLE configuracoes_marcenaria ADD COLUMN rt_vencimento_dias INTEGER NOT NULL DEFAULT 30"))

    command.upgrade(_config(url), REVISAO)                         # nao pode levantar "duplicate column"

    assert "rt_plano_conta_id" in {c["name"] for c in _inspector(engine).get_columns("configuracoes_marcenaria")}


def test_banco_completo_fica_igual_aos_models(tmp_path, monkeypatch):
    """Tabelas de antes + todas as migracoes da marcenaria = os models de hoje."""
    url = f"sqlite:///{tmp_path / 'loja.db'}"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    engine = sa.create_engine(url)
    with engine.begin() as conn:
        for tabela in ("empresas", "clientes", "funcionarios", "objetos_servico", "ordens_servico", "fornecedores",
                       "produtos", "ordem_servico_itens", "contas_pagar", "planos_conta"):
            conn.execute(sa.text(f"CREATE TABLE {tabela} (id INTEGER PRIMARY KEY)"))
    command.stamp(_config(url), "d7a3e9c2f418")                      # antes da Spec 04A
    command.upgrade(_config(url), REVISAO)

    insp = _inspector(engine)
    for tabela in ("configuracoes_marcenaria", "marcenaria_orcamento_rt", "marcenaria_orcamentos", "marcenaria_moveis"):
        assert {c["name"] for c in insp.get_columns(tabela)} == set(Base.metadata.tables[tabela].columns.keys()), tabela
    engine.dispose()


def test_downgrade_tira_as_colunas(banco):
    url, engine = banco
    command.upgrade(_config(url), REVISAO)

    command.downgrade(_config(url), REVISAO_ANTERIOR)

    insp = _inspector(engine)
    assert "rt_vencimento_dias" not in {c["name"] for c in insp.get_columns("configuracoes_marcenaria")}
    assert "conta_pagar_id" not in {c["name"] for c in insp.get_columns("marcenaria_orcamento_rt")}
