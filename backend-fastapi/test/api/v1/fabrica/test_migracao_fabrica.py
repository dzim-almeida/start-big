# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/fabrica/test_migracao_fabrica.py
# DESCRIÇÃO: A migração f1c7a2d9e3b4 numa base como a do cliente.
#
# O `create_all()` do startup não acrescenta coluna em tabela que já existe:
# num cliente que atualiza, é a migração que cria as colunas — e ela não pode
# tocar nos dados nem quebrar se rodar de novo.
# ---------------------------------------------------------------------------

import importlib.util
from pathlib import Path

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


def _migracao():
    caminho = Path(__file__).parents[4] / "alembic" / "versions" / "f1c7a2d9e3b4_fabrica_insumo_no_produto.py"
    spec = importlib.util.spec_from_file_location("migracao_fabrica_f1", caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_acrescenta_as_colunas_sem_tocar_nos_produtos_e_e_idempotente():
    m = _migracao()
    assert m.down_revision == "e8a3c6d1f702"
    engine = sa.create_engine("sqlite://")
    with engine.begin() as conexao:
        # Com FK ligada, como no app: um batch_alter_table quebraria aqui.
        conexao.exec_driver_sql("PRAGMA foreign_keys=ON")
        conexao.exec_driver_sql("CREATE TABLE produtos (id INTEGER PRIMARY KEY, nome TEXT)")
        conexao.exec_driver_sql(
            "CREATE TABLE estoque (id INTEGER PRIMARY KEY, produto_id INTEGER REFERENCES produtos(id))"
        )
        conexao.exec_driver_sql("INSERT INTO produtos VALUES (1, 'MDF 15mm')")
        conexao.exec_driver_sql("INSERT INTO estoque VALUES (1, 1)")
        with Operations.context(MigrationContext.configure(conexao)):
            m.upgrade()
            m.upgrade()  # idempotente
        colunas = {c["name"] for c in sa.inspect(conexao).get_columns("produtos")}
        assert {"unidade_consumo", "consumo_por_unidade", "sofre_perda"} <= colunas
        linha = conexao.exec_driver_sql(
            "SELECT nome, unidade_consumo, consumo_por_unidade, sofre_perda FROM produtos"
        ).one()
        assert tuple(linha) == ("MDF 15mm", None, None, 0)
        assert conexao.exec_driver_sql("SELECT produto_id FROM estoque").scalar() == 1


def test_banco_sem_produtos_nao_quebra():
    m = _migracao()
    engine = sa.create_engine("sqlite://")
    with engine.begin() as conexao:
        with Operations.context(MigrationContext.configure(conexao)):
            m.upgrade()
