# ---------------------------------------------------------------------------
# ARQUIVO: test_reconciliacao_colunas.py
# DESCRIÇÃO: A rede de segurança do boot (`reconciliar_colunas`) precisa
#            conseguir criar toda coluna que tem default.
#
# Incidente de 06/10/2026: a serigrafia foi atualizada por cima de uma versão
# antiga e as vendas deram "erro interno". O banco estava sem
# `configuracoes_vendas.regra_ordem`; a migração não rodou (linhagem antiga) e a
# reconciliação tentava, a cada boot:
#     ALTER TABLE ... ADD COLUMN "regra_ordem" VARCHAR(20) DEFAULT R1,R2,R3
# — erro de sintaxe (literal sem aspas), coluna pulada para sempre.
# ---------------------------------------------------------------------------

import pytest
from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, create_engine, func, text

from app.db import migrations


@pytest.fixture
def banco(monkeypatch, tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'r.db'}")
    monkeypatch.setattr(migrations, "engine", engine)
    return engine


def _ddl(coluna, banco):
    Table("t", MetaData(), Column("id", Integer, primary_key=True), coluna)
    return migrations._ddl_da_coluna(coluna)


def test_literal_com_virgula_vai_entre_aspas(banco):
    ddl = _ddl(Column("regra_ordem", String(20), server_default="R1,R2,R3", nullable=False), banco)
    assert ddl.endswith("DEFAULT 'R1,R2,R3'")


def test_literal_com_aspas_e_escapado(banco):
    assert _ddl(Column("x", String(20), server_default="d'agua"), banco).endswith("DEFAULT 'd''agua'")


def test_funcao_now_entra_sem_default(banco):
    ddl = _ddl(Column("criado_em", DateTime, server_default=func.now(), nullable=False), banco)
    assert ddl is not None and "DEFAULT" not in ddl


def test_o_caso_da_serigrafia_a_coluna_e_criada_no_boot(banco, monkeypatch):
    """Banco antigo sem `regra_ordem`: a reconciliação cria, com o default certo."""
    meta = MetaData()
    tabela = Table(
        "configuracoes_vendas", meta,
        Column("id", Integer, primary_key=True),
        Column("regra_conflito", String(12), server_default="MENOR_PRECO", nullable=False),
        Column("regra_ordem", String(20), server_default="R1,R2,R3", nullable=False),
        Column("data_atualizacao", DateTime, server_default=func.now(), nullable=False),
    )

    class _BaseFalsa:
        metadata = meta

    monkeypatch.setattr(migrations, "Base", _BaseFalsa)
    with banco.begin() as c:
        c.execute(text("CREATE TABLE configuracoes_vendas (id INTEGER PRIMARY KEY)"))
        c.execute(text("INSERT INTO configuracoes_vendas (id) VALUES (1)"))

    migrations.reconciliar_colunas()

    with banco.connect() as c:
        linha = c.execute(text("SELECT regra_conflito, regra_ordem FROM configuracoes_vendas")).one()
        colunas = {r[1] for r in c.execute(text("PRAGMA table_info(configuracoes_vendas)"))}
    assert linha == ("MENOR_PRECO", "R1,R2,R3")
    assert "data_atualizacao" in colunas
    assert tabela is not None
