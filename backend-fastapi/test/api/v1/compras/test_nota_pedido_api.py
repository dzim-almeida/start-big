# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/compras/test_nota_pedido_api.py
# DESCRIÇÃO: A XML da NF-e casada com o pedido (docs/compras-plano.md, fase 4).
#
# O que não pode errar:
# - SEM o módulo, a prévia e a importação da XML ficam exatamente como eram;
# - o estoque entra UMA vez (pela XML), e o pedido só registra o recebimento;
# - divergência (a menos, a mais, preço) só AVISA (D11);
# - com duplicatas na nota, as contas são as da nota e as do pedido NÃO nascem;
#   sem duplicatas, nascem as parcelas do pedido — nunca em dobro (D8);
# - pedido de outro fornecedor, cancelado ou sem o módulo: recusa, sem lançar nada.
# ---------------------------------------------------------------------------

import pytest

from app.db.models.conta_pagar import ContaPagar
from app.db.models.fornecedor import Fornecedor
from app.db.models.movimentacao_estoque import MovimentacaoEstoque
from app.db.models.nota_entrada import NotaEntrada
from app.db.models.recebimento_compra import RecebimentoCompra
from test.api.v1.embalagens.test_entrada_xml import decisoes
from test.api.v1.embalagens.test_venda_por_embalagem import estoque, loja  # noqa: F401 — `loja` é fixture
from test.core.nfe_exemplo import CNPJ_FORNECEDOR, nota

URL_XML = "/api/v1/estoque/nfe-entrada"
URL_PEDIDOS = "/api/v1/compras/pedidos"


@pytest.fixture
def distribuidora(db_session) -> int:
    """O emitente da nota de exemplo, já cadastrado (o pedido nasce antes da nota)."""
    f = Fornecedor(nome="DISTRIBUIDORA DE BEBIDAS LTDA", nome_fantasia="DISTRIBEB", cnpj=CNPJ_FORNECEDOR,
                   tipo="produto", ativo=True)
    db_session.add(f)
    db_session.commit()
    return f.id


def pedido(client, headers, fornecedor_id, loja, quantidade=2, custo=5200, enviar=True, **extra) -> dict:
    r = client.post(URL_PEDIDOS, json={
        "fornecedor_id": fornecedor_id,
        "itens": [{"produto_id": loja["produto_id"], "embalagem_id": loja["FD"], "quantidade": quantidade,
                   "custo_unitario": custo}],
        **extra,
    }, headers=headers)
    assert r.status_code == 201, r.text
    if enviar:
        assert client.post(f"{URL_PEDIDOS}/{r.json()['id']}/enviar", headers=headers).status_code == 200
    return client.get(f"{URL_PEDIDOS}/{r.json()['id']}", headers=headers).json()


def ler(client, headers, xml=None):
    xml = xml or nota()
    r = client.post(f"{URL_XML}/ler", files={"arquivo": ("nota.xml", xml.encode(), "text/xml")}, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def importar(client, headers, loja, **extra):
    return client.post(f"{URL_XML}/importar", json=decisoes(loja, **extra), headers=headers)


# --- sem o módulo, tudo como antes -------------------------------------------------

def test_sem_o_modulo_a_previa_nao_muda(client, header_com_token, loja, distribuidora, licenca):
    pedido(client, header_com_token, distribuidora, loja)
    licenca()  # licença sem resposta: Compras NÃO está ativo
    previa = ler(client, header_com_token)
    assert (previa["pedidos_abertos"], previa["pedido_sugerido_id"], previa["pedido_avisos"]) == ([], None, [])
    assert all(i["pedido_avisos"] == [] for i in previa["itens"])


def test_sem_o_modulo_nao_liga_a_pedido(client, db_session, header_com_token, loja, distribuidora, licenca):
    p = pedido(client, header_com_token, distribuidora, loja)
    licenca()
    r = importar(client, header_com_token, loja, pedido_id=p["id"])
    assert r.status_code == 422 and "módulo Compras" in r.json()["detail"]
    assert db_session.query(NotaEntrada).count() == 0


# --- prévia --------------------------------------------------------------------------

def test_previa_sugere_o_pedido_e_confere_sem_divergencia(client, header_com_token, loja, distribuidora):
    p = pedido(client, header_com_token, distribuidora, loja)  # 2 FD a 52,00 — exatamente o que a nota traz
    previa = ler(client, header_com_token)
    assert [x["codigo"] for x in previa["pedidos_abertos"]] == [p["codigo"]]
    assert previa["pedido_sugerido_id"] == p["id"]
    cerveja = previa["itens"][0]
    assert cerveja["pedido_avisos"] == []
    assert previa["pedido_avisos"] == []


def test_previa_avisa_preco_e_quantidade(client, header_com_token, loja, distribuidora):
    pedido(client, header_com_token, distribuidora, loja, quantidade=5, custo=4800)
    [avisos] = [i["pedido_avisos"] for i in ler(client, header_com_token)["itens"][:1]]
    assert any("veio a menos — 2 de 5 FD" in a for a in avisos)
    assert any("8,3% mais caro" in a and "R$ 4,33/un" in a and "R$ 4,00/un" in a for a in avisos)


def test_previa_avisa_o_que_nao_veio(client, db_session, header_com_token, loja, distribuidora):
    from app.db.models.estoque import Estoque
    from app.db.models.produto import Produto

    refri = Produto(nome="Refrigerante 2L", codigo_produto="REFRI-2L", unidade_medida="UN", ativo=True)
    refri.estoque = Estoque(quantidade=0, valor_varejo=900)
    db_session.add(refri)
    db_session.commit()
    r = client.post(URL_PEDIDOS, json={"fornecedor_id": distribuidora, "itens": [
        {"produto_id": loja["produto_id"], "embalagem_id": loja["FD"], "quantidade": 2, "custo_unitario": 5200},
        {"produto_id": refri.id, "quantidade": 6, "custo_unitario": 700},
    ]}, headers=header_com_token)
    client.post(f"{URL_PEDIDOS}/{r.json()['id']}/enviar", headers=header_com_token)
    assert ler(client, header_com_token)["pedido_avisos"] == [
        "'Refrigerante 2L': o pedido espera 6 UN e não veio na nota."]


def test_pedido_rascunho_nao_aparece(client, header_com_token, loja, distribuidora):
    pedido(client, header_com_token, distribuidora, loja, enviar=False)
    assert ler(client, header_com_token)["pedidos_abertos"] == []


# --- importação ligada ao pedido ------------------------------------------------------

def test_estoque_entra_uma_vez_e_o_pedido_fica_recebido(client, db_session, header_com_token, loja, distribuidora):
    p = pedido(client, header_com_token, distribuidora, loja)
    r = importar(client, header_com_token, loja, pedido_id=p["id"], lancar_contas_pagar=False)
    assert r.status_code == 201, r.text
    res = r.json()
    assert (res["pedido_codigo"], res["pedido_situacao"]) == (p["codigo"], "RECEBIDO")
    # O biscoito veio na nota e não estava no pedido: entra, e o lojista é avisado.
    assert res["pedido_avisos"] == ["1 item(ns) da nota não estão no pedido (entram no estoque assim mesmo)."]

    assert estoque(db_session, loja["produto_id"]) == 124  # 100 + 24, uma vez só
    db_session.expire_all()
    [rec] = db_session.query(RecebimentoCompra).all()
    assert (rec.nota_entrada_id, rec.numero_nota, rec.valor_total) == (res["nota_entrada_id"], "1234", 10400)
    mov = db_session.query(MovimentacaoEstoque).filter(
        MovimentacaoEstoque.origem == "NFE_ENTRADA", MovimentacaoEstoque.produto_id == loja["produto_id"]).one()
    assert mov.recebimento_compra_id == rec.id
    assert db_session.query(MovimentacaoEstoque).filter(MovimentacaoEstoque.origem == "COMPRA").count() == 0


def test_parte_do_pedido_fica_parcial(client, header_com_token, loja, distribuidora):
    p = pedido(client, header_com_token, distribuidora, loja, quantidade=5)
    res = importar(client, header_com_token, loja, pedido_id=p["id"], lancar_contas_pagar=False).json()
    assert res["pedido_situacao"] == "PARCIAL"
    assert any("veio a menos" in a for a in res["pedido_avisos"])
    depois = client.get(f"{URL_PEDIDOS}/{p['id']}", headers=header_com_token).json()
    assert depois["itens"][0]["pendente"] == 3


def test_com_duplicatas_as_contas_sao_so_as_da_nota(
    client, db_session, header_com_token, loja, distribuidora, licenca
):
    licenca("COMPRAS", "FINANCEIRO")
    p = pedido(client, header_com_token, distribuidora, loja, condicao_pagamento="30/60/90")
    res = importar(client, header_com_token, loja, pedido_id=p["id"], lancar_contas_pagar=True).json()
    db_session.expire_all()
    contas = db_session.query(ContaPagar).all()
    assert res["contas_pagar_lancadas"] == 2 == len(contas)  # as 2 duplicatas da nota, nada do pedido
    assert all(c.recebimento_compra_id is None for c in contas)


def test_sem_duplicatas_nascem_as_parcelas_do_pedido(
    client, db_session, header_com_token, loja, distribuidora, licenca
):
    licenca("COMPRAS", "FINANCEIRO")
    p = pedido(client, header_com_token, distribuidora, loja, condicao_pagamento="30/60")
    corpo = decisoes(loja, pedido_id=p["id"], lancar_contas_pagar=True)
    corpo["xml"] = nota(duplicatas=False)  # a mesma nota, sem <dup>
    r = client.post(f"{URL_XML}/importar", json=corpo, headers=header_com_token)
    assert r.status_code == 201, r.text
    db_session.expire_all()
    contas = db_session.query(ContaPagar).order_by(ContaPagar.id).all()
    # Só a cerveja é do pedido: 2 FD pela nota = R$ 104,00, nas parcelas dele
    # (30/60). O biscoito, fora do pedido, não vira conta por aqui.
    assert [c.valor for c in contas] == [5200, 5200]
    assert all(c.recebimento_compra_id is not None for c in contas)


# --- recusas ---------------------------------------------------------------------------

def test_pedido_de_outro_fornecedor(client, db_session, header_com_token, loja, distribuidora):
    outro = Fornecedor(nome="Outro Distribuidor", cnpj="55555555000155", tipo="produto", ativo=True)
    db_session.add(outro)
    db_session.commit()
    p = pedido(client, header_com_token, outro.id, loja)
    r = importar(client, header_com_token, loja, pedido_id=p["id"])
    assert r.status_code == 422 and "outro fornecedor" in r.json()["detail"]
    assert db_session.query(NotaEntrada).count() == 0
    assert estoque(db_session, loja["produto_id"]) == 100


def test_pedido_cancelado(client, db_session, header_com_token, loja, distribuidora):
    p = pedido(client, header_com_token, distribuidora, loja)
    client.post(f"{URL_PEDIDOS}/{p['id']}/cancelar", json={"motivo": "Teste"}, headers=header_com_token)
    r = importar(client, header_com_token, loja, pedido_id=p["id"])
    assert r.status_code == 409
    assert db_session.query(NotaEntrada).count() == 0


def test_importar_sem_ligar_continua_igual(client, db_session, header_com_token, loja, distribuidora):
    p = pedido(client, header_com_token, distribuidora, loja)
    r = importar(client, header_com_token, loja, lancar_contas_pagar=False)  # sem pedido_id
    assert r.status_code == 201
    assert (r.json()["pedido_codigo"], r.json()["pedido_avisos"]) == (None, [])
    depois = client.get(f"{URL_PEDIDOS}/{p['id']}", headers=header_com_token).json()
    assert depois["situacao"] == "ENVIADO"  # o pedido não foi tocado
