# ---------------------------------------------------------------------------
# ARQUIVO: test/db/test_migracao_base_marcenaria.py
# DESCRICAO: A migracao 608dc99a8616 (Spec 04A da marcenaria) num banco de loja.
#
# ⚠️ alembic/env.py le `settings.DATABASE_URL`; o fixture redireciona para o
# tmp_path e o teste se recusa a rodar fora dele (mesmo padrao de
# test_migracao_perfil_tributario.py). Nunca toca o banco real da maquina.
# ---------------------------------------------------------------------------

import os

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from app.core.config import settings

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REVISAO_ANTERIOR = "d7a3e9c2f418"          # a head antes da Spec 04A
REVISAO = "608dc99a8616"
TABELA = "configuracoes_marcenaria"


def _config(url: str) -> Config:
    """Config do Alembic apontada para o banco temporario (e so para ele)."""
    assert url == settings.DATABASE_URL and "loja.db" in url
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    return cfg


@pytest.fixture
def banco(tmp_path, monkeypatch):
    """Banco de loja de antes da Spec 04A: empresa e produtos (com sofre_perda,
    que a fabrica F1 ja criou), e nada da configuracao da marcenaria."""
    url = f"sqlite:///{tmp_path / 'loja.db'}"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    engine = sa.create_engine(url)
    with engine.begin() as conn:
        conn.execute(sa.text("CREATE TABLE empresas (id INTEGER PRIMARY KEY, razao_social VARCHAR(255))"))
        conn.execute(sa.text("INSERT INTO empresas (razao_social) VALUES ('Marcenaria')"))
        conn.execute(sa.text(
            "CREATE TABLE produtos (id INTEGER PRIMARY KEY, nome VARCHAR(255), sofre_perda BOOLEAN NOT NULL DEFAULT 0)"
        ))
        conn.execute(sa.text("INSERT INTO produtos (nome, sofre_perda) VALUES ('MDF 15mm', 1), ('Dobradiça', 0)"))
    command.stamp(_config(url), REVISAO_ANTERIOR)        # "este banco esta na head antiga"
    yield url, engine
    engine.dispose()


def _inspector(engine) -> sa.Inspector:
    """Inspector numa conexao nova (o Alembic mexeu no banco por outra engine)."""
    engine.dispose()
    return sa.inspect(engine)


def _produtos(engine) -> list[tuple]:
    with engine.connect() as conn:
        return [tuple(l) for l in conn.execute(sa.text("SELECT id, nome, sofre_perda FROM produtos ORDER BY id"))]


def test_banco_antigo_ganha_a_tabela_e_produtos_ficam_intactos(banco):
    """Caso 21."""
    url, engine = banco
    antes = _produtos(engine)

    command.upgrade(_config(url), REVISAO)

    insp = _inspector(engine)
    assert insp.has_table(TABELA)
    colunas = {c["name"] for c in insp.get_columns(TABELA)}
    assert colunas == {
        "id", "empresa_id", "markup_padrao_bp", "perda_padrao_bp", "custo_hora_centavos",
        "rt_padrao_bp", "rt_modo", "validade_dias", "prazo_entrega_dias",
        "etapas_producao", "checklist_vistoria", "data_atualizacao",
    }
    fk = insp.get_foreign_keys(TABELA)[0]
    assert fk["referred_table"] == "empresas" and fk["options"].get("ondelete") == "CASCADE"
    assert _produtos(engine) == antes                   # sofre_perda com os valores que ja tinha


def test_tabela_ja_criada_pelo_create_all_nao_quebra(banco):
    """Caso 22: o startup roda create_all ANTES das migracoes."""
    url, engine = banco
    with engine.begin() as conn:
        conn.execute(sa.text(f"CREATE TABLE {TABELA} (id INTEGER PRIMARY KEY, empresa_id INTEGER NOT NULL)"))

    command.upgrade(_config(url), REVISAO)              # nao pode levantar "already exists"

    assert _inspector(engine).has_table(TABELA)


def test_downgrade_e_upgrade_de_novo(banco):
    """Caso 22a."""
    url, engine = banco
    command.upgrade(_config(url), REVISAO)
    command.downgrade(_config(url), REVISAO_ANTERIOR)
    assert not _inspector(engine).has_table(TABELA)
    command.upgrade(_config(url), REVISAO)
    assert _inspector(engine).has_table(TABELA)
