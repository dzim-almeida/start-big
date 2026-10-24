# ---------------------------------------------------------------------------
# ARQUIVO: test/db/test_migracao_faturamento_marcenaria.py
# DESCRICAO: A migracao f4t1m0v3l001 (faturamento dos moveis, F1 do plano
#            docs/marcenaria-faturamento-plano.md) num banco de loja. Nunca
#            toca o banco real da maquina (mesmo padrao das outras).
# ---------------------------------------------------------------------------

import os

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from app.core.config import settings
from app.db.base import Base

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REVISAO_ANTERIOR = "a7d1t1v0os01"          # a head antes do faturamento (aditivo)
REVISAO = "f4t1m0v3l001"
COLUNAS_CONFIG = {"faturamento_modo", "instalacao_modo", "produto_acabado_padrao_id", "produto_acabado_revenda_id"}


def _config(url: str) -> Config:
    """Config do Alembic apontada para o banco temporario (e so para ele)."""
    assert url == settings.DATABASE_URL and "loja.db" in url
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    return cfg


@pytest.fixture
def banco(tmp_path, monkeypatch):
    """Loja com a configuracao da marcenaria e um movel, na head de antes."""
    url = f"sqlite:///{tmp_path / 'loja.db'}"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    engine = sa.create_engine(url)
    with engine.begin() as conn:
        for tabela in ("produtos", "ordens_servico", "movimentacoes_estoque", "documento_fiscal"):
            conn.execute(sa.text(f"CREATE TABLE {tabela} (id INTEGER PRIMARY KEY)"))
        conn.execute(sa.text("CREATE TABLE configuracoes_marcenaria (id INTEGER PRIMARY KEY, markup_padrao_bp INTEGER)"))
        conn.execute(sa.text("INSERT INTO configuracoes_marcenaria (markup_padrao_bp) VALUES (9000)"))
        conn.execute(sa.text("CREATE TABLE marcenaria_moveis (id INTEGER PRIMARY KEY, nome VARCHAR(120))"))
        conn.execute(sa.text("INSERT INTO marcenaria_moveis (nome) VALUES ('Torre Quente')"))
    command.stamp(_config(url), REVISAO_ANTERIOR)
    yield url, engine
    engine.dispose()


def _inspector(engine) -> sa.Inspector:
    engine.dispose()                                     # o Alembic mexeu no banco por outra engine
    return sa.inspect(engine)


def test_colunas_e_tabela_novas_e_a_loja_fica_desligada(banco):
    url, engine = banco

    command.upgrade(_config(url), REVISAO)

    insp = _inspector(engine)
    assert COLUNAS_CONFIG <= {c["name"] for c in insp.get_columns("configuracoes_marcenaria")}
    assert "produto_acabado_id" in {c["name"] for c in insp.get_columns("marcenaria_moveis")}
    assert insp.has_table("marcenaria_moveis_faturamento")
    with engine.connect() as conn:
        # A configuracao que ja existia nasce DESLIGADA: nada muda na loja.
        linha = conn.execute(sa.text(
            "SELECT markup_padrao_bp, faturamento_modo, instalacao_modo, produto_acabado_padrao_id "
            "FROM configuracoes_marcenaria"
        )).one()
        assert tuple(linha) == (9000, "DESLIGADO", "EMBUTIDA", None)
        assert conn.execute(sa.text("SELECT nome, produto_acabado_id FROM marcenaria_moveis")).one() == ("Torre Quente", None)


def test_tabela_e_colunas_ja_criadas_pelo_create_all_nao_quebram(banco):
    url, engine = banco
    with engine.begin() as conn:
        conn.execute(sa.text("ALTER TABLE marcenaria_moveis ADD COLUMN produto_acabado_id INTEGER"))
        conn.execute(sa.text("CREATE TABLE marcenaria_moveis_faturamento (id INTEGER PRIMARY KEY)"))

    command.upgrade(_config(url), REVISAO)              # nem "duplicate column" nem "table exists"

    assert COLUNAS_CONFIG <= {c["name"] for c in _inspector(engine).get_columns("configuracoes_marcenaria")}


def test_tabela_nova_igual_ao_model(banco):
    url, engine = banco

    command.upgrade(_config(url), REVISAO)

    colunas = {c["name"] for c in _inspector(engine).get_columns("marcenaria_moveis_faturamento")}
    assert colunas == set(Base.metadata.tables["marcenaria_moveis_faturamento"].columns.keys())


def test_downgrade_tira_tudo(banco):
    url, engine = banco
    command.upgrade(_config(url), REVISAO)

    command.downgrade(_config(url), REVISAO_ANTERIOR)

    insp = _inspector(engine)
    assert not COLUNAS_CONFIG & {c["name"] for c in insp.get_columns("configuracoes_marcenaria")}
    assert "produto_acabado_id" not in {c["name"] for c in insp.get_columns("marcenaria_moveis")}
    assert not insp.has_table("marcenaria_moveis_faturamento")
    with engine.connect() as conn:
        assert conn.execute(sa.text("SELECT nome FROM marcenaria_moveis")).scalar() == "Torre Quente"


# =========================
# f4t1m0v3l002: entrega futura (F4)
# =========================

def test_entrega_futura_papel_e_simples_faturamento_do_movel(banco):
    url, engine = banco
    command.upgrade(_config(url), "f4t1m0v3l002")

    insp = _inspector(engine)
    assert "papel" in {c["name"] for c in insp.get_columns("documento_fiscal")}
    assert "simples_faturamento_id" in {c["name"] for c in insp.get_columns("marcenaria_moveis")}

    command.downgrade(_config(url), REVISAO)
    insp = _inspector(engine)
    assert "papel" not in {c["name"] for c in insp.get_columns("documento_fiscal")}
    assert "simples_faturamento_id" not in {c["name"] for c in insp.get_columns("marcenaria_moveis")}
