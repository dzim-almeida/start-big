# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/compras/test_importacao_planilha.py
# DESCRIÇÃO: Importação de produtos por planilha Excel.
#
# O que não pode errar: a prévia não grava; importar de novo não duplica nem
# muda o que existe; linha com erro não entra e não derruba as outras.
# ---------------------------------------------------------------------------

import io

import pytest
from openpyxl import Workbook

from app.db.models.movimentacao_estoque import MovimentacaoEstoque
from app.db.models.produto import Produto
from app.db.models.produto_fiscal import ProdutoFiscal
from app.services.produto import importacao_planilha

URL = "/api/v1/estoque/importar-planilha"
CABECALHO = ["IMPORTAR", "CODIGO", "NOME", "UNIDADE", "CODIGO_BARRAS", "CATEGORIA", "NCM", "CFOP", "CSOSN", "CUSTO", "PRECO_VENDA", "ESTOQUE"]


def _xlsx(*linhas, cabecalho=CABECALHO, aba="Produtos") -> bytes:
    livro = Workbook()
    livro.active.title = "Leia-me"
    livro.active.append(["isto não é a lista de produtos"])
    planilha = livro.create_sheet(aba)
    planilha.append(cabecalho)
    for linha in linhas:
        planilha.append(linha)
    saida = io.BytesIO()
    livro.save(saida)
    return saida.getvalue()


def _enviar(client, headers, conteudo: bytes, rota: str = "ler"):
    return client.post(
        f"{URL}/{rota}",
        files={"arquivo": ("produtos.xlsx", conteudo, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=headers,
    )


def _produto(db, codigo: str) -> Produto | None:
    db.expire_all()
    return db.query(Produto).filter_by(codigo_produto=codigo).first()


@pytest.fixture
def com_fiscal(monkeypatch):
    monkeypatch.setattr(importacao_planilha, "_fiscal_disponivel", lambda *_: True)


@pytest.fixture
def sem_fiscal(monkeypatch):
    monkeypatch.setattr(importacao_planilha, "_fiscal_disponivel", lambda *_: False)


MDF = ["SIM", "ANT-1", "MDF 15MM BRANCO", "UN", "7898945023665", "Chapas", "44111490", "5102", "102", 100.5, 150.75, 3]


def test_previa_nao_grava(client, db_session, header_com_token, com_fiscal):
    r = _enviar(client, header_com_token, _xlsx(MDF))

    assert r.status_code == 200, r.text
    corpo = r.json()
    assert (corpo["novos"], corpo["com_erro"]) == (1, 0)
    linha = corpo["linhas"][0]
    assert (linha["linha"], linha["preco"], linha["custo"], linha["ncm"]) == (2, 15075, 10050, "44111490")
    assert _produto(db_session, "ANT-1") is None


def test_importa_produto_com_estoque_livro_e_fiscal(client, db_session, header_com_token, com_fiscal):
    r = _enviar(client, header_com_token, _xlsx(MDF), "importar")

    assert r.status_code == 201, r.text
    assert r.json()["criados"] == 1
    produto = _produto(db_session, "ANT-1")
    assert (produto.estoque.valor_varejo, produto.estoque.valor_entrada, produto.estoque.quantidade) == (15075, 10050, 3)
    assert (produto.codigo_barras, produto.categoria, produto.unidade_medida) == ("7898945023665", "Chapas", "UN")

    fiscal = db_session.query(ProdutoFiscal).filter_by(produto_id=produto.id).one()
    assert (fiscal.ncm, fiscal.cfop_padrao, fiscal.csosn) == ("44111490", "5102", "102")

    # Não dobra: a quantidade entra pelo livro, uma vez só.
    movimentos = db_session.query(MovimentacaoEstoque).filter_by(produto_id=produto.id).all()
    assert [m.quantidade for m in movimentos] == [3]


def test_importar_de_novo_nao_duplica_nem_muda(client, db_session, header_com_token, com_fiscal):
    _enviar(client, header_com_token, _xlsx(MDF), "importar")
    outra = [*MDF[:10], 999.0, 500]

    r = _enviar(client, header_com_token, _xlsx(outra), "importar")

    assert (r.json()["criados"], r.json()["ja_existiam"]) == (0, 1)
    produto = _produto(db_session, "ANT-1")
    assert (produto.estoque.valor_varejo, produto.estoque.quantidade) == (15075, 3)
    assert db_session.query(Produto).filter_by(codigo_produto="ANT-1").count() == 1


def test_linha_com_erro_nao_entra_e_nao_derruba_as_outras(client, db_session, header_com_token, com_fiscal):
    sem_preco = ["SIM", "ANT-2", "SEM PRECO", "UN", None, None, "44111490", None, None, 10, 0, 1]
    ncm_ruim = ["SIM", "ANT-3", "NCM RUIM", "UN", None, None, "123", None, None, 10, 20, 1]

    r = _enviar(client, header_com_token, _xlsx(MDF, sem_preco, ncm_ruim), "importar")

    assert (r.json()["criados"], r.json()["com_erro"]) == (1, 2)
    assert _produto(db_session, "ANT-1") is not None
    assert _produto(db_session, "ANT-2") is None
    assert _produto(db_session, "ANT-3") is None


def test_nao_importa_o_que_esta_marcado_nao(client, db_session, header_com_token, com_fiscal):
    r = _enviar(client, header_com_token, _xlsx(["NÃO", *MDF[1:]]), "importar")

    assert (r.json()["criados"], r.json()["ignorados"]) == (0, 1)
    assert _produto(db_session, "ANT-1") is None


def test_estoque_negativo_entra_zerado_com_aviso(client, db_session, header_com_token, com_fiscal):
    movel = ["SIM", "ANT-4", "ARMARIO", "UN", None, None, "94036000", "5101", "101", None, 1000, -117]

    previa = _enviar(client, header_com_token, _xlsx(movel)).json()["linhas"][0]
    assert previa["situacao"] == "novo"
    assert "Estoque negativo (-117) entra como zero." in previa["mensagens"]

    _enviar(client, header_com_token, _xlsx(movel), "importar")
    assert _produto(db_session, "ANT-4").estoque.quantidade == 0


def test_codigo_e_barras_repetidos_na_planilha(client, db_session, header_com_token, com_fiscal):
    mesmo_codigo = [*MDF]
    mesmo_barras = ["SIM", "ANT-9", "OUTRO", "UN", MDF[4], None, None, None, None, 1, 2, 1]

    linhas = _enviar(client, header_com_token, _xlsx(MDF, mesmo_codigo, mesmo_barras)).json()["linhas"]

    assert [l["situacao"] for l in linhas] == ["novo", "existe", "erro"]


def test_sem_gtin_vira_produto_sem_codigo_de_barras(client, db_session, header_com_token, com_fiscal):
    linha = ["SIM", "ANT-5", "PARAFUSO", "UN", "SEM GTIN", None, "73181200", None, None, 1, 2, 10]

    _enviar(client, header_com_token, _xlsx(linha), "importar")

    assert _produto(db_session, "ANT-5").codigo_barras is None


def test_sem_modulo_fiscal_cadastra_sem_gravar_fiscal(client, db_session, header_com_token, sem_fiscal):
    previa = _enviar(client, header_com_token, _xlsx(MDF)).json()
    assert (previa["fiscal_disponivel"], previa["planilha_tem_fiscal"]) == (False, True)

    _enviar(client, header_com_token, _xlsx(MDF), "importar")

    produto = _produto(db_session, "ANT-1")
    assert produto is not None
    assert db_session.query(ProdutoFiscal).filter_by(produto_id=produto.id).first() is None


def test_valores_como_o_excel_entrega(client, db_session, header_com_token, com_fiscal):
    """Código numérico, preço em texto brasileiro, NCM sem o zero à esquerda."""
    linha = ["SIM", 1234.0, "TESTE", "UN", None, None, 1012100, None, None, "1.234,56", "R$ 2.000,50", "1,5"]

    previa = _enviar(client, header_com_token, _xlsx(linha)).json()["linhas"][0]

    assert (previa["codigo"], previa["ncm"], previa["custo"], previa["preco"], previa["estoque"]) == ("1234", "01012100", 123456, 200050, 1.5)


@pytest.mark.parametrize("conteudo", [b"isto nao e excel", b""])
def test_arquivo_invalido_explica(client, header_com_token, conteudo):
    r = _enviar(client, header_com_token, conteudo)

    assert r.status_code == 422
    assert "xlsx" in r.json()["detail"]


def test_falta_coluna_explica(client, header_com_token):
    r = _enviar(client, header_com_token, _xlsx(["X", "Y"], cabecalho=["CODIGO", "NOME"]))

    assert r.status_code == 422
    assert "PRECO_VENDA" in r.json()["detail"]


def test_exige_login(client):
    assert _enviar(client, {}, _xlsx(MDF)).status_code == 401
