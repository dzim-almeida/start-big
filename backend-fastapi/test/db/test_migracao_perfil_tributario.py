# ---------------------------------------------------------------------------
# ARQUIVO: test/db/test_migracao_perfil_tributario.py
# DESCRIÇÃO: A migration v5w6x7y8z9a0 (TASK004) num banco de loja.
#
# ⚠️ alembic/env.py lê `settings.DATABASE_URL`; o fixture redireciona para o
# tmp_path e o teste se recusa a rodar fora dele (ver
# test_migracao_numeracao_confirmada.py).
# ---------------------------------------------------------------------------

import os

import pytest
import sqlalchemy as sa
from alembic.config import Config
from alembic import command

from app.core.config import settings

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REVISAO_ANTERIOR = "u4v5w6x7y8z9"
REVISAO = "v5w6x7y8z9a0"
TABELAS_NOVAS = {"perfil_tributario", "regra_perfil_tributario"}


def _config(url: str) -> Config:
    assert url == settings.DATABASE_URL and "loja.db" in url
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    return cfg


@pytest.fixture
def banco(tmp_path, monkeypatch):
    """Banco de loja antigo: só `empresas` (alvo da FK) e nada de perfil."""
    url = f"sqlite:///{tmp_path / 'loja.db'}"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    engine = sa.create_engine(url)
    with engine.begin() as conn:
        conn.execute(sa.text("CREATE TABLE empresas (id INTEGER PRIMARY KEY, razao_social VARCHAR(255))"))
        conn.execute(sa.text("INSERT INTO empresas (razao_social) VALUES ('Loja')"))
    command.stamp(_config(url), REVISAO_ANTERIOR)
    yield url, engine
    engine.dispose()


def _inspector(engine) -> sa.Inspector:
    """Inspector numa conexão nova.

    O Alembic altera o banco por outra engine; a conexão que ficou no pool
    desta guarda o schema em cache, e `PRAGMA foreign_key_list` numa tabela
    que ela ainda não conhece devolve vazio em vez de recarregar.
    """
    engine.dispose()
    return sa.inspect(engine)


def _tabelas(engine) -> set[str]:
    return set(_inspector(engine).get_table_names())


def _colunas(engine, tabela) -> dict[str, dict]:
    return {c["name"]: c for c in _inspector(engine).get_columns(tabela)}


def test_banco_antigo_ganha_as_duas_tabelas(banco):
    url, engine = banco
    command.upgrade(_config(url), REVISAO)

    assert TABELAS_NOVAS <= _tabelas(engine)
    assert "empresas" in _tabelas(engine)  # nada existente é tocado

    perfil = _colunas(engine, "perfil_tributario")
    assert set(perfil) == {"id", "empresa_id", "descricao", "data_criacao", "data_atualizacao"}

    regra = _colunas(engine, "regra_perfil_tributario")
    assert set(regra) == {
        "id", "perfil_id", "uf_destino", "ncm_excecao",
        "aliquota_interestadual", "aliquota_interna_destino", "percentual_fcp",
        "calculo_base_dupla", "mva_st", "reducao_base_calculo",
    }
    assert regra["uf_destino"]["nullable"] and regra["mva_st"]["nullable"]
    assert not regra["aliquota_interestadual"]["nullable"]


def test_defaults_de_banco_valem_num_insert_cru(banco):
    url, engine = banco
    command.upgrade(_config(url), REVISAO)

    with engine.begin() as conn:
        conn.execute(sa.text("INSERT INTO perfil_tributario (empresa_id, descricao) VALUES (1, 'Varejo')"))
        conn.execute(sa.text(
            "INSERT INTO regra_perfil_tributario (perfil_id, aliquota_interestadual, aliquota_interna_destino) "
            "VALUES (1, 1200, 1800)"
        ))
        linha = conn.execute(sa.text(
            "SELECT percentual_fcp, calculo_base_dupla FROM regra_perfil_tributario"
        )).one()
        datas = conn.execute(sa.text(
            "SELECT data_criacao, data_atualizacao FROM perfil_tributario"
        )).one()
    assert tuple(linha) == (0, 0)
    assert datas[0] is not None and datas[1] is not None


def test_constraints_no_banco(banco):
    url, engine = banco
    command.upgrade(_config(url), REVISAO)
    insp = _inspector(engine)

    fk_perfil = insp.get_foreign_keys("perfil_tributario")[0]
    assert fk_perfil["referred_table"] == "empresas" and fk_perfil["options"].get("ondelete") == "CASCADE"

    fk_regra = insp.get_foreign_keys("regra_perfil_tributario")[0]
    assert fk_regra["referred_table"] == "perfil_tributario" and fk_regra["options"].get("ondelete") == "CASCADE"

    uniques = {u["name"]: u["column_names"] for u in insp.get_unique_constraints("regra_perfil_tributario")}
    assert uniques.get("uq_regra_perfil_uf_ncm") == ["perfil_id", "uf_destino", "ncm_excecao"]

    indices = {i["name"] for i in insp.get_indexes("perfil_tributario")} | {i["name"] for i in insp.get_indexes("regra_perfil_tributario")}
    assert {"ix_perfil_tributario_empresa_id", "ix_regra_perfil_tributario_perfil_id"} <= indices


def test_tabelas_ja_criadas_pelo_create_all_nao_quebram(banco):
    url, engine = banco
    with engine.begin() as conn:
        conn.execute(sa.text("CREATE TABLE perfil_tributario (id INTEGER PRIMARY KEY, empresa_id INTEGER NOT NULL, descricao VARCHAR(120) NOT NULL)"))
        conn.execute(sa.text("CREATE TABLE regra_perfil_tributario (id INTEGER PRIMARY KEY, perfil_id INTEGER NOT NULL)"))
    command.upgrade(_config(url), REVISAO)  # não pode levantar "already exists"
    assert TABELAS_NOVAS <= _tabelas(engine)


def test_downgrade_remove_na_ordem_certa(banco):
    url, engine = banco
    command.upgrade(_config(url), REVISAO)
    command.downgrade(_config(url), REVISAO_ANTERIOR)
    assert not (TABELAS_NOVAS & _tabelas(engine))
    assert "empresas" in _tabelas(engine)
