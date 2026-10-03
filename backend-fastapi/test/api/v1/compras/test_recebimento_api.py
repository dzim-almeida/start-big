# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/compras/test_recebimento_api.py
# DESCRIÇÃO: Recebimento do pedido (docs/compras-plano.md, fase 3).
#
# Aqui o pedido vira ESTOQUE e DINHEIRO — o que não pode errar:
# - a entrada vai pelo livro de sempre (origem COMPRA), em unidades, com o
#   custo real por unidade, recalculando o custo médio;
# - recebido em partes, as contas a pagar somadas fecham o pedido AO CENTAVO
#   (frete incluído), seguindo as parcelas combinadas;
# - não se recebe mais do que falta, nem pedido que não foi enviado;
# - quem só recebe não mexe em custo nem vê preço;
# - sem o Financeiro, nenhuma conta nasce.
# ---------------------------------------------------------------------------

from datetime import date, timedelta

from app.db.models.conta_pagar import ContaPagar
from app.db.models.estoque import Estoque
from app.db.models.movimentacao_estoque import MovimentacaoEstoque
from app.db.models.produto_fornecedor import ProdutoFornecedor
from app.services.movimentacao_estoque import calcular_custo_medio

URL = "/api/v1/compras/pedidos"


def pedido_enviado(client, headers, cadastro, fardo, **extra) -> dict:
    """10 FD de cerveja a R$ 52,00 + frete R$ 10,00 = R$ 530,00, em 30/60."""
    corpo = {
        "fornecedor_id": cadastro["ambev"],
        "condicao_pagamento": "30/60",
        "frete": 1000,
        "itens": [{"produto_id": cadastro["produto_id"], "embalagem_id": fardo, "quantidade": 10, "custo_unitario": 5200}],
        **extra,
    }
    r = client.post(URL, json=corpo, headers=headers)
    assert r.status_code == 201, r.text
    p = r.json()
    assert client.post(f"{URL}/{p['id']}/enviar", headers=headers).status_code == 200
    return client.get(f"{URL}/{p['id']}", headers=headers).json()


def receber(client, headers, pedido, quantidade, **extra):
    item = pedido["itens"][0]
    corpo = {"itens": [{"pedido_item_id": item["id"], "quantidade": quantidade, **extra.pop("item", {})}], **extra}
    return client.post(f"{URL}/{pedido['id']}/recebimentos", json=corpo, headers=headers)


def contas(db_session) -> list[ContaPagar]:
    db_session.expire_all()
    return db_session.query(ContaPagar).order_by(ContaPagar.id).all()


def estoque(db_session, produto_id) -> Estoque:
    db_session.expire_all()
    return db_session.get(Estoque, produto_id)


# --- estoque ------------------------------------------------------------------------

def test_entrada_em_unidades_com_custo_real_e_media(client, db_session, header_com_token, cadastro, fardo):
    p = pedido_enviado(client, header_com_token, cadastro, fardo)
    r = receber(client, header_com_token, p, 6, numero_nota="4471")
    assert r.status_code == 201, r.text

    e = estoque(db_session, cadastro["produto_id"])
    assert e.quantidade == 10 + 72  # 6 fardos de 12
    # R$ 52,00 o fardo = R$ 4,33 a lata (meio para cima), e a média recalcula.
    assert e.custo_medio == calcular_custo_medio(
        quantidade_anterior=10, custo_anterior=300, quantidade_entrada=72, custo_entrada=433)

    [mov] = db_session.query(MovimentacaoEstoque).filter(MovimentacaoEstoque.origem == "COMPRA").all()
    assert (mov.quantidade, mov.custo_unitario, mov.embalagem_sigla, mov.quantidade_embalagem) == (72, 433, "FD", 6)
    assert mov.recebimento_compra_id is not None
    assert "PC-000001" in mov.observacao and "NF 4471" in mov.observacao


def test_parcial_e_depois_o_resto(client, db_session, header_com_token, cadastro, fardo):
    p = pedido_enviado(client, header_com_token, cadastro, fardo)
    r = receber(client, header_com_token, p, 6)
    assert (r.json()["situacao"], r.json()["itens"][0]["pendente"]) == ("PARCIAL", 4)
    r = receber(client, header_com_token, r.json(), 4)
    assert (r.json()["situacao"], r.json()["itens"][0]["pendente"]) == ("RECEBIDO", 0)
    assert [h["acao"] for h in r.json()["historico"][:2]] == ["RECEBIDO", "RECEBIDO"]
    assert len(r.json()["recebimentos"]) == 2


def test_ultimo_preco_do_fornecedor_e_atualizado(client, db_session, header_com_token, cadastro, fardo):
    p = pedido_enviado(client, header_com_token, cadastro, fardo)
    receber(client, header_com_token, p, 2, item={"custo_unitario": 5000})
    db_session.expire_all()
    linha = db_session.query(ProdutoFornecedor).filter_by(
        produto_id=cadastro["produto_id"], fornecedor_id=cadastro["ambev"]).one()
    assert (linha.ultimo_preco, linha.ultima_compra_em) == (5000, date.today())


# --- contas a pagar ---------------------------------------------------------------

def test_contas_fecham_o_pedido_ao_centavo_em_duas_chegadas(
    client, db_session, header_com_token, cadastro, fardo, licenca
):
    licenca("COMPRAS", "FINANCEIRO")
    p = pedido_enviado(client, header_com_token, cadastro, fardo)

    primeira = receber(client, header_com_token, p, 6, numero_nota="100").json()
    # 6 × 52,00 = 312,00 + frete proporcional (312/520 de 10,00 = 6,00) = 318,00, em 2 parcelas.
    assert [(c.valor, c.vencimento) for c in contas(db_session)] == [
        (15900, date.today() + timedelta(days=30)), (15900, date.today() + timedelta(days=60))]
    assert primeira["recebimentos"][0]["valor_total"] == 31800

    receber(client, header_com_token, primeira, 4)
    todas = contas(db_session)
    # 4 × 52,00 = 208,00 + o RESTO do frete (4,00) = 212,00.
    assert [c.valor for c in todas[2:]] == [10600, 10600]
    assert sum(c.valor for c in todas) == 53000 == p["valor_total"]
    assert all(c.fornecedor_id == cadastro["ambev"] and c.recebimento_compra_id for c in todas)
    assert "Pedido PC-000001 — Ambev — NF 100" == todas[0].descricao
    assert (todas[0].parcela_numero, todas[0].parcela_total) == (1, 2)


def test_sem_o_financeiro_nenhuma_conta(client, db_session, header_com_token, cadastro, fardo, licenca):
    licenca("COMPRAS")  # licença que fala, e sem FINANCEIRO
    p = pedido_enviado(client, header_com_token, cadastro, fardo)
    r = receber(client, header_com_token, p, 10)
    assert r.status_code == 201
    assert contas(db_session) == []
    assert r.json()["recebimentos"][0]["contas_pagar_lancadas"] == 0


def test_lojista_pode_nao_lancar_as_contas(client, db_session, header_com_token, cadastro, fardo, licenca):
    licenca("COMPRAS", "FINANCEIRO")
    p = pedido_enviado(client, header_com_token, cadastro, fardo)
    receber(client, header_com_token, p, 10, lancar_contas_pagar=False)
    assert contas(db_session) == []


def test_a_vista_vira_uma_conta_no_dia(client, db_session, header_com_token, cadastro, fardo, licenca):
    licenca("COMPRAS", "FINANCEIRO")
    p = pedido_enviado(client, header_com_token, cadastro, fardo, condicao_pagamento=None, frete=0)
    receber(client, header_com_token, p, 10)
    [conta] = contas(db_session)
    assert (conta.valor, conta.vencimento, conta.parcela_total) == (52000, date.today(), None)


# --- recusas -------------------------------------------------------------------------

def test_nao_recebe_mais_do_que_falta(client, db_session, header_com_token, cadastro, fardo):
    p = pedido_enviado(client, header_com_token, cadastro, fardo)
    r = receber(client, header_com_token, p, 11)
    assert r.status_code == 422 and "faltam só 10" in r.json()["detail"]
    assert estoque(db_session, cadastro["produto_id"]).quantidade == 10


def test_nada_chegou_e_recusado(client, header_com_token, cadastro, fardo):
    p = pedido_enviado(client, header_com_token, cadastro, fardo)
    assert receber(client, header_com_token, p, 0).status_code == 422


def test_rascunho_e_cancelado_nao_recebem(client, header_com_token, cadastro, fardo):
    r = client.post(URL, json={"fornecedor_id": cadastro["ambev"], "itens": [
        {"produto_id": cadastro["produto_id"], "quantidade": 1}]}, headers=header_com_token)
    rascunho = client.get(f"{URL}/{r.json()['id']}", headers=header_com_token).json()
    assert receber(client, header_com_token, rascunho, 1).status_code == 409

    client.post(f"{URL}/{rascunho['id']}/cancelar", json={"motivo": "Teste"}, headers=header_com_token)
    assert receber(client, header_com_token, rascunho, 1).status_code == 409


def test_recebido_em_parte_nao_volta_nem_cancela(client, header_com_token, cadastro, fardo):
    p = pedido_enviado(client, header_com_token, cadastro, fardo)
    receber(client, header_com_token, p, 3)
    assert client.post(f"{URL}/{p['id']}/voltar-rascunho", json={"motivo": "x" * 5}, headers=header_com_token).status_code == 409
    assert client.post(f"{URL}/{p['id']}/cancelar", json={"motivo": "x" * 5}, headers=header_com_token).status_code == 409


def test_erro_no_meio_nao_deixa_nada_pela_metade(client, db_session, header_com_token, cadastro, fardo):
    corpo = {"fornecedor_id": cadastro["ambev"], "itens": [
        {"produto_id": cadastro["produto_id"], "embalagem_id": fardo, "quantidade": 2, "custo_unitario": 5200},
        {"produto_id": cadastro["outro_id"], "quantidade": 1, "custo_unitario": 700},
    ]}
    p = client.post(URL, json=corpo, headers=header_com_token).json()
    client.post(f"{URL}/{p['id']}/enviar", headers=header_com_token)
    cerveja, refri = p["itens"]
    r = client.post(f"{URL}/{p['id']}/recebimentos", json={"itens": [
        {"pedido_item_id": cerveja["id"], "quantidade": 2},
        {"pedido_item_id": refri["id"], "quantidade": 5},  # pediu 1
    ]}, headers=header_com_token)
    assert r.status_code == 422
    assert estoque(db_session, cadastro["produto_id"]).quantidade == 10
    assert db_session.query(MovimentacaoEstoque).filter(MovimentacaoEstoque.origem == "COMPRA").count() == 0


# --- encerrar saldo -------------------------------------------------------------------

def test_encerrar_saldo_junto_com_o_recebimento(client, db_session, header_com_token, cadastro, fardo, licenca):
    licenca("COMPRAS", "FINANCEIRO")
    p = pedido_enviado(client, header_com_token, cadastro, fardo)
    r = receber(client, header_com_token, p, 7, encerrar_saldo=True).json()
    item = r["itens"][0]
    assert (r["situacao"], item["quantidade_recebida"], item["quantidade_cancelada"], item["pendente"]) == (
        "RECEBIDO", 7, 3, 0)
    assert "Saldo encerrado" in r["historico"][0]["motivo"]
    # Sendo a última chegada, leva o frete inteiro: 7 × 52,00 + 10,00 = 374,00.
    assert sum(c.valor for c in contas(db_session)) == 37400


def test_encerrar_saldo_depois(client, header_com_token, cadastro, fardo):
    p = pedido_enviado(client, header_com_token, cadastro, fardo)
    assert client.post(f"{URL}/{p['id']}/encerrar", json={"motivo": "Acabou no fornecedor"},
                       headers=header_com_token).status_code == 409  # nada recebido: cancela-se, não encerra
    receber(client, header_com_token, p, 4)
    r = client.post(f"{URL}/{p['id']}/encerrar", json={"motivo": "Acabou no fornecedor"}, headers=header_com_token)
    assert r.status_code == 200, r.text
    assert (r.json()["situacao"], r.json()["itens"][0]["quantidade_cancelada"]) == ("RECEBIDO", 6)
    assert r.json()["historico"][0]["acao"] == "SALDO_ENCERRADO"


# --- quem só recebe (o almoxarife) ---------------------------------------------------------

def test_almoxarife_recebe_sem_ver_preco_e_sem_mudar_custo(client, db_session, header_com_token, cadastro, fardo):
    from app.core.depends import get_current_active_user
    from app.db.models.usuario import Usuario
    from app.main import app

    p = pedido_enviado(client, header_com_token, cadastro, fardo)
    # Usuário que EXISTE (o recebimento grava quem recebeu, com FK).
    usuario_id = db_session.query(Usuario).first().id
    app.dependency_overrides[get_current_active_user] = lambda: {
        "sub": str(usuario_id), "nome": "Almoxarife", "empresa_id": 1, "cargo": "Almoxarife", "is_master": False,
        "permissoes": {"recebimento_compra": True, "view_receiving": True, "receive_purchases": True},
    }

    visto = client.get(f"{URL}/{p['id']}").json()
    assert visto["itens"][0]["custo_unitario"] is None and visto["valor_total"] is None

    r = receber(client, {}, visto, 2, item={"custo_unitario": 1})  # tenta mudar o custo
    assert r.status_code == 201, r.text
    assert r.json()["recebimentos"][0]["valor_total"] is None
    db_session.expire_all()
    [mov] = db_session.query(MovimentacaoEstoque).filter(MovimentacaoEstoque.origem == "COMPRA").all()
    assert mov.custo_unitario == 433  # o do pedido, não o que ele mandou
    assert r.json()["recebimentos"][0]["recebido_por_nome"] == "Almoxarife"

    assert client.post(URL, json={"fornecedor_id": cadastro["ambev"], "itens": []}).status_code == 403
    app.dependency_overrides.pop(get_current_active_user, None)


def test_visualizar_compras_nao_recebe(client, header_com_token, cadastro, fardo, como):
    p = pedido_enviado(client, header_com_token, cadastro, fardo)
    como(compra=True, view_purchases=True)
    assert receber(client, {}, p, 1).status_code == 403


# --- leitura ---------------------------------------------------------------------------

def test_lista_a_receber(client, header_com_token, cadastro, fardo):
    a = pedido_enviado(client, header_com_token, cadastro, fardo)
    client.post(URL, json={"fornecedor_id": cadastro["ambev"], "itens": []}, headers=header_com_token)  # rascunho
    r = client.get(URL, params={"a_receber": True}, headers=header_com_token).json()
    assert [p["id"] for p in r["itens"]] == [a["id"]]


def test_codigos_que_o_leitor_pode_bipar(client, db_session, header_com_token, cadastro, fardo):
    from app.db.models.produto import Produto
    from app.db.models.produto_embalagem import ProdutoEmbalagem

    db_session.get(Produto, cadastro["produto_id"]).codigo_barras = "7891000000001"
    db_session.get(ProdutoEmbalagem, fardo).codigo_barras = "17891000000008"
    db_session.commit()
    p = pedido_enviado(client, header_com_token, cadastro, fardo)
    assert p["itens"][0]["codigos_barras"] == ["17891000000008", "7891000000001", "CERV-350"]


def test_necessidades_contam_so_o_que_falta_chegar(client, db_session, header_com_token, cadastro, fardo):
    estoque(db_session, cadastro["produto_id"]).quantidade_minima = 200
    db_session.commit()
    client.put(f"/api/v1/compras/produtos/{cadastro['produto_id']}/fornecedores", json={"fornecedores": [
        {"fornecedor_id": cadastro["ambev"], "embalagem_id": fardo, "padrao": True}]}, headers=header_com_token)
    p = pedido_enviado(client, header_com_token, cadastro, fardo)
    receber(client, header_com_token, p, 6)
    [grupo] = client.get("/api/v1/compras/necessidades", headers=header_com_token).json()
    [item] = grupo["itens"]
    # Estoque 82 (10 + 72) e a caminho só os 4 fardos que faltam (48).
    assert (item["saldo"], item["em_pedido"]) == (82, 48)
