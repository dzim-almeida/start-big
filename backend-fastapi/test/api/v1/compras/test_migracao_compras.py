# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/compras/test_migracao_compras.py
# DESCRIÇÃO: A migração a1c4e7b20d93 numa base como a do cliente.
#
# No startup, `create_all()` roda ANTES das migrações (app/core/tarefas.py):
# num cliente que atualiza, a tabela pode já existir quando a migração roda.
# Ela precisa decidir pela ausência da tabela e não tocar em nada que exista.
# ---------------------------------------------------------------------------

import importlib.util
from pathlib import Path

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


def _migracao():
    caminho = Path(__file__).parents[4] / "alembic" / "versions" / "a1c4e7b20d93_compras_fornecedores_do_produto.py"
    spec = importlib.util.spec_from_file_location("migracao_compras_fase1", caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _base_do_cliente(conexao):
    conexao.exec_driver_sql("CREATE TABLE produtos (id INTEGER PRIMARY KEY, nome TEXT)")
    conexao.exec_driver_sql("CREATE TABLE fornecedores (id INTEGER PRIMARY KEY, nome TEXT)")
    conexao.exec_driver_sql("CREATE TABLE produto_embalagens (id INTEGER PRIMARY KEY, produto_id INTEGER)")
    conexao.exec_driver_sql("INSERT INTO produtos VALUES (1, 'Cerveja')")
    conexao.exec_driver_sql("INSERT INTO fornecedores VALUES (1, 'Ambev')")


def test_cria_a_tabela_e_rodar_de_novo_nao_muda_nada():
    m = _migracao()
    assert m.down_revision == "f6b3d82a1c47"
    engine = sa.create_engine("sqlite://")
    with engine.begin() as conexao:
        _base_do_cliente(conexao)
        with Operations.context(MigrationContext.configure(conexao)):
            m.upgrade()
            m.upgrade()  # idempotente
        insp = sa.inspect(conexao)
        colunas = {c["name"] for c in insp.get_columns("produto_fornecedores")}
        assert {"produto_id", "fornecedor_id", "embalagem_id", "fator", "ultimo_preco", "prazo_dias"} <= colunas
        # Nada existente foi tocado.
        assert conexao.exec_driver_sql("SELECT nome FROM produtos").scalar() == "Cerveja"


def test_tabela_ja_criada_pelo_create_all_e_respeitada():
    from app.db.models.produto_fornecedor import ProdutoFornecedor

    m = _migracao()
    engine = sa.create_engine("sqlite://")
    with engine.begin() as conexao:
        _base_do_cliente(conexao)
        ProdutoFornecedor.__table__.create(conexao)  # o create_all chegou primeiro
        conexao.exec_driver_sql(
            "INSERT INTO produto_fornecedores (produto_id, fornecedor_id, fator, criado_em, atualizado_em) "
            "VALUES (1, 1, 12, '2026-10-03', '2026-10-03')"
        )
        with Operations.context(MigrationContext.configure(conexao)):
            m.upgrade()
        assert conexao.exec_driver_sql("SELECT fator FROM produto_fornecedores").scalar() == 12


# --- fase 2: pedido de compra (b7d2f4a9c315) -----------------------------------

def _migracao_fase2():
    caminho = Path(__file__).parents[4] / "alembic" / "versions" / "b7d2f4a9c315_compras_pedido_de_compra.py"
    spec = importlib.util.spec_from_file_location("migracao_compras_fase2", caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _base_fase2(conexao):
    _base_do_cliente(conexao)
    conexao.exec_driver_sql("CREATE TABLE empresas (id INTEGER PRIMARY KEY)")
    conexao.exec_driver_sql("CREATE TABLE usuarios (id INTEGER PRIMARY KEY)")


def test_fase2_cria_as_quatro_tabelas_e_e_idempotente():
    m = _migracao_fase2()
    assert m.down_revision == "a1c4e7b20d93"
    engine = sa.create_engine("sqlite://")
    with engine.begin() as conexao:
        _base_fase2(conexao)
        with Operations.context(MigrationContext.configure(conexao)):
            m.upgrade()
            m.upgrade()
        tabelas = set(sa.inspect(conexao).get_table_names())
        assert {"pedidos_compra", "pedido_compra_itens", "pedido_compra_parcelas", "compras_log"} <= tabelas


def test_fase2_respeita_tabela_criada_pelo_create_all():
    from app.db.models.compra_log import CompraLog

    m = _migracao_fase2()
    engine = sa.create_engine("sqlite://")
    with engine.begin() as conexao:
        _base_fase2(conexao)
        CompraLog.__table__.create(conexao)
        conexao.exec_driver_sql(
            "INSERT INTO compras_log (objeto, objeto_id, acao, ocorrido_em) VALUES ('PEDIDO', 1, 'CRIADO', '2026-10-03')"
        )
        with Operations.context(MigrationContext.configure(conexao)):
            m.upgrade()
        assert conexao.exec_driver_sql("SELECT COUNT(*) FROM compras_log").scalar() == 1


# --- fase 3: recebimento (c3e8a1f5d927) ------------------------------------------------

def _migracao_fase3():
    caminho = Path(__file__).parents[4] / "alembic" / "versions" / "c3e8a1f5d927_compras_recebimento.py"
    spec = importlib.util.spec_from_file_location("migracao_compras_fase3", caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _base_fase3(conexao):
    _base_fase2(conexao)
    with Operations.context(MigrationContext.configure(conexao)):
        _migracao_fase2().upgrade()
    conexao.exec_driver_sql("CREATE TABLE movimentacoes_estoque (id INTEGER PRIMARY KEY, quantidade FLOAT)")
    conexao.exec_driver_sql("CREATE TABLE contas_pagar (id INTEGER PRIMARY KEY, valor INTEGER)")
    conexao.exec_driver_sql("INSERT INTO movimentacoes_estoque VALUES (1, 5)")
    conexao.exec_driver_sql("INSERT INTO contas_pagar VALUES (1, 1000)")


def test_fase3_cria_tabelas_e_colunas_sem_tocar_nas_linhas():
    m = _migracao_fase3()
    assert m.down_revision == "b7d2f4a9c315"
    engine = sa.create_engine("sqlite://")
    with engine.begin() as conexao:
        _base_fase3(conexao)
        with Operations.context(MigrationContext.configure(conexao)):
            m.upgrade()
            m.upgrade()  # idempotente
        insp = sa.inspect(conexao)
        assert {"recebimentos_compra", "recebimento_compra_itens"} <= set(insp.get_table_names())
        assert "recebimento_compra_id" in {c["name"] for c in insp.get_columns("movimentacoes_estoque")}
        assert "recebimento_compra_id" in {c["name"] for c in insp.get_columns("contas_pagar")}
        # As linhas que já existiam continuam iguais, com a coluna nova nula.
        assert conexao.exec_driver_sql(
            "SELECT quantidade, recebimento_compra_id FROM movimentacoes_estoque").one() == (5, None)
        assert conexao.exec_driver_sql("SELECT valor, recebimento_compra_id FROM contas_pagar").one() == (1000, None)
