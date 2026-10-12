# ---------------------------------------------------------------------------
# ARQUIVO: test/db/test_migracao_terceirizados_marcenaria.py
# DESCRICAO: A migracao 642b2e8f79fa (Spec 11A da marcenaria) num banco de loja.
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
REVISAO_ANTERIOR = "195109da93f7"          # a head antes da Spec 11A (Spec 09A)
REVISAO = "642b2e8f79fa"
COLUNAS_NOVAS = {"pedido_compra_id", "terc_situacao", "terc_pedido", "terc_enviado_em", "terc_previsao",
                 "terc_recebido_em", "terc_conferido_em", "terc_problema"}


def _config(url: str) -> Config:
    """Config do Alembic apontada para o banco temporario (e so para ele)."""
    assert url == settings.DATABASE_URL and "loja.db" in url
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    return cfg


@pytest.fixture
def banco(tmp_path, monkeypatch):
    """Loja com um movel ja aprovado, na head antiga."""
    url = f"sqlite:///{tmp_path / 'loja.db'}"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    engine = sa.create_engine(url)
    with engine.begin() as conn:
        conn.execute(sa.text("CREATE TABLE pedidos_compra (id INTEGER PRIMARY KEY)"))
        conn.execute(sa.text("CREATE TABLE marcenaria_moveis (id INTEGER PRIMARY KEY, nome VARCHAR(120), aprovado BOOLEAN)"))
        conn.execute(sa.text("INSERT INTO marcenaria_moveis (nome, aprovado) VALUES ('Torre Quente', 1)"))
    command.stamp(_config(url), REVISAO_ANTERIOR)
    yield url, engine
    engine.dispose()


def _inspector(engine) -> sa.Inspector:
    engine.dispose()
    return sa.inspect(engine)


def test_colunas_e_indices_novos_e_o_movel_fica_a_pedir(banco):
    url, engine = banco

    command.upgrade(_config(url), REVISAO)

    insp = _inspector(engine)
    assert COLUNAS_NOVAS <= {c["name"] for c in insp.get_columns("marcenaria_moveis")}
    assert {"ix_marcenaria_moveis_pedido", "ix_marcenaria_moveis_terc"} <= {i["name"] for i in insp.get_indexes("marcenaria_moveis")}
    with engine.connect() as conn:
        # O movel que ja existia continua igual, com tudo nulo (= "A pedir").
        linha = conn.execute(sa.text("SELECT nome, aprovado, pedido_compra_id, terc_situacao FROM marcenaria_moveis")).one()
        assert tuple(linha) == ("Torre Quente", 1, None, None)


def test_colunas_ja_criadas_nao_quebram(banco):
    url, engine = banco
    with engine.begin() as conn:
        conn.execute(sa.text("ALTER TABLE marcenaria_moveis ADD COLUMN terc_situacao VARCHAR(10)"))
        conn.execute(sa.text("CREATE INDEX ix_marcenaria_moveis_pedido ON marcenaria_moveis (id)"))

    command.upgrade(_config(url), REVISAO)                         # nem "duplicate column" nem "index exists"

    assert COLUNAS_NOVAS <= {c["name"] for c in _inspector(engine).get_columns("marcenaria_moveis")}


def test_banco_completo_fica_igual_aos_models(tmp_path, monkeypatch):
    """Tabelas de antes + todas as migracoes da marcenaria = os models de hoje."""
    url = f"sqlite:///{tmp_path / 'loja.db'}"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    engine = sa.create_engine(url)
    with engine.begin() as conn:
        for tabela in ("empresas", "clientes", "funcionarios", "objetos_servico", "ordens_servico", "fornecedores",
                       "produtos", "ordem_servico_itens", "contas_pagar", "planos_conta", "pedidos_compra"):
            conn.execute(sa.text(f"CREATE TABLE {tabela} (id INTEGER PRIMARY KEY)"))
    command.stamp(_config(url), "d7a3e9c2f418")                      # antes da Spec 04A
    command.upgrade(_config(url), "head")

    insp = _inspector(engine)
    for tabela in ("configuracoes_marcenaria", "marcenaria_orcamentos", "marcenaria_moveis", "marcenaria_orcamento_rt"):
        assert {c["name"] for c in insp.get_columns(tabela)} == set(Base.metadata.tables[tabela].columns.keys()), tabela
    engine.dispose()


def test_downgrade_tira_as_colunas(banco):
    url, engine = banco
    command.upgrade(_config(url), REVISAO)

    command.downgrade(_config(url), REVISAO_ANTERIOR)

    insp = _inspector(engine)
    assert not COLUNAS_NOVAS & {c["name"] for c in insp.get_columns("marcenaria_moveis")}
    assert "ix_marcenaria_moveis_terc" not in {i["name"] for i in insp.get_indexes("marcenaria_moveis")}
    with engine.connect() as conn:
        assert conn.execute(sa.text("SELECT nome FROM marcenaria_moveis")).scalar() == "Torre Quente"
