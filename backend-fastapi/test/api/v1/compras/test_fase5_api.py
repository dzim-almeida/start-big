# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/compras/test_fase5_api.py
# DESCRIÇÃO: Fase 5 do módulo de Compras (docs/compras-plano.md):
#            necessidades pela média de vendas, pedidos atrasados, previsão
#            no Fluxo de Caixa e relatórios.
#
# Não-regressão: a base padrão das Necessidades continua sendo o mínimo
# (fase 2), e o Fluxo de Caixa de quem não tem Compras fica igual.
# ---------------------------------------------------------------------------

from datetime import date, datetime, timedelta

from app.core.enum import MovimentacaoOrigem, MovimentacaoTipo
from app.db.models.estoque import Estoque
from app.db.models.movimentacao_estoque import MovimentacaoEstoque

NEC = "/api/v1/compras/necessidades"
PEDIDOS = "/api/v1/compras/pedidos"


def vender(db_session, produto_id, quantidade, dias_atras=1, tipo=MovimentacaoTipo.SAIDA,
           origem=MovimentacaoOrigem.VENDA):
    db_session.add(MovimentacaoEstoque(
        produto_id=produto_id, produto_nome="x", usuario_nome="teste", tipo=tipo, quantidade=quantidade,
        quantidade_anterior=0, quantidade_posterior=0, origem=origem.value,
        created_at=datetime.now() - timedelta(days=dias_atras),
    ))
    db_session.commit()


def necessidades(client, headers, **params):
    r = client.get(NEC, params=params, headers=headers)
    assert r.status_code == 200, r.text
    return {i["produto_id"]: i for g in r.json() for i in g["itens"]}


def pedido_enviado(client, headers, cadastro, fardo, **extra) -> dict:
    corpo = {"fornecedor_id": cadastro["ambev"], "itens": [
        {"produto_id": cadastro["produto_id"], "embalagem_id": fardo, "quantidade": 10, "custo_unitario": 5200}],
        **extra}
    p = client.post(PEDIDOS, json=corpo, headers=headers).json()
    assert client.post(f"{PEDIDOS}/{p['id']}/enviar", headers=headers).status_code == 200
    return client.get(f"{PEDIDOS}/{p['id']}", headers=headers).json()


# --- necessidades pela média de vendas ----------------------------------------------

def test_base_padrao_continua_o_minimo(client, db_session, header_com_token, cadastro):
    vender(db_session, cadastro["produto_id"], 900)  # vende muito, mas não tem mínimo
    assert necessidades(client, header_com_token) == {}


def test_pela_venda_produto_sem_minimo_aparece(client, db_session, header_com_token, cadastro, fardo):
    client.put(f"/api/v1/compras/produtos/{cadastro['produto_id']}/fornecedores", json={"fornecedores": [
        {"fornecedor_id": cadastro["ambev"], "embalagem_id": fardo, "prazo_dias": 3, "padrao": True}]},
        headers=header_com_token)
    vender(db_session, cadastro["produto_id"], 900)  # 900 em 90 dias = 10/dia
    item = necessidades(client, header_com_token, base="VENDAS", cobertura_dias=30)[cadastro["produto_id"]]
    # Saldo 10 ≤ ponto (10 × 3 = 30). Alvo 10 × 33 = 330 → faltam 320 → 27 fardos de 12.
    assert (item["origem"], item["media_diaria"], item["dura_dias"], item["sugestao"]) == ("VENDAS", 10, 1, 27)


def test_venda_cancelada_e_devolucao_descontam(client, db_session, header_com_token, cadastro):
    vender(db_session, cadastro["produto_id"], 900)
    vender(db_session, cadastro["produto_id"], 450, tipo=MovimentacaoTipo.ENTRADA)  # venda cancelada
    vender(db_session, cadastro["produto_id"], 180, tipo=MovimentacaoTipo.ENTRADA, origem=MovimentacaoOrigem.DEVOLUCAO)
    item = necessidades(client, header_com_token, base="VENDAS")[cadastro["produto_id"]]
    assert item["media_diaria"] == 3  # (900 − 450 − 180) / 90


def test_venda_antiga_fica_fora_da_janela(client, db_session, header_com_token, cadastro):
    vender(db_session, cadastro["produto_id"], 900, dias_atras=120)
    assert necessidades(client, header_com_token, base="VENDAS") == {}


def test_vale_a_maior_entre_minimo_e_venda(client, db_session, header_com_token, cadastro):
    e = db_session.get(Estoque, cadastro["produto_id"])
    e.quantidade_minima, e.quantidade_ideal = 50, 200
    db_session.commit()
    vender(db_session, cadastro["produto_id"], 9)  # 0,1/dia: gira pouco, o mínimo manda
    item = necessidades(client, header_com_token, base="VENDAS")[cadastro["produto_id"]]
    assert (item["origem"], item["sugestao"]) == ("MINIMO", 190)


def test_base_invalida(client, header_com_token, cadastro):
    assert client.get(NEC, params={"base": "XPTO"}, headers=header_com_token).status_code == 422


# --- atrasados ----------------------------------------------------------------------------

def test_filtro_de_atrasados(client, header_com_token, cadastro, fardo):
    ontem = (date.today() - timedelta(days=1)).isoformat()
    amanha = (date.today() + timedelta(days=1)).isoformat()
    atrasado = pedido_enviado(client, header_com_token, cadastro, fardo, previsao_entrega=ontem)
    pedido_enviado(client, header_com_token, cadastro, fardo, previsao_entrega=amanha)
    r = client.get(PEDIDOS, params={"atrasados": True}, headers=header_com_token).json()
    assert [p["id"] for p in r["itens"]] == [atrasado["id"]]


# --- previsão no Fluxo de Caixa ---------------------------------------------------------

def _fluxo(client, headers, dias=60):
    r = client.get("/api/v1/financeiro/fluxo-caixa", params={"dias": dias}, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def test_pedido_enviado_entra_como_previsao(client, header_com_token, cadastro, fardo, licenca):
    licenca("COMPRAS", "FINANCEIRO", "FINANCEIRO_PRO")
    entrega = date.today() + timedelta(days=5)
    pedido_enviado(client, header_com_token, cadastro, fardo, previsao_entrega=entrega.isoformat(),
                   condicao_pagamento="30", frete=1000)
    fluxo = _fluxo(client, header_com_token)
    [dia] = fluxo["linha"]
    [lanc] = dia["lancamentos"]
    # 10 FD × 52,00 + frete 10,00 = 530,00, 30 dias depois da entrega prevista.
    assert dia["data"] == (entrega + timedelta(days=30)).isoformat()
    assert (lanc["valor"], lanc["previsao_compra"], lanc["tipo"]) == (53000, True, "SAIDA")
    assert "PC-000001" in lanc["descricao"]
    assert fluxo["previsto_compras"] == 53000 == fluxo["total_saidas"]


def test_so_o_que_falta_chegar_e_previsto(client, header_com_token, cadastro, fardo, licenca):
    licenca("COMPRAS", "FINANCEIRO", "FINANCEIRO_PRO")
    p = pedido_enviado(client, header_com_token, cadastro, fardo)  # à vista, sem previsão = hoje
    client.post(f"{PEDIDOS}/{p['id']}/recebimentos", json={"itens": [
        {"pedido_item_id": p["itens"][0]["id"], "quantidade": 6}], "lancar_contas_pagar": False},
        headers=header_com_token)
    previsoes = [l for d in _fluxo(client, header_com_token)["linha"] for l in d["lancamentos"] if l["previsao_compra"]]
    assert [l["valor"] for l in previsoes] == [4 * 5200]


def test_sem_compras_o_fluxo_nao_muda(client, header_com_token, cadastro, fardo, licenca):
    pedido_enviado(client, header_com_token, cadastro, fardo)
    licenca("FINANCEIRO", "FINANCEIRO_PRO")  # a licença diz: sem Compras
    fluxo = _fluxo(client, header_com_token)
    assert (fluxo["linha"], fluxo["previsto_compras"]) == ([], 0)


# --- relatórios ------------------------------------------------------------------------------

def test_relatorio_prazo_pontualidade_e_variacao(client, header_com_token, cadastro, fardo):
    hoje = date.today()
    a = pedido_enviado(client, header_com_token, cadastro, fardo, previsao_entrega=(hoje + timedelta(days=2)).isoformat())
    client.post(f"{PEDIDOS}/{a['id']}/recebimentos", json={"itens": [
        {"pedido_item_id": a["itens"][0]["id"], "quantidade": 10, "custo_unitario": 4800}],
        "lancar_contas_pagar": False}, headers=header_com_token)
    b = pedido_enviado(client, header_com_token, cadastro, fardo, previsao_entrega=(hoje - timedelta(days=1)).isoformat())
    client.post(f"{PEDIDOS}/{b['id']}/recebimentos", json={"itens": [
        {"pedido_item_id": b["itens"][0]["id"], "quantidade": 10, "custo_unitario": 5280}],
        "lancar_contas_pagar": False}, headers=header_com_token)

    r = client.get("/api/v1/compras/relatorios", params={"inicio": hoje.isoformat(), "fim": hoje.isoformat()},
                   headers=header_com_token)
    assert r.status_code == 200, r.text
    rel = r.json()
    assert (rel["pedidos_enviados"], rel["valor_recebido"]) == (2, 48000 + 52800)
    [ambev] = rel["por_fornecedor"]
    assert (ambev["fornecedor_nome"], ambev["recebimentos"], ambev["prazo_medio_dias"]) == ("Ambev", 2, 0)
    # O pedido B tinha previsão para ontem e chegou hoje: 1 de 2 no prazo.
    assert (ambev["entregas_com_previsao"], ambev["entregas_no_prazo"]) == (2, 1)
    [var] = rel["variacao_precos"]
    # 48,00 → 52,80 o fardo = 4,00 → 4,40 a unidade: +10%.
    assert (var["compras"], round(var["primeiro_custo_unidade"]), round(var["ultimo_custo_unidade"]), var["variacao_bp"]) == (
        2, 400, 440, 1000)


def test_relatorio_exige_ver_custo(client, cadastro, como):
    como(recebimento_compra=True, view_receiving=True, receive_purchases=True)
    hoje = date.today().isoformat()
    assert client.get("/api/v1/compras/relatorios", params={"inicio": hoje, "fim": hoje}).status_code == 403


def test_relatorio_periodo_invalido(client, header_com_token, cadastro):
    assert client.get("/api/v1/compras/relatorios", params={"inicio": "2026-10-10", "fim": "2026-10-01"},
                      headers=header_com_token).status_code == 422
