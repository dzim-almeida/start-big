# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/compras/test_fase6_api.py
# DESCRIÇÃO: Fase 6 (genérica) — a OS como origem de compra
#            (docs/compras-plano.md; RC03/RC06/RC08 do resumo da marcenaria).
#
# O que não pode errar:
# - a "reserva" é a MESMA regra da baixa da OS (produto, aprovado, OS aberta);
#   OS finalizada (já baixou) e cancelada não reservam;
# - o estoque é repartido em FILA: a OS mais antiga pega primeiro;
# - o pedido gerado é ligado à OS a que a peça FALTA, e gerar de novo não
#   pede duas vezes para a mesma OS;
# - nada disso mexe no estoque nem na OS.
# ---------------------------------------------------------------------------

from datetime import datetime, timedelta

import pytest

from app.core.enum import (
    OrdemServicoItemAprovacao,
    OrdemServicoItemTipo,
    OrdemServicoStatus,
    UnidadeMedida,
)
from app.db.models.cliente import ClientePF
from app.db.models.estoque import Estoque
from app.db.models.objeto_servico import ObjetoServico
from app.db.models.ordem_servico import OrdemServico
from app.db.models.ordem_servico_item import OrdemServicoItem
from app.db.models.pedido_compra import PedidoCompraOrigem

NEC = "/api/v1/compras/necessidades"
PEDIDOS = "/api/v1/compras/pedidos"


@pytest.fixture
def oficina(db_session, cadastro) -> dict:
    """Duas OS abertas que usam o refrigerante (estoque 5): a 1ª precisa de 4, a 2ª de 6."""
    cliente = ClientePF(tipo="PF", nome="Maria", cpf="52998224725", celular="88999990000")
    db_session.add(cliente)
    db_session.flush()
    objeto = ObjetoServico(cliente_id=cliente.id, marca="Fiat", modelo="Uno", numero_serie="ABC1234")
    db_session.add(objeto)
    db_session.flush()

    def nova_os(numero, quantidade, dias_atras, status=OrdemServicoStatus.EM_ANDAMENTO,
                aprovacao=OrdemServicoItemAprovacao.APROVADO, previsao=None):
        os_ = OrdemServico(numero_os=numero, objeto_id=objeto.id, defeito_relatado="Revisão", status=status,
                           data_criacao=datetime.now() - timedelta(days=dias_atras), data_previsao=previsao)
        db_session.add(os_)
        db_session.flush()
        db_session.add(OrdemServicoItem(
            ordem_servico_id=os_.id, produto_id=cadastro["outro_id"], tipo=OrdemServicoItemTipo.PRODUTO,
            nome="Refrigerante 2L", unidade_medida=UnidadeMedida.UNIDADE, quantidade=quantidade,
            valor_unitario=900, valor_total=int(900 * quantidade), status_aprovacao=aprovacao,
        ))
        db_session.flush()
        return os_.id

    ids = {
        "antiga": nova_os("OS-2026-000001", 4, dias_atras=5),
        "nova": nova_os("OS-2026-000002", 6, dias_atras=1, previsao=datetime.now() + timedelta(days=2)),
        # Estas três NÃO reservam:
        "finalizada": nova_os("OS-2026-000003", 50, dias_atras=9, status=OrdemServicoStatus.FINALIZADA),
        "cancelada": nova_os("OS-2026-000004", 50, dias_atras=9, status=OrdemServicoStatus.CANCELADA),
        "pendente": nova_os("OS-2026-000005", 50, dias_atras=9, aprovacao=OrdemServicoItemAprovacao.PENDENTE),
    }
    db_session.commit()
    return ids


def item_refri(client, headers, cadastro) -> dict:
    r = client.get(NEC, headers=headers)
    assert r.status_code == 200, r.text
    return next(i for g in r.json() for i in g["itens"] if i["produto_id"] == cadastro["outro_id"])


def compras_da_os(client, headers, os_id) -> dict:
    r = client.get(f"/api/v1/compras/ordens-servico/{os_id}", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


# --- necessidades ------------------------------------------------------------------------

def test_os_vira_origem_sem_precisar_de_minimo(client, header_com_token, cadastro, oficina):
    item = item_refri(client, header_com_token, cadastro)
    # Estoque 5, OS pedem 4 + 6 = 10 → livre −5 → comprar 5.
    assert (item["origem"], item["reservado_os"], item["sugestao"], item["saldo"]) == ("OS", 10, 5, 5)
    assert [(o["numero_os"], o["quantidade"]) for o in item["ordens"]] == [
        ("OS-2026-000001", 4), ("OS-2026-000002", 6)]  # a mais antiga primeiro


def test_minimo_olha_o_saldo_livre(client, db_session, header_com_token, cadastro, oficina):
    e = db_session.get(Estoque, cadastro["outro_id"])
    e.quantidade, e.quantidade_minima, e.quantidade_ideal = 30, 25, 40
    db_session.commit()
    item = item_refri(client, header_com_token, cadastro)
    # Saldo 30 parece acima do mínimo 25, mas 10 já têm dono: livre 20 ≤ 25 → até o ideal: 20.
    assert (item["origem"], item["sugestao"]) == ("MINIMO", 20)


def test_estoque_que_cobre_as_os_nao_gera_compra(client, db_session, header_com_token, cadastro, oficina):
    db_session.get(Estoque, cadastro["outro_id"]).quantidade = 10
    db_session.commit()
    r = client.get(NEC, headers=header_com_token).json()
    assert all(i["produto_id"] != cadastro["outro_id"] for g in r for i in g["itens"])


# --- pedido ligado à OS (RC06) -------------------------------------------------------------

def test_pedido_vai_para_a_os_a_que_falta(client, db_session, header_com_token, cadastro, oficina):
    r = client.post(f"{NEC}/gerar-pedidos", json={"itens": [
        {"produto_id": cadastro["outro_id"], "fornecedor_id": cadastro["atacado"], "quantidade": 7}]},
        headers=header_com_token)
    assert r.status_code == 201, r.text
    db_session.expire_all()
    origens = [(o.origem, o.origem_id, o.quantidade) for o in db_session.query(PedidoCompraOrigem).all()]
    # Estoque 5 cobre a antiga (4) e 1 da nova; faltam 5 à nova. Os outros 2 são reposição.
    assert origens == [("OS", oficina["nova"], 5)]


def test_gerar_de_novo_nao_pede_duas_vezes_para_a_mesma_os(client, db_session, header_com_token, cadastro, oficina):
    for _ in range(2):
        client.post(f"{NEC}/gerar-pedidos", json={"itens": [
            {"produto_id": cadastro["outro_id"], "fornecedor_id": cadastro["atacado"], "quantidade": 5}]},
            headers=header_com_token)
    db_session.expire_all()
    assert sum(o.quantidade for o in db_session.query(PedidoCompraOrigem).all()) == 5


# --- "Compras desta OS" ----------------------------------------------------------------------

def test_painel_da_os_mostra_estoque_pedido_e_falta(client, header_com_token, cadastro, oficina):
    antiga = compras_da_os(client, header_com_token, oficina["antiga"])
    [peca] = antiga["itens"]
    assert (peca["necessario"], peca["no_estoque"], peca["falta"], peca["situacao"]) == (4, 4, 0, "NO_ESTOQUE")

    nova = compras_da_os(client, header_com_token, oficina["nova"])
    [peca] = nova["itens"]
    assert (peca["no_estoque"], peca["em_pedido"], peca["falta"], peca["situacao"]) == (1, 0, 5, "FALTA")

    # Gera e envia o pedido, com entrega DEPOIS da previsão da OS.
    criados = client.post(f"{NEC}/gerar-pedidos", json={"itens": [
        {"produto_id": cadastro["outro_id"], "fornecedor_id": cadastro["atacado"], "quantidade": 5}]},
        headers=header_com_token).json()
    pid = criados[0]["id"]
    rascunho = compras_da_os(client, header_com_token, oficina["nova"])["itens"][0]
    assert (rascunho["situacao"], rascunho["pedidos"][0]["situacao"]) == ("FALTA", "RASCUNHO")  # rascunho não cobre

    tarde = (datetime.now() + timedelta(days=10)).date().isoformat()
    client.patch(f"{PEDIDOS}/{pid}", json={"previsao_entrega": tarde, "observacao": None}, headers=header_com_token)
    client.post(f"{PEDIDOS}/{pid}/enviar", headers=header_com_token)
    peca = compras_da_os(client, header_com_token, oficina["nova"])["itens"][0]
    assert (peca["em_pedido"], peca["falta"], peca["situacao"]) == (5, 0, "EM_PEDIDO")
    assert peca["pedidos"][0]["atrasa_os"] is True  # RC08: chega depois da previsão da OS


def test_os_finalizada_nao_tem_o_que_comprar(client, header_com_token, cadastro, oficina):
    r = compras_da_os(client, header_com_token, oficina["finalizada"])
    assert (r["aberta"], r["itens"]) == (False, [])


def test_os_inexistente_e_sem_modulo(client, header_com_token, cadastro, oficina, licenca):
    assert client.get("/api/v1/compras/ordens-servico/99999", headers=header_com_token).status_code == 404
    licenca()
    assert client.get(f"/api/v1/compras/ordens-servico/{oficina['nova']}", headers=header_com_token).status_code == 403


def test_nada_disso_mexe_no_estoque(client, db_session, header_com_token, cadastro, oficina):
    item_refri(client, header_com_token, cadastro)
    compras_da_os(client, header_com_token, oficina["nova"])
    db_session.expire_all()
    assert db_session.get(Estoque, cadastro["outro_id"]).quantidade == 5
