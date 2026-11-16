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


# --- F2: orçamento por móvel (a2d8b3e5f107) -----------------------------------------

def _migracao_f2():
    caminho = Path(__file__).parents[4] / "alembic" / "versions" / "a2d8b3e5f107_fabrica_orcamento_por_movel.py"
    spec = importlib.util.spec_from_file_location("migracao_fabrica_f2", caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _base_f2(conexao):
    conexao.exec_driver_sql("PRAGMA foreign_keys=ON")
    conexao.exec_driver_sql("CREATE TABLE produtos (id INTEGER PRIMARY KEY, nome TEXT)")
    conexao.exec_driver_sql("CREATE TABLE pedidos_compra (id INTEGER PRIMARY KEY)")
    conexao.exec_driver_sql("CREATE TABLE configuracoes_os (id INTEGER PRIMARY KEY, empresa_id INTEGER)")
    conexao.exec_driver_sql("CREATE TABLE ordens_servico (id INTEGER PRIMARY KEY, numero_os TEXT)")
    conexao.exec_driver_sql(
        "CREATE TABLE ordem_servico_itens (id INTEGER PRIMARY KEY, "
        "ordem_servico_id INTEGER REFERENCES ordens_servico(id), nome TEXT)"
    )
    conexao.exec_driver_sql("INSERT INTO configuracoes_os VALUES (1, 1)")
    conexao.exec_driver_sql("INSERT INTO ordens_servico VALUES (1, 'OS-2026-000001')")
    conexao.exec_driver_sql("INSERT INTO ordem_servico_itens VALUES (1, 1, 'Troca de óleo')")


def test_f2_cria_tabelas_e_colunas_sem_tocar_nas_os_e_e_idempotente():
    m = _migracao_f2()
    assert m.down_revision == "f1c7a2d9e3b4"
    engine = sa.create_engine("sqlite://")
    with engine.begin() as conexao:
        _base_f2(conexao)
        with Operations.context(MigrationContext.configure(conexao)):
            m.upgrade()
            m.upgrade()
        insp = sa.inspect(conexao)
        for tabela in ("fabrica_orcamentos", "fabrica_ambientes", "fabrica_moveis", "fabrica_materiais"):
            assert insp.has_table(tabela)
        assert "modo_fabrica" in {c["name"] for c in insp.get_columns("configuracoes_os")}
        assert "fase_fabrica" in {c["name"] for c in insp.get_columns("ordens_servico")}
        assert {"fabrica_orcamento_id", "fabrica_movel_id"} <= {c["name"] for c in insp.get_columns("ordem_servico_itens")}
        assert conexao.exec_driver_sql("SELECT modo_fabrica FROM configuracoes_os").scalar() == 0
        assert conexao.exec_driver_sql("SELECT fase_fabrica FROM ordens_servico").scalar() is None
        assert conexao.exec_driver_sql("SELECT nome FROM ordem_servico_itens").scalar() == "Troca de óleo"


def test_f2_tabelas_ja_criadas_pelo_create_all_sao_respeitadas():
    from app.db.models.fabrica_orcamento import FabricaOrcamento

    m = _migracao_f2()
    engine = sa.create_engine("sqlite://")
    with engine.begin() as conexao:
        _base_f2(conexao)
        FabricaOrcamento.__table__.create(conexao)
        conexao.exec_driver_sql(
            "INSERT INTO fabrica_orcamentos (os_id, versao, situacao, perda_bp, sinal_bp, total, custo_total, "
            "criado_em, atualizado_em) VALUES (1, 1, 'RASCUNHO', 1000, 5000, 0, 0, '2026-10-05', '2026-10-05')"
        )
        with Operations.context(MigrationContext.configure(conexao)):
            m.upgrade()
        assert conexao.exec_driver_sql("SELECT versao FROM fabrica_orcamentos").scalar() == 1



# --- F3: o trilho (b4e9c1a7d2f3) ------------------------------------------------------

def _migracao_f3():
    caminho = Path(__file__).parents[4] / "alembic" / "versions" / "b4e9c1a7d2f3_fabrica_trilho.py"
    spec = importlib.util.spec_from_file_location("migracao_fabrica_f3", caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_f3_colunas_e_log_sem_tocar_nas_os_e_idempotente():
    m = _migracao_f3()
    assert m.down_revision == "a2d8b3e5f107"
    engine = sa.create_engine("sqlite://")
    with engine.begin() as conexao:
        _base_f2(conexao)
        with Operations.context(MigrationContext.configure(conexao)):
            m.upgrade()
            m.upgrade()
        insp = sa.inspect(conexao)
        assert insp.has_table("fabrica_fases_log")
        assert {"data_instalacao", "compra_liberada_em", "compra_liberada_por", "compra_liberada_motivo"} <= {
            c["name"] for c in insp.get_columns("ordens_servico")
        }
        assert "fabrica_travar_etapas" in {c["name"] for c in insp.get_columns("configuracoes_os")}
        assert conexao.exec_driver_sql("SELECT fabrica_travar_etapas FROM configuracoes_os").scalar() == 0
        assert conexao.exec_driver_sql("SELECT numero_os, data_instalacao FROM ordens_servico").one() == (
            "OS-2026-000001", None)


# --- F4: separação (c6f2d8a4b915) -------------------------------------------------------

def test_f4_colunas_do_item_sem_tocar_nos_itens():
    caminho = Path(__file__).parents[4] / "alembic" / "versions" / "c6f2d8a4b915_fabrica_separacao.py"
    spec = importlib.util.spec_from_file_location("migracao_fabrica_f4", caminho)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert m.down_revision == "b4e9c1a7d2f3"
    engine = sa.create_engine("sqlite://")
    with engine.begin() as conexao:
        _base_f2(conexao)
        with Operations.context(MigrationContext.configure(conexao)):
            m.upgrade()
            m.upgrade()
        colunas = {c["name"] for c in sa.inspect(conexao).get_columns("ordem_servico_itens")}
        assert {"quantidade_separada", "custo_real"} <= colunas
        assert conexao.exec_driver_sql(
            "SELECT nome, quantidade_separada, custo_real FROM ordem_servico_itens"
        ).one() == ("Troca de óleo", None, None)
