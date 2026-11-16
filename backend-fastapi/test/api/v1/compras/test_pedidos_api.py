# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/compras/test_pedidos_api.py
# DESCRIÇÃO: Pedido de compra (docs/compras-plano.md, fase 2).
#
# O que não pode errar: os totais e as parcelas fecham ao centavo; só rascunho
# se edita; toda mudança de situação fica no histórico com motivo; cancelar
# exige a caixa Excluir; o pedido NÃO mexe no estoque; quem não vê custo não
# vê preço; loja sem o módulo não acessa.
# ---------------------------------------------------------------------------

from datetime import date, timedelta

from app.db.models.compra_log import CompraLog
from app.db.models.estoque import Estoque
from app.db.models.fornecedor import Fornecedor

URL = "/api/v1/compras/pedidos"


def pedido_base(cadastro, fardo, **extra) -> dict:
    """2 FD de cerveja a R$ 52,00 + frete 5,00 − desconto 2,00 = R$ 107,00, em 30/60."""
    return {
        "fornecedor_id": cadastro["ambev"],
        "condicao_pagamento": "30/60",
        "frete": 500,
        "desconto": 200,
        "itens": [{"produto_id": cadastro["produto_id"], "embalagem_id": fardo, "quantidade": 2, "custo_unitario": 5200}],
        **extra,
    }


def criar(client, headers, corpo):
    r = client.post(URL, json=corpo, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


# --- criar e ler -------------------------------------------------------------------

def test_cria_rascunho_com_totais_parcelas_e_historico(client, header_com_token, cadastro, fardo):
    p = criar(client, header_com_token, pedido_base(cadastro, fardo))
    assert (p["codigo"], p["situacao"], p["fornecedor_nome"]) == ("PC-000001", "RASCUNHO", "Ambev")
    [item] = p["itens"]
    assert (item["unidade_compra"], item["fator"], item["quantidade"], item["subtotal"]) == ("FD", 12, 2, 10400)
    assert (p["valor_itens"], p["valor_total"]) == (10400, 10700)
    assert [(x["dias"], x["valor"]) for x in p["parcelas"]] == [(30, 5350), (60, 5350)]
    assert [(h["acao"], h["situacao_nova"]) for h in p["historico"]] == [("CRIADO", "RASCUNHO")]


def test_numero_e_sequencial(client, header_com_token, cadastro, fardo):
    criar(client, header_com_token, pedido_base(cadastro, fardo))
    assert criar(client, header_com_token, pedido_base(cadastro, fardo))["codigo"] == "PC-000002"


def test_resto_dos_centavos_vai_na_ultima_parcela(client, header_com_token, cadastro, fardo):
    corpo = pedido_base(cadastro, fardo, frete=0, desconto=0, condicao_pagamento="30/60/90")
    corpo["itens"][0]["custo_unitario"] = 5000  # 2 × 50,00 = 100,00 em 3
    p = criar(client, header_com_token, corpo)
    assert [x["valor"] for x in p["parcelas"]] == [3333, 3333, 3334]


def test_sem_condicao_e_uma_parcela_a_vista(client, header_com_token, cadastro, fardo):
    p = criar(client, header_com_token, pedido_base(cadastro, fardo, condicao_pagamento=None))
    assert [(x["dias"], x["valor"]) for x in p["parcelas"]] == [(0, 10700)]


def test_codigo_do_fornecedor_vem_do_cadastro_do_produto(client, header_com_token, cadastro, fardo):
    client.put(f"/api/v1/compras/produtos/{cadastro['produto_id']}/fornecedores", json={"fornecedores": [
        {"fornecedor_id": cadastro["ambev"], "codigo_fornecedor": "CERV-CX12"}]}, headers=header_com_token)
    p = criar(client, header_com_token, pedido_base(cadastro, fardo))
    assert p["itens"][0]["codigo_fornecedor"] == "CERV-CX12"


# --- recusas na escrita --------------------------------------------------------------

def test_parcelas_explicitas_precisam_fechar_o_total(client, header_com_token, cadastro, fardo):
    corpo = pedido_base(cadastro, fardo, parcelas=[{"dias": 30, "valor": 5000}, {"dias": 60, "valor": 5000}])
    r = client.post(URL, json=corpo, headers=header_com_token)
    assert r.status_code == 422 and "somam" in r.json()["detail"]


def test_parcelas_explicitas_que_fecham_sao_aceitas(client, header_com_token, cadastro, fardo):
    corpo = pedido_base(cadastro, fardo, parcelas=[{"dias": 0, "valor": 700}, {"dias": 30, "valor": 10000}])
    p = criar(client, header_com_token, corpo)
    assert [(x["dias"], x["valor"]) for x in p["parcelas"]] == [(0, 700), (30, 10000)]


def test_condicao_que_nao_da_para_entender(client, header_com_token, cadastro, fardo):
    r = client.post(URL, json=pedido_base(cadastro, fardo, condicao_pagamento="boleto"), headers=header_com_token)
    assert r.status_code == 422 and "Não entendi" in r.json()["detail"]


def test_desconto_maior_que_o_pedido(client, header_com_token, cadastro, fardo):
    r = client.post(URL, json=pedido_base(cadastro, fardo, desconto=999_999), headers=header_com_token)
    assert r.status_code == 422


def test_produto_repetido(client, header_com_token, cadastro, fardo):
    corpo = pedido_base(cadastro, fardo)
    corpo["itens"].append({"produto_id": cadastro["produto_id"], "quantidade": 1})
    assert client.post(URL, json=corpo, headers=header_com_token).status_code == 422


def test_fornecedor_transportadora_ou_inativo(client, header_com_token, cadastro, fardo):
    for chave in ("frete", "inativo"):
        r = client.post(URL, json=pedido_base(cadastro, fardo, fornecedor_id=cadastro[chave]), headers=header_com_token)
        assert r.status_code == 422, (chave, r.text)


def test_embalagem_de_outro_produto(client, header_com_token, cadastro, fardo):
    corpo = pedido_base(cadastro, fardo)
    corpo["itens"] = [{"produto_id": cadastro["outro_id"], "embalagem_id": fardo, "quantidade": 1}]
    assert client.post(URL, json=corpo, headers=header_com_token).status_code == 422


# --- ciclo de situações ---------------------------------------------------------------

def test_so_rascunho_se_edita_por_inteiro(client, header_com_token, cadastro, fardo):
    p = criar(client, header_com_token, pedido_base(cadastro, fardo))
    corpo = pedido_base(cadastro, fardo, frete=0, desconto=0)
    corpo["itens"][0]["quantidade"] = 5
    r = client.put(f"{URL}/{p['id']}", json=corpo, headers=header_com_token)
    assert r.status_code == 200 and r.json()["valor_total"] == 26000

    assert client.post(f"{URL}/{p['id']}/enviar", headers=header_com_token).status_code == 200
    r = client.put(f"{URL}/{p['id']}", json=corpo, headers=header_com_token)
    assert r.status_code == 409 and "rascunho" in r.json()["detail"]


def test_enviar_pedido_vazio_e_recusado(client, header_com_token, cadastro, fardo):
    p = criar(client, header_com_token, pedido_base(cadastro, fardo, itens=[]))
    assert client.post(f"{URL}/{p['id']}/enviar", headers=header_com_token).status_code == 422


def test_enviado_aceita_mudar_previsao_e_fica_no_historico(client, header_com_token, cadastro, fardo):
    p = criar(client, header_com_token, pedido_base(cadastro, fardo))
    client.post(f"{URL}/{p['id']}/enviar", headers=header_com_token)
    nova = (date.today() + timedelta(days=10)).isoformat()
    r = client.patch(f"{URL}/{p['id']}", json={"previsao_entrega": nova, "observacao": "Atrasou"}, headers=header_com_token)
    assert r.status_code == 200, r.text
    assert r.json()["previsao_entrega"] == nova
    assert r.json()["historico"][0]["motivo"] == "Mudou previsão de entrega e observação"


def test_voltar_a_rascunho_exige_motivo(client, header_com_token, cadastro, fardo):
    p = criar(client, header_com_token, pedido_base(cadastro, fardo))
    client.post(f"{URL}/{p['id']}/enviar", headers=header_com_token)
    assert client.post(f"{URL}/{p['id']}/voltar-rascunho", json={"motivo": " "}, headers=header_com_token).status_code == 422
    r = client.post(f"{URL}/{p['id']}/voltar-rascunho", json={"motivo": "Faltou um item"}, headers=header_com_token)
    assert r.status_code == 200 and r.json()["situacao"] == "RASCUNHO"
    ultimo = r.json()["historico"][0]
    assert (ultimo["acao"], ultimo["situacao_anterior"], ultimo["situacao_nova"], ultimo["motivo"]) == (
        "VOLTOU_RASCUNHO", "ENVIADO", "RASCUNHO", "Faltou um item")


def test_cancelar_exige_a_caixa_excluir(client, header_com_token, cadastro, fardo, como):
    p = criar(client, header_com_token, pedido_base(cadastro, fardo))
    como(compra=True, view_purchases=True, manage_purchases=True)
    assert client.post(f"{URL}/{p['id']}/cancelar", json={"motivo": "Desisti"}).status_code == 403


def test_cancelado_nao_volta(client, db_session, header_com_token, cadastro, fardo):
    p = criar(client, header_com_token, pedido_base(cadastro, fardo))
    r = client.post(f"{URL}/{p['id']}/cancelar", json={"motivo": "Fornecedor sem estoque"}, headers=header_com_token)
    assert r.status_code == 200
    assert (r.json()["situacao"], r.json()["motivo_cancelamento"]) == ("CANCELADO", "Fornecedor sem estoque")
    assert client.post(f"{URL}/{p['id']}/enviar", headers=header_com_token).status_code == 409
    assert client.post(f"{URL}/{p['id']}/cancelar", json={"motivo": "De novo"}, headers=header_com_token).status_code == 409
    assert db_session.query(CompraLog).filter(CompraLog.acao == "CANCELADO").count() == 1


def test_pedido_nao_mexe_no_estoque(client, db_session, header_com_token, cadastro, fardo):
    p = criar(client, header_com_token, pedido_base(cadastro, fardo))
    client.post(f"{URL}/{p['id']}/enviar", headers=header_com_token)
    db_session.expire_all()
    assert db_session.get(Estoque, cadastro["produto_id"]).quantidade == 10


# --- listagem ---------------------------------------------------------------------------

def test_lista_filtra_por_situacao_numero_e_fornecedor(client, header_com_token, cadastro, fardo):
    a = criar(client, header_com_token, pedido_base(cadastro, fardo))
    criar(client, header_com_token, pedido_base(cadastro, fardo, fornecedor_id=cadastro["atacado"]))
    client.post(f"{URL}/{a['id']}/enviar", headers=header_com_token)

    def codigos(**params):
        r = client.get(URL, params=params, headers=header_com_token)
        assert r.status_code == 200, r.text
        return [p["codigo"] for p in r.json()["itens"]], r.json()["total_itens"]

    assert codigos() == (["PC-000002", "PC-000001"], 2)
    assert codigos(situacao="ENVIADO") == (["PC-000001"], 1)
    assert codigos(busca="PC-2") == (["PC-000002"], 1)
    assert codigos(busca="atacado") == (["PC-000002"], 1)
    assert codigos(fornecedor_id=cadastro["ambev"]) == (["PC-000001"], 1)
    assert client.get(URL, params={"situacao": "XPTO"}, headers=header_com_token).status_code == 422


def test_atrasado_e_enviado_com_previsao_passada(client, header_com_token, cadastro, fardo):
    ontem = (date.today() - timedelta(days=1)).isoformat()
    p = criar(client, header_com_token, pedido_base(cadastro, fardo, previsao_entrega=ontem))
    assert p["atrasado"] is False  # rascunho não atrasa: o fornecedor nem recebeu
    client.post(f"{URL}/{p['id']}/enviar", headers=header_com_token)
    [linha] = client.get(URL, headers=header_com_token).json()["itens"]
    assert linha["atrasado"] is True


# --- permissões e custo ----------------------------------------------------------------

def test_quem_nao_ve_custo_nao_ve_preco(client, header_com_token, cadastro, fardo, como):
    p = criar(client, header_com_token, pedido_base(cadastro, fardo))
    como(compra=True)  # só a chave genérica — o almoxarife da fase 3
    r = client.get(f"{URL}/{p['id']}")
    assert r.status_code == 200
    corpo = r.json()
    assert (corpo["valor_total"], corpo["valor_itens"], corpo["frete"]) == (None, None, None)
    assert corpo["itens"][0]["custo_unitario"] is None and corpo["itens"][0]["subtotal"] is None
    assert all(x["valor"] is None for x in corpo["parcelas"])
    assert "R$" not in client.get(f"{URL}/{p['id']}/whatsapp").json()["texto"]


def test_visualizar_nao_cria(client, cadastro, fardo, como):
    como(compra=True, view_purchases=True)
    assert client.post(URL, json=pedido_base(cadastro, fardo)).status_code == 403


def test_sem_o_modulo_nada_de_pedido(client, header_com_token, cadastro, fardo, licenca):
    licenca()
    assert client.get(URL, headers=header_com_token).status_code == 403


# --- WhatsApp e simulação ------------------------------------------------------------------

def test_texto_do_whatsapp(client, db_session, header_com_token, cadastro, fardo):
    db_session.get(Fornecedor, cadastro["ambev"]).celular = "11987654321"
    db_session.commit()
    p = criar(client, header_com_token, pedido_base(cadastro, fardo, observacao="Entregar pela manhã"))
    r = client.get(f"{URL}/{p['id']}/whatsapp", headers=header_com_token).json()
    assert r["telefone"] == "5511987654321"
    texto = r["texto"]
    assert "*Pedido de compra PC-000001*" in texto
    assert "• 2 FD com 12 Cerveja Lata 350ml — R$ 52,00 cada" in texto
    assert "Total: R$ 107,00" in texto and "Pagamento: 30/60" in texto and "Obs.: Entregar pela manhã" in texto


def test_whatsapp_sem_telefone(client, header_com_token, cadastro, fardo):
    p = criar(client, header_com_token, pedido_base(cadastro, fardo))
    assert client.get(f"{URL}/{p['id']}/whatsapp", headers=header_com_token).json()["telefone"] is None


def test_simular_parcelas(client, header_com_token, cadastro):
    r = client.post("/api/v1/compras/parcelas/simular", json={"total": 10000, "condicao": "30/60/90"},
                    headers=header_com_token)
    assert [p["valor"] for p in r.json()] == [3333, 3333, 3334]
    r = client.post("/api/v1/compras/parcelas/simular", json={"total": 100, "condicao": "xyz"}, headers=header_com_token)
    assert r.status_code == 422


def test_pedido_de_outra_empresa_nao_aparece(client, header_com_token, cadastro, fardo, como):
    p = criar(client, header_com_token, pedido_base(cadastro, fardo))
    como(compra=True, view_purchases=True)
    # `como` usa empresa_id=1; o master criado pelo conftest também é 1 — então
    # forjamos outra empresa no token para provar o isolamento.
    from app.core.depends import get_current_active_user
    from app.main import app
    app.dependency_overrides[get_current_active_user] = lambda: {
        "sub": "98", "empresa_id": 2, "cargo": "X", "is_master": False, "permissoes": {"view_purchases": True}}
    assert client.get(f"{URL}/{p['id']}").status_code == 404
    assert client.get(URL).json()["total_itens"] == 0
