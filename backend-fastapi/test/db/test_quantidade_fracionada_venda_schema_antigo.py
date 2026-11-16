"""
Venda fracionada (docs/venda-fracionada-plano.md, F0): a aposta do SQLite,
agora para `produtos_venda` e `orcamentos_produtos`.

Mesma decisão de `test_quantidade_fracionada_schema_antigo.py` (estoque, 10/08):
a linha da venda vai aceitar 3,5 kg SEM migration, porque o SQLite guarda 3.5
numa coluna declarada INTEGER sem perda. Recriar `produtos_venda` no banco
vivo das lojas, sem backup automático, seria risco sem ganho.

O DDL abaixo é o de 07/10/2026 (quantidade INTEGER NOT NULL com CHECK > 0),
CONGELADO aqui de propósito: o conftest monta o banco com create_all, e depois
da F1 ele passa a gerar REAL — quem roda na loja continua com INTEGER.
"""

import sqlite3

import pytest

DDL_PRODUTOS_VENDA_LEGADO = """
CREATE TABLE produtos_venda (
    id INTEGER NOT NULL,
    venda_id INTEGER NOT NULL,
    produto_id INTEGER,
    tipo_produto VARCHAR(10) NOT NULL,
    descricao_avulsa VARCHAR(255),
    quantidade INTEGER NOT NULL,
    valor_unitario INTEGER NOT NULL,
    custo_unitario INTEGER,
    desconto INTEGER NOT NULL,
    subtotal INTEGER NOT NULL,
    embalagem_id INTEGER,
    fator_embalagem INTEGER DEFAULT '1' NOT NULL,
    sigla_embalagem VARCHAR(6),
    desconto_regra INTEGER DEFAULT '0' NOT NULL,
    regra_preco VARCHAR(12),
    regra_descricao VARCHAR(80),
    valor_unitario_tabela INTEGER,
    PRIMARY KEY (id),
    CONSTRAINT ck_produto_venda_qtd_positiva CHECK (quantidade > 0)
)
"""

DDL_ORCAMENTOS_PRODUTOS_LEGADO = """
CREATE TABLE orcamentos_produtos (
    id INTEGER NOT NULL,
    orcamento_id INTEGER NOT NULL,
    produto_id INTEGER,
    tipo_produto VARCHAR(10) NOT NULL,
    descricao_avulsa VARCHAR(255),
    quantidade INTEGER NOT NULL,
    valor_unitario INTEGER NOT NULL,
    desconto INTEGER NOT NULL,
    subtotal INTEGER NOT NULL,
    embalagem_id INTEGER,
    fator_embalagem INTEGER DEFAULT '1' NOT NULL,
    sigla_embalagem VARCHAR(6),
    PRIMARY KEY (id),
    CONSTRAINT ck_orcamento_produto_qtd_positiva CHECK (quantidade > 0)
)
"""

TABELAS = {
    "produtos_venda": (DDL_PRODUTOS_VENDA_LEGADO, "venda_id"),
    "orcamentos_produtos": (DDL_ORCAMENTOS_PRODUTOS_LEGADO, "orcamento_id"),
}


@pytest.fixture(params=sorted(TABELAS))
def legado(request, tmp_path):
    tabela = request.param
    ddl, fk = TABELAS[tabela]
    conn = sqlite3.connect(tmp_path / "legado.db")
    conn.execute(ddl)
    conn.commit()
    yield conn, tabela, fk
    conn.close()


def _inserir(conn, tabela, fk, quantidade, id_=1):
    conn.execute(
        f"INSERT INTO {tabela} (id, {fk}, produto_id, tipo_produto, quantidade, valor_unitario, desconto, subtotal) "
        "VALUES (?, 1, 1, 'CADASTRADO', ?, 3000, 0, 10500)",
        (id_, quantidade),
    )
    conn.commit()


def test_o_schema_do_teste_e_mesmo_o_antigo(legado):
    """Guarda: se falhar, os demais não provam nada."""
    conn, tabela, _ = legado
    tipo = next(r[2] for r in conn.execute(f"PRAGMA table_info({tabela})") if r[1] == "quantidade")
    assert tipo == "INTEGER"


def test_tres_e_meio_sobrevive_em_coluna_integer(legado):
    conn, tabela, fk = legado
    _inserir(conn, tabela, fk, 3.5)
    assert conn.execute(f"SELECT quantidade, typeof(quantidade) FROM {tabela}").fetchone() == (3.5, "real")


def test_meio_quilo_passa_no_check_de_positivo(legado):
    """O CHECK (quantidade > 0) do schema antigo não pode barrar 0,5 kg."""
    conn, tabela, fk = legado
    _inserir(conn, tabela, fk, 0.5)
    assert conn.execute(f"SELECT quantidade FROM {tabela}").fetchone()[0] == 0.5
    with pytest.raises(sqlite3.IntegrityError):
        _inserir(conn, tabela, fk, 0, id_=2)


def test_inteiro_continua_inteiro(legado):
    """3.0 vindo de um Float volta a ser `integer` no disco — a venda em UN fica igual."""
    conn, tabela, fk = legado
    _inserir(conn, tabela, fk, 3.0)
    assert conn.execute(f"SELECT quantidade, typeof(quantidade) FROM {tabela}").fetchone() == (3, "integer")
