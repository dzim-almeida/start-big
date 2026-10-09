# ---------------------------------------------------------------------------
# ARQUIVO: test/db/test_migracao_aprovacao_marcenaria.py
# DESCRICAO: A migracao 971eb6cc5a33 (Spec 08A da marcenaria) num banco de loja.
#
# ⚠️ E a unica migracao da marcenaria que toca uma tabela EXISTENTE
# (`ordem_servico_itens`): o teste confere que nenhuma linha muda e que a
# tabela nao e recriada (os itens continuam com o mesmo id e conteudo).
# Nunca toca o banco real da maquina (mesmo padrao das outras migracoes).
# ---------------------------------------------------------------------------

import os

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from app.core.config import settings
from app.db.base import Base

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REVISAO_ANTERIOR = "683ff38df873"          # a head antes da Spec 08A (Spec 06A)
REVISAO = "971eb6cc5a33"


def _config(url: str) -> Config:
    """Config do Alembic apontada para o banco temporario (e so para ele)."""
    assert url == settings.DATABASE_URL and "loja.db" in url
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    return cfg


@pytest.fixture
def banco(tmp_path, monkeypatch):
    """Loja com itens de OS e as tabelas da 06A, na head antiga."""
    url = f"sqlite:///{tmp_path / 'loja.db'}"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    engine = sa.create_engine(url)
    with engine.begin() as conn:
        conn.execute(sa.text("CREATE TABLE ordem_servico_itens (id INTEGER PRIMARY KEY, nome VARCHAR(255), valor_total INTEGER)"))
        conn.execute(sa.text("INSERT INTO ordem_servico_itens (nome, valor_total) VALUES ('Troca de tela', 35000), ('Película', 3000)"))
        conn.execute(sa.text("CREATE TABLE marcenaria_moveis (id INTEGER PRIMARY KEY, nome VARCHAR(120))"))
        conn.execute(sa.text("CREATE TABLE marcenaria_orcamentos (id INTEGER PRIMARY KEY, codigo VARCHAR(20), os_id INTEGER)"))
    command.stamp(_config(url), REVISAO_ANTERIOR)
    yield url, engine
    engine.dispose()


def _inspector(engine) -> sa.Inspector:
    engine.dispose()
    return sa.inspect(engine)


def _itens(engine) -> list[tuple]:
    with engine.connect() as conn:
        return [tuple(l) for l in conn.execute(sa.text("SELECT id, nome, valor_total FROM ordem_servico_itens ORDER BY id"))]


def test_colunas_novas_nulas_e_itens_intactos(banco):
    url, engine = banco
    antes = _itens(engine)

    command.upgrade(_config(url), REVISAO)

    insp = _inspector(engine)
    assert "origem" in {c["name"] for c in insp.get_columns("ordem_servico_itens")}
    assert _itens(engine) == antes                                  # mesmas linhas, mesmos ids
    with engine.connect() as conn:
        assert conn.execute(sa.text("SELECT COUNT(*) FROM ordem_servico_itens WHERE origem IS NOT NULL")).scalar() == 0
    assert "os_item_id" in {c["name"] for c in insp.get_columns("marcenaria_moveis")}
    # O inspetor do SQLAlchemy nao le o ON DELETE de uma coluna criada por
    # ALTER TABLE; o PRAGMA do proprio SQLite le: (.., tabela, de, para, on_update, on_delete, ..).
    with engine.connect() as conn:
        fks = conn.execute(sa.text("PRAGMA foreign_key_list(marcenaria_moveis)")).fetchall()
    assert [(f[2], f[3], f[6]) for f in fks] == [("ordem_servico_itens", "os_item_id", "SET NULL")]
    assert {"instalacao_aprovada", "resumo_aprovado_total_centavos", "resumo_aprovado_sinal_centavos",
            "sinal_recebido_centavos"} <= {c["name"] for c in insp.get_columns("marcenaria_orcamentos")}
    assert "ix_marcenaria_orcamentos_os" in {i["name"] for i in insp.get_indexes("marcenaria_orcamentos")}


def test_colunas_ja_criadas_pelo_create_all_nao_quebram(banco):
    """Instalacao nova: o create_all ja criou as tabelas com as colunas desta spec."""
    url, engine = banco
    with engine.begin() as conn:
        conn.execute(sa.text("ALTER TABLE ordem_servico_itens ADD COLUMN origem VARCHAR(30)"))
        conn.execute(sa.text("ALTER TABLE marcenaria_moveis ADD COLUMN os_item_id INTEGER"))

    command.upgrade(_config(url), REVISAO)                         # nao pode levantar "duplicate column"

    assert "sinal_recebido_centavos" in {c["name"] for c in _inspector(engine).get_columns("marcenaria_orcamentos")}


def test_banco_completo_fica_igual_aos_models(tmp_path, monkeypatch):
    """create_all das tabelas de antes + todas as migracoes da marcenaria = os models de hoje."""
    url = f"sqlite:///{tmp_path / 'loja.db'}"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    engine = sa.create_engine(url)
    with engine.begin() as conn:
        for tabela in ("clientes", "funcionarios", "objetos_servico", "ordens_servico", "fornecedores", "produtos"):
            conn.execute(sa.text(f"CREATE TABLE {tabela} (id INTEGER PRIMARY KEY)"))
        conn.execute(sa.text("CREATE TABLE ordem_servico_itens (id INTEGER PRIMARY KEY)"))
    command.stamp(_config(url), "608dc99a8616")
    command.upgrade(_config(url), REVISAO)

    insp = _inspector(engine)
    for tabela in ("marcenaria_orcamentos", "marcenaria_moveis"):
        assert {c["name"] for c in insp.get_columns(tabela)} == set(Base.metadata.tables[tabela].columns.keys()), tabela
    engine.dispose()


def test_downgrade_tira_as_colunas(banco):
    url, engine = banco
    antes = _itens(engine)
    command.upgrade(_config(url), REVISAO)

    command.downgrade(_config(url), REVISAO_ANTERIOR)

    insp = _inspector(engine)
    assert "origem" not in {c["name"] for c in insp.get_columns("ordem_servico_itens")}
    assert "os_item_id" not in {c["name"] for c in insp.get_columns("marcenaria_moveis")}
    assert _itens(engine) == antes
