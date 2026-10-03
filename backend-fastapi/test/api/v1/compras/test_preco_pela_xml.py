# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/compras/test_preco_pela_xml.py
# DESCRIÇÃO: A entrada por XML alimenta o último preço por fornecedor
#            (docs/compras-plano.md, D13/D18).
#
# A entrada por XML está em produção: o que se testa aqui é que ela continua
# funcionando COM o gancho novo — com ou sem o módulo Compras, inclusive com o
# mesmo produto em dois itens da nota (que derrubaria a importação se o
# gancho criasse duas linhas).
# ---------------------------------------------------------------------------

from datetime import date

from app.db.models.produto import Produto
from app.db.models.produto_fornecedor import ProdutoFornecedor
from test.api.v1.embalagens.test_entrada_xml import decisoes
from test.api.v1.embalagens.test_venda_por_embalagem import estoque, loja  # noqa: F401 — `loja` é fixture
from test.core.nfe_exemplo import item_cerveja, nota

URL = "/api/v1/estoque/nfe-entrada/importar"


def linhas(db_session) -> dict[int, ProdutoFornecedor]:
    db_session.expire_all()
    return {l.produto_id: l for l in db_session.query(ProdutoFornecedor).all()}


def test_grava_o_preco_mesmo_sem_o_modulo(client, db_session, header_com_token, loja, licenca):
    licenca()  # loja SEM Compras: a entrada por XML não pode depender dele
    r = client.post(URL, json=decisoes(loja), headers=header_com_token)
    assert r.status_code == 201, r.text
    fornecedor_id = r.json()["fornecedor_id"]

    por_produto = linhas(db_session)
    cerveja = por_produto[loja["produto_id"]]
    # 2 CX = 2 fardos de 12; o item custou R$ 104,00 → R$ 52,00 o fardo.
    assert (cerveja.fornecedor_id, cerveja.embalagem_id, cerveja.fator, cerveja.ultimo_preco) == (
        fornecedor_id, loja["FD"], 12, 5200)
    assert (cerveja.codigo_fornecedor, cerveja.ultima_compra_em) == ("CERV-CX12", date(2026, 9, 30))

    biscoito = db_session.query(Produto).filter(Produto.codigo_produto == "BISC-140").one()
    # 10 un a R$ 2,50 + R$ 1,00 de IPI = R$ 26,00 → R$ 2,60 a unidade.
    assert (por_produto[biscoito.id].fator, por_produto[biscoito.id].ultimo_preco) == (1, 260)


def test_linha_existente_mantem_a_embalagem_do_lojista(client, db_session, header_com_token, loja):
    # O lojista disse que compra deste fornecedor POR UNIDADE; a nota veio em fardo.
    primeira = client.post(URL, json=decisoes(loja, lancar_contas_pagar=False), headers=header_com_token)
    fornecedor_id = primeira.json()["fornecedor_id"]
    r = client.put(
        f"/api/v1/compras/produtos/{loja['produto_id']}/fornecedores",
        json={"fornecedores": [{"fornecedor_id": fornecedor_id, "fator": 1, "ultimo_preco": 999}]},
        headers=header_com_token,
    )
    assert r.status_code == 200, r.text

    outra = decisoes(loja, lancar_contas_pagar=False)
    outra["xml"] = nota(item_cerveja(1), chave="35261012345678000199550010000088881000088888")
    outra["itens"] = outra["itens"][:1]  # só a cerveja: o biscoito já foi cadastrado na primeira
    r = client.post(URL, json=outra, headers=header_com_token)
    assert r.status_code == 201, r.text

    cerveja = linhas(db_session)[loja["produto_id"]]
    # Continua por unidade; o preço da nota foi convertido: 104,00 ÷ 24 = 4,33.
    assert (cerveja.embalagem_id, cerveja.fator, cerveja.ultimo_preco) == (None, 1, 433)


def test_mesmo_produto_em_dois_itens_da_nota_nao_derruba_a_importacao(client, db_session, header_com_token, loja):
    xml = nota(item_cerveja(1) + item_cerveja(2, codigo="CERV-CX12-B"))
    corpo = {
        "xml": xml,
        "itens": [
            {"indice": i, "acao": "vincular", "produto_id": loja["produto_id"], "embalagem_id": loja["FD"], "fator": 12}
            for i in (1, 2)
        ],
        "lancar_contas_pagar": False,
    }
    r = client.post(URL, json=corpo, headers=header_com_token)
    assert r.status_code == 201, r.text
    assert estoque(db_session, loja["produto_id"]) == 148  # 100 + 2 × 24
    assert db_session.query(ProdutoFornecedor).count() == 1
