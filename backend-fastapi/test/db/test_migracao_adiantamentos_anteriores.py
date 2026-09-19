# ---------------------------------------------------------------------------
# ARQUIVO: test/db/test_migracao_adiantamentos_anteriores.py
# DESCRIÇÃO: A migration v5w6x7y8z9a0 num banco de loja já em operação.
#
# O que ela precisa acertar: recuperar, por diferença, o adiantamento que uma
# OS reaberta UMA vez pela conta antiga carrega dentro de `credito_anterior`.
# Sem isso o `finalizar` novo (que soma `pagamentos + adiantamentos_anteriores`)
# cobraria de novo aquele adiantamento -- a correção viraria regressão.
#
# ⚠️ Mesma armadilha do test_migracao_numeracao_confirmada: env.py lê
# settings.DATABASE_URL. O fixture redireciona e o teste se recusa a rodar
# fora do diretório temporário.
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


def _config(url: str) -> Config:
    assert url == settings.DATABASE_URL and "loja.db" in url, (
        "env.py usa settings.DATABASE_URL; sem o redirecionamento a migration "
        "rodaria no banco real"
    )
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    return cfg


@pytest.fixture
def banco(tmp_path, monkeypatch):
    """Banco 'antigo': só o que a migration toca, sem a coluna nova."""
    url = f"sqlite:///{tmp_path / 'loja.db'}"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    engine = sa.create_engine(url)
    with engine.begin() as conn:
        conn.execute(sa.text(
            "CREATE TABLE ordens_servico (id INTEGER PRIMARY KEY, credito_anterior INTEGER)"
        ))
        conn.execute(sa.text(
            "CREATE TABLE ordem_servico_pagamentos ("
            " id INTEGER PRIMARY KEY, ordem_servico_id INTEGER NOT NULL, valor INTEGER NOT NULL)"
        ))
    command.stamp(_config(url), REVISAO_ANTERIOR)
    yield url, engine
    engine.dispose()


def _os(engine, os_id: int, credito, pagamentos: list[int]):
    with engine.begin() as conn:
        conn.execute(sa.text(
            "INSERT INTO ordens_servico (id, credito_anterior) VALUES (:id, :c)"
        ), {"id": os_id, "c": credito})
        for v in pagamentos:
            conn.execute(sa.text(
                "INSERT INTO ordem_servico_pagamentos (ordem_servico_id, valor) VALUES (:os, :v)"
            ), {"os": os_id, "v": v})


def _adiantamentos(engine) -> dict:
    with engine.connect() as conn:
        return dict(conn.execute(sa.text(
            "SELECT id, adiantamentos_anteriores FROM ordens_servico ORDER BY id"
        )).all())


def test_banco_antigo_ganha_a_coluna(banco):
    url, engine = banco
    _os(engine, 1, None, [])
    command.upgrade(_config(url), REVISAO)
    assert _adiantamentos(engine) == {1: None}


def test_os_reaberta_uma_vez_recupera_o_adiantamento_por_diferenca(banco):
    """Crédito 100 com pagamentos de 70: os 30 restantes eram o adiantamento."""
    url, engine = banco
    _os(engine, 1, 10000, [7000])
    command.upgrade(_config(url), REVISAO)
    assert _adiantamentos(engine) == {1: 3000}


def test_os_reaberta_sem_adiantamento_fica_em_zero(banco):
    url, engine = banco
    _os(engine, 1, 14000, [14000])
    command.upgrade(_config(url), REVISAO)
    assert _adiantamentos(engine) == {1: 0}


def test_os_nunca_reaberta_nao_e_tocada(banco):
    url, engine = banco
    _os(engine, 1, None, [5000])
    command.upgrade(_config(url), REVISAO)
    assert _adiantamentos(engine) == {1: None}


def test_os_ja_quebrada_pela_conta_antiga_nao_inventa_valor(banco):
    """Reaberta DUAS vezes pela conta antiga: o adiantamento já se perdeu e o
    crédito é só os pagamentos. A diferença dá 0 -- não há de onde recuperar,
    e o backfill não pode chutar."""
    url, engine = banco
    _os(engine, 1, 12000, [7000, 5000])
    command.upgrade(_config(url), REVISAO)
    assert _adiantamentos(engine) == {1: 0}


def test_coluna_ja_criada_pelo_create_all_ainda_faz_o_backfill(banco):
    """Cenário real do startup: create_all() cria a coluna (NULL) antes da
    migration. O ADD é pulado, mas o backfill PRECISA rodar."""
    url, engine = banco
    with engine.begin() as conn:
        conn.execute(sa.text("ALTER TABLE ordens_servico ADD COLUMN adiantamentos_anteriores INTEGER"))
    _os(engine, 1, 10000, [7000])
    command.upgrade(_config(url), REVISAO)  # não pode levantar "duplicate column"
    assert _adiantamentos(engine) == {1: 3000}


def test_rodar_duas_vezes_nao_muda_nada(banco):
    url, engine = banco
    _os(engine, 1, 10000, [7000])
    command.upgrade(_config(url), REVISAO)
    command.downgrade(_config(url), REVISAO_ANTERIOR)
    command.upgrade(_config(url), REVISAO)
    assert _adiantamentos(engine) == {1: 3000}
