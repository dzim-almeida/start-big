# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/compras/test_necessidades_api.py
# DESCRIÇÃO: Necessidades de compra e geração de rascunhos (plano, fase 2).
#
# O que não pode errar: o que está a caminho desconta (senão o mesmo produto
# seria pedido duas vezes); rascunho NÃO desconta mas aparece; a quantidade
# vem na unidade de compra do fornecedor; o mais barato é avisado (D18).
# ---------------------------------------------------------------------------

from datetime import date, timedelta

from app.db.models.estoque import Estoque
from app.db.models.pedido_compra import PedidoCompra
from app.db.models.produto import Produto

URL = "/api/v1/compras/necessidades"


def minimo(db_session, produto_id, minimo, ideal=None, saldo=None):
    estoque = db_session.get(Estoque, produto_id)
    estoque.quantidade_minima = minimo
    estoque.quantidade_ideal = ideal
    if saldo is not None:
        estoque.quantidade = saldo
    db_session.commit()


def fornecedores(client, headers, produto_id, lista):
    r = client.put(f"/api/v1/compras/produtos/{produto_id}/fornecedores", json={"fornecedores": lista}, headers=headers)
    assert r.status_code == 200, r.text


def necessidades(client, headers) -> list[dict]:
    r = client.get(URL, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def itens(grupos) -> dict[int, dict]:
    return {i["produto_id"]: i for g in grupos for i in g["itens"]}


def test_so_entra_quem_tem_minimo_e_esta_abaixo(client, db_session, header_com_token, cadastro):
    assert necessidades(client, header_com_token) == []  # ninguém tem mínimo
    minimo(db_session, cadastro["produto_id"], 24, 60)   # saldo 10 ≤ 24
    minimo(db_session, cadastro["outro_id"], 2)          # saldo 5 > 2
    assert list(itens(necessidades(client, header_com_token))) == [cadastro["produto_id"]]


def test_sugere_na_unidade_de_compra_do_principal(client, db_session, header_com_token, cadastro, fardo):
    minimo(db_session, cadastro["produto_id"], 24, 60)  # faltam 50 latas → 5 fardos de 12
    fornecedores(client, header_com_token, cadastro["produto_id"], [
        {"fornecedor_id": cadastro["ambev"], "embalagem_id": fardo, "ultimo_preco": 5200, "padrao": True}])
    [grupo] = necessidades(client, header_com_token)
    [item] = grupo["itens"]
    assert (grupo["fornecedor_nome"], item["unidade_compra"], item["fator"], item["sugestao"]) == ("Ambev", "FD", 12, 5)
    assert (item["saldo"], item["minimo"], item["ideal"], item["ultimo_preco"]) == (10, 24, 60, 5200)


def test_o_que_esta_a_caminho_desconta(client, db_session, header_com_token, cadastro, fardo):
    minimo(db_session, cadastro["produto_id"], 24, 60)
    fornecedores(client, header_com_token, cadastro["produto_id"], [
        {"fornecedor_id": cadastro["ambev"], "embalagem_id": fardo, "padrao": True}])
    r = client.post(f"{URL}/gerar-pedidos", json={"itens": [
        {"produto_id": cadastro["produto_id"], "fornecedor_id": cadastro["ambev"], "quantidade": 5}]},
        headers=header_com_token)
    [pedido] = r.json()

    # Rascunho NÃO desconta, mas aparece.
    [item] = itens(necessidades(client, header_com_token)).values()
    assert (item["em_rascunho"], item["rascunhos"], item["sugestao"]) == (60, [pedido["codigo"]], 5)

    # Enviado desconta: 10 + 60 a caminho > 24 → some da lista.
    client.post(f"/api/v1/compras/pedidos/{pedido['id']}/enviar", headers=header_com_token)
    assert necessidades(client, header_com_token) == []

    # Cancelado deixa de estar a caminho → volta.
    client.post(f"/api/v1/compras/pedidos/{pedido['id']}/cancelar", json={"motivo": "Teste"}, headers=header_com_token)
    assert list(itens(necessidades(client, header_com_token))) == [cadastro["produto_id"]]


def test_avisa_quando_outro_fornecedor_e_mais_barato(client, db_session, header_com_token, cadastro, fardo):
    minimo(db_session, cadastro["produto_id"], 24)
    fornecedores(client, header_com_token, cadastro["produto_id"], [
        {"fornecedor_id": cadastro["ambev"], "embalagem_id": fardo, "ultimo_preco": 4200, "padrao": True},  # 3,50/un
        {"fornecedor_id": cadastro["atacado"], "ultimo_preco": 333},                                          # 3,33/un
    ])
    [item] = itens(necessidades(client, header_com_token)).values()
    assert item["fornecedor_id"] == cadastro["ambev"]  # o principal continua o sugerido
    alt = item["alternativa"]
    assert (alt["fornecedor_id"], alt["fornecedor_nome"], round(alt["preco_unidade"]), alt["economia_bp"]) == (
        cadastro["atacado"], "Atacado Central LTDA", 333, 486)
    assert {o["fornecedor_id"] for o in item["opcoes"]} == {cadastro["ambev"], cadastro["atacado"]}


def test_sem_principal_sugere_o_mais_barato(client, db_session, header_com_token, cadastro):
    minimo(db_session, cadastro["produto_id"], 24)
    fornecedores(client, header_com_token, cadastro["produto_id"], [
        {"fornecedor_id": cadastro["ambev"], "ultimo_preco": 400},
        {"fornecedor_id": cadastro["atacado"], "ultimo_preco": 350},
    ])
    [item] = itens(necessidades(client, header_com_token)).values()
    assert (item["fornecedor_id"], item["alternativa"]) == (cadastro["atacado"], None)


def test_sem_fornecedor_vai_para_o_fim(client, db_session, header_com_token, cadastro):
    minimo(db_session, cadastro["produto_id"], 24)
    minimo(db_session, cadastro["outro_id"], 10)
    fornecedores(client, header_com_token, cadastro["outro_id"], [{"fornecedor_id": cadastro["atacado"]}])
    grupos = necessidades(client, header_com_token)
    assert [g["fornecedor_nome"] for g in grupos] == ["Atacado Central LTDA", "Sem fornecedor cadastrado"]


def test_sem_permissao_de_custo_nao_ve_preco_nem_alternativa(client, db_session, header_com_token, cadastro, fardo, como):
    minimo(db_session, cadastro["produto_id"], 24)
    fornecedores(client, header_com_token, cadastro["produto_id"], [
        {"fornecedor_id": cadastro["ambev"], "embalagem_id": fardo, "ultimo_preco": 4200, "padrao": True},
        {"fornecedor_id": cadastro["atacado"], "ultimo_preco": 333},
    ])
    como(compra=True)
    [item] = itens(necessidades(client, {})).values()
    assert (item["ultimo_preco"], item["alternativa"]) == (None, None)
    assert all(o["ultimo_preco"] is None for o in item["opcoes"])


# --- gerar pedidos ---------------------------------------------------------------------

def test_gera_um_rascunho_por_fornecedor_com_preco_embalagem_e_prazo(
    client, db_session, header_com_token, cadastro, fardo
):
    fornecedores(client, header_com_token, cadastro["produto_id"], [
        {"fornecedor_id": cadastro["ambev"], "embalagem_id": fardo, "ultimo_preco": 5200, "prazo_dias": 3,
         "codigo_fornecedor": "CERV-CX12"}])
    db_session.get(Estoque, cadastro["outro_id"]).valor_entrada = 650
    db_session.commit()

    r = client.post(f"{URL}/gerar-pedidos", json={"itens": [
        {"produto_id": cadastro["produto_id"], "fornecedor_id": cadastro["ambev"], "quantidade": 5},
        {"produto_id": cadastro["outro_id"], "fornecedor_id": cadastro["atacado"], "quantidade": 12},
    ]}, headers=header_com_token)
    assert r.status_code == 201, r.text
    criados = {p["fornecedor_nome"]: p for p in r.json()}
    assert sorted(p["codigo"] for p in criados.values()) == ["PC-000001", "PC-000002"]
    assert all(p["situacao"] == "RASCUNHO" for p in criados.values())

    ambev = client.get(f"/api/v1/compras/pedidos/{criados['Ambev']['id']}", headers=header_com_token).json()
    [item] = ambev["itens"]
    assert (item["unidade_compra"], item["fator"], item["quantidade"], item["custo_unitario"], item["codigo_fornecedor"]) == (
        "FD", 12, 5, 5200, "CERV-CX12")
    assert ambev["previsao_entrega"] == (date.today() + timedelta(days=3)).isoformat()
    assert ambev["historico"][0]["motivo"] == "Gerado pelas Necessidades de compra"

    # Sem cadastro do fornecedor: entra por unidade, com o último custo do estoque.
    atacado = client.get(f"/api/v1/compras/pedidos/{criados['Atacado Central LTDA']['id']}", headers=header_com_token).json()
    [item] = atacado["itens"]
    assert (item["unidade_compra"], item["fator"], item["custo_unitario"], atacado["previsao_entrega"]) == ("UN", 1, 650, None)


def test_gerar_com_erro_nao_cria_nenhum(client, db_session, header_com_token, cadastro):
    r = client.post(f"{URL}/gerar-pedidos", json={"itens": [
        {"produto_id": cadastro["produto_id"], "fornecedor_id": cadastro["ambev"], "quantidade": 5},
        {"produto_id": cadastro["outro_id"], "fornecedor_id": cadastro["frete"], "quantidade": 1},  # transportadora
    ]}, headers=header_com_token)
    assert r.status_code == 422
    db_session.expire_all()
    assert db_session.query(PedidoCompra).count() == 0


def test_gerar_exige_gerenciar(client, cadastro, como):
    como(compra=True, view_purchases=True)
    r = client.post(f"{URL}/gerar-pedidos", json={"itens": [
        {"produto_id": cadastro["produto_id"], "fornecedor_id": cadastro["ambev"], "quantidade": 1}]})
    assert r.status_code == 403


def test_produto_inativo_nao_entra(client, db_session, header_com_token, cadastro):
    minimo(db_session, cadastro["produto_id"], 24)
    db_session.get(Produto, cadastro["produto_id"]).ativo = False
    db_session.commit()
    assert necessidades(client, header_com_token) == []
