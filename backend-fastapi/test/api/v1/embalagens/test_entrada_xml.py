# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/embalagens/test_entrada_xml.py
# DESCRIÇÃO: Entrada de mercadoria pela XML da NF-e (docs/entrada-xml-nfe-plano.md).
#
# O que não pode errar: a prévia não grava nada; a importação dá entrada na
# quantidade e no custo DA NOTA (não da tela); a mesma chave não entra duas
# vezes; erro no meio não deixa nada pela metade; o vínculo é lembrado.
# ---------------------------------------------------------------------------

from datetime import date

from app.db.models.conta_pagar import ContaPagar
from app.db.models.empresa import Empresa
from app.db.models.fornecedor import Fornecedor
from app.db.models.movimentacao_estoque import MovimentacaoEstoque
from app.db.models.nota_entrada import NotaEntrada
from app.db.models.produto import Produto
from test.api.v1.embalagens.test_venda_por_embalagem import estoque, loja  # noqa: F401 — `loja` é fixture
from test.core.nfe_exemplo import CNPJ_FORNECEDOR, CNPJ_LOJA, item_biscoito, item_caixa_sem_fator, nota

URL = "/api/v1/estoque/nfe-entrada"
OUTRA_CHAVE = "35261012345678000199550010000099991000099999"


def ler(client, headers, xml: str):
    return client.post(f"{URL}/ler", files={"arquivo": ("nota.xml", xml.encode(), "text/xml")}, headers=headers)


def decisoes(loja, **extra) -> dict:
    """Cerveja → o fardo FD da `loja`; biscoito → produto novo."""
    return {
        "xml": nota(),
        "itens": [
            {"indice": 1, "acao": "vincular", "produto_id": loja["produto_id"], "embalagem_id": loja["FD"], "fator": 12},
            {"indice": 2, "acao": "criar", "fator": 1, "novo": {
                "nome": "Biscoito Recheado 140g", "codigo_produto": "BISC-140", "valor_varejo": 450}},
        ],
        "lancar_contas_pagar": True,
        **extra,
    }


def test_previa_reconhece_o_fardo_e_nao_grava_nada(client, db_session, header_com_token, loja):
    r = ler(client, header_com_token, nota())
    assert r.status_code == 200, r.text
    previa = r.json()
    assert (previa["numero"], previa["valor_total"], previa["fornecedor"]["id"]) == ("1234", 13000, None)
    assert [d["valor"] for d in previa["duplicatas"]] == [6300, 6300]

    cerveja, biscoito = previa["itens"]
    assert (cerveja["reconhecido_por"], cerveja["produto"]["id"], cerveja["embalagem_sigla"], cerveja["fator"]) == (
        "embalagem", loja["produto_id"], "FD", 12)
    assert cerveja["custo_total"] == 10400
    assert cerveja["fiscal_sugerido"]["icms_st"] is True
    assert (biscoito["reconhecido_por"], biscoito["produto"]) == (None, None)
    assert biscoito["fiscal_sugerido"]["ncm"] == "19053100"

    db_session.expire_all()
    assert db_session.query(NotaEntrada).count() == 0
    assert db_session.query(Fornecedor).count() == 0
    assert estoque(db_session, loja["produto_id"]) == 100


def test_importa_estoque_custo_produto_novo_fornecedor_e_parcelas(client, db_session, header_com_token, loja):
    r = client.post(f"{URL}/importar", json=decisoes(loja), headers=header_com_token)
    assert r.status_code == 201, r.text
    res = r.json()
    assert (res["itens_lancados"], res["produtos_criados"], res["contas_pagar_lancadas"], res["fornecedor_criado"]) == (
        2, 1, 2, True)

    db_session.expire_all()
    # 2 FD de 12 = 24 latas, a 104,00 ÷ 24 = 4,33 cada.
    assert estoque(db_session, loja["produto_id"]) == 124
    movs = db_session.query(MovimentacaoEstoque).filter(MovimentacaoEstoque.origem == "NFE_ENTRADA").all()
    por_produto = {m.produto_id: m for m in movs}
    cerveja = por_produto[loja["produto_id"]]
    assert (cerveja.quantidade, cerveja.custo_unitario, cerveja.embalagem_sigla, cerveja.quantidade_embalagem) == (
        24, 433, "FD", 2)
    assert cerveja.nota_entrada_id == res["nota_entrada_id"]
    assert "NF-e 1234/1" in cerveja.observacao

    biscoito = db_session.query(Produto).filter(Produto.codigo_produto == "BISC-140").one()
    assert (biscoito.estoque.quantidade, biscoito.estoque.custo_medio, biscoito.estoque.valor_varejo) == (10, 260, 450)
    assert (biscoito.fiscal.ncm, biscoito.fiscal.cfop_padrao) == ("19053100", "5102")
    assert biscoito.fornecedor_id == res["fornecedor_id"]

    fornecedor = db_session.get(Fornecedor, res["fornecedor_id"])
    assert (fornecedor.cnpj, fornecedor.nome_fantasia) == (CNPJ_FORNECEDOR, "DISTRIBEB")
    assert fornecedor.endereco[0].cidade == "SAO PAULO"

    contas = db_session.query(ContaPagar).order_by(ContaPagar.vencimento).all()
    assert [(c.valor, c.vencimento, c.fornecedor_id, c.parcela_numero) for c in contas] == [
        (6300, date(2026, 10, 31), fornecedor.id, 1), (6300, date(2026, 11, 30), fornecedor.id, 2)]

    lista = client.get(URL, headers=header_com_token).json()
    assert [(n["numero"], n["itens_lancados"], n["contas_pagar_lancadas"]) for n in lista] == [("1234", 2, 2)]


def test_mesma_nota_nao_entra_duas_vezes(client, db_session, header_com_token, loja):
    assert client.post(f"{URL}/importar", json=decisoes(loja), headers=header_com_token).status_code == 201
    r = client.post(f"{URL}/importar", json=decisoes(loja), headers=header_com_token)
    assert r.status_code == 409, r.text
    assert "já foi importada" in r.json()["detail"]
    db_session.expire_all()
    assert estoque(db_session, loja["produto_id"]) == 124
    assert ler(client, header_com_token, nota()).json()["ja_importada_em"] is not None


def test_erro_no_meio_nao_deixa_nada_pela_metade(client, db_session, header_com_token, loja):
    corpo = decisoes(loja)
    corpo["itens"][1]["novo"]["codigo_produto"] = "CERV-350"  # SKU que já existe: o 2º item falha
    r = client.post(f"{URL}/importar", json=corpo, headers=header_com_token)
    assert r.status_code >= 400, r.text
    db_session.expire_all()
    assert estoque(db_session, loja["produto_id"]) == 100  # o 1º item não ficou lançado
    assert db_session.query(NotaEntrada).count() == 0
    assert db_session.query(Fornecedor).count() == 0
    assert db_session.query(ContaPagar).count() == 0


def test_item_sem_decisao_e_recusado(client, header_com_token, loja):
    corpo = decisoes(loja)
    corpo["itens"] = corpo["itens"][:1]
    r = client.post(f"{URL}/importar", json=corpo, headers=header_com_token)
    assert r.status_code == 422 and "item(ns) 2" in r.json()["detail"]


def test_proxima_nota_do_fornecedor_vem_pelo_vinculo(client, header_com_token, loja):
    assert client.post(f"{URL}/importar", json=decisoes(loja, lancar_contas_pagar=False),
                       headers=header_com_token).status_code == 201
    previa = ler(client, header_com_token, nota(item_biscoito(1), chave=OUTRA_CHAVE)).json()
    [biscoito] = previa["itens"]
    assert previa["fornecedor"]["id"] is not None
    assert (biscoito["reconhecido_por"], biscoito["produto"]["nome"]) == ("vinculo", "Biscoito Recheado 140g")


def test_aviso_quando_a_nota_e_de_outro_cnpj(client, db_session, header_com_token, loja):
    for empresa in db_session.query(Empresa).all():
        empresa.documento = "11111111000111"
    db_session.commit()
    avisos = ler(client, header_com_token, nota(destinatario=CNPJ_LOJA)).json()["avisos"]
    assert any("outro CNPJ" in a for a in avisos)


def test_nfce_e_recusada_na_previa(client, header_com_token, loja):
    r = ler(client, header_com_token, nota(modelo="65"))
    assert r.status_code == 422 and "NFC-e" in r.json()["detail"]


# ── "2 CX" sem dizer quantas vêm na caixa ────────────────────────────────────

def _refri(fator: int, confirmado: bool = False) -> dict:
    return {
        "xml": nota(item_caixa_sem_fator()),
        "itens": [{"indice": 1, "acao": "criar", "fator": fator, "fator_confirmado": confirmado, "novo": {
            "nome": "Refrigerante 2L", "codigo_produto": "REFRI-2L", "valor_varejo": 1000}}],
    }


def test_caixa_sem_fator_fica_pendente_e_o_servidor_recusa(client, db_session, header_com_token, loja):
    [item] = ler(client, header_com_token, nota(item_caixa_sem_fator())).json()["itens"]
    assert (item["fator"], item["fator_a_confirmar"]) == (1, True)

    r = client.post(f"{URL}/importar", json=_refri(1), headers=header_com_token)
    assert r.status_code == 422 and "quantas unidades" in r.json()["detail"]
    db_session.expire_all()
    assert db_session.query(Produto).filter(Produto.codigo_produto == "REFRI-2L").count() == 0


def test_caixa_com_fator_informado_entra_em_unidades(client, db_session, header_com_token, loja):
    assert client.post(f"{URL}/importar", json=_refri(6), headers=header_com_token).status_code == 201
    db_session.expire_all()
    refri = db_session.query(Produto).filter(Produto.codigo_produto == "REFRI-2L").one()
    assert (refri.estoque.quantidade, refri.estoque.custo_medio) == (12, 1000)  # 120,00 ÷ 12

    # A próxima nota do fornecedor vem com o fator lembrado, sem pendência.
    outra = nota(item_caixa_sem_fator(), chave="35261012345678000199550010000077771000077777")
    [item] = ler(client, header_com_token, outra).json()["itens"]
    assert (item["reconhecido_por"], item["fator"], item["fator_a_confirmar"]) == ("vinculo", 6, False)


def test_e_1_mesmo_quando_o_lojista_confirma(client, db_session, header_com_token, loja):
    assert client.post(f"{URL}/importar", json=_refri(1, confirmado=True), headers=header_com_token).status_code == 201
    db_session.expire_all()
    refri = db_session.query(Produto).filter(Produto.codigo_produto == "REFRI-2L").one()
    assert refri.estoque.quantidade == 2
