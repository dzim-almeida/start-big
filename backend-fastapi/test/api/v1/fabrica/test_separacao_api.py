# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/fabrica/test_separacao_api.py
# DESCRIÇÃO: Separação bipada e margem (F4) e terceirizados (F5)
#            (docs/marcenaria-fabrica-plano.md).
#
# O que não pode errar:
# - separar dá a baixa NA HORA, e o finalizar baixa só o resto — separou e
#   finalizou = UMA baixa;
# - a reserva de Compras cai ao separar; cancelar devolve o separado;
# - a etapa "Separação e compra" só sai com tudo separado e os serviços
#   terceirizados recebidos;
# - o pedido à central de corte é um pedido de SERVIÇO: recebe sem estoque;
# - a tela do almoxarife não tem preço.
# ---------------------------------------------------------------------------

import pytest

from app.db.models.estoque import Estoque
from app.db.models.fornecedor import Fornecedor
from app.db.models.ordem_servico import OrdemServico
from app.db.models.produto import Produto
from app.services import ordem_servico as os_service
from app.services.compras.demanda_os import demandas_por_produto

from .test_orcamento_api import FAB, OS, acao, cozinha, nova_versao, os_atual, salvar
from .test_trilho_api import avancar, pagar_sinal, travar  # noqa: F401 (fixture)

M2 = 1_000_000
PEDIDOS = "/api/v1/compras/pedidos"


def estoque(db_session, produto_id) -> float:
    db_session.expire_all()
    return float(db_session.get(Produto, produto_id).estoque.quantidade)


def bipar(client, headers, numero, codigo=None, item_id=None, quantidade=1):
    corpo = {"quantidade": quantidade}
    if codigo:
        corpo["codigo"] = codigo
    if item_id:
        corpo["item_id"] = item_id
    return client.post(f"{FAB}/os/{numero}/separacao", json=corpo, headers=headers)


@pytest.fixture
def com_estoque(db_session, insumos):
    for pid, qtd in ((insumos["mdf"], 10), (insumos["fita"], 5), (insumos["dobradica"], 50)):
        db_session.get(Produto, pid).estoque.quantidade = qtd
    db_session.commit()


@pytest.fixture
def na_separacao(client, header_com_token, modo_fabrica, abrir_os, insumos, com_estoque, db_session):
    """Cozinha aprovada, sinal pago, na etapa "Separação e compra"."""
    def _abrir(arvore=None):
        os_ = abrir_os()
        numero = os_["numero_os"]
        v1 = nova_versao(client, header_com_token, numero)
        assert salvar(client, header_com_token, v1["id"], arvore or cozinha(insumos)).status_code == 200
        acao(client, header_com_token, v1["id"], "enviar")
        assert acao(client, header_com_token, v1["id"], "aprovar").status_code == 200
        pagar_sinal(db_session, numero, valor=10_000_000)   # sinal coberto, qualquer que seja o total
        assert avancar(client, header_com_token, numero).json()["fase"] == "SEPARACAO_COMPRA"
        return numero, v1["id"]
    return _abrir


def separar_tudo(client, headers, numero):
    for item in client.get(f"{FAB}/os/{numero}/separacao", headers=headers).json()["itens"]:
        if item["falta"]:
            assert bipar(client, headers, numero, item_id=item["item_id"], quantidade=item["falta"]).status_code == 200


# --- separar -------------------------------------------------------------------------------

def test_so_separa_depois_do_sinal(client, header_com_token, modo_fabrica, abrir_os, insumos, com_estoque):
    numero = abrir_os()["numero_os"]
    v1 = nova_versao(client, header_com_token, numero)
    salvar(client, header_com_token, v1["id"], cozinha(insumos))
    acao(client, header_com_token, v1["id"], "enviar")
    acao(client, header_com_token, v1["id"], "aprovar")
    assert bipar(client, header_com_token, numero, codigo="MDF-15").status_code == 409


def test_bipar_da_baixa_na_hora_e_a_reserva_cai(client, header_com_token, na_separacao, insumos, db_session):
    numero, _ = na_separacao()
    tela = client.get(f"{FAB}/os/{numero}/separacao", headers=header_com_token).json()
    assert {i["descricao"]: i["falta"] for i in tela["itens"]} == {
        "MDF Branco 15mm": 3, "Fita de borda branca 22mm": 1, "Dobradiça 35mm": 6,
    }
    assert "custo" not in str(tela).lower()                    # a tela do almoxarife não tem preço

    r = bipar(client, header_com_token, numero, codigo="MDF-15")
    assert r.status_code == 200, r.text
    assert estoque(db_session, insumos["mdf"]) == 9
    mdf = next(i for i in r.json()["itens"] if i["produto_id"] == insumos["mdf"])
    assert (mdf["separada"], mdf["falta"]) == (1, 2)
    reserva = demandas_por_produto(db_session, [insumos["mdf"]])[insumos["mdf"]][0]
    assert reserva.quantidade == 2


def test_nao_separa_mais_que_o_aprovado(client, header_com_token, na_separacao):
    numero, _ = na_separacao()
    assert bipar(client, header_com_token, numero, codigo="MDF-15", quantidade=4).status_code == 409
    assert bipar(client, header_com_token, numero, codigo="NAO-EXISTE").status_code == 404


def test_separou_tudo_e_finalizou_uma_baixa_so(client, header_com_token, na_separacao, insumos, db_session):
    numero, _ = na_separacao()
    separar_tudo(client, header_com_token, numero)
    assert estoque(db_session, insumos["mdf"]) == 7
    os_ = db_session.query(OrdemServico).filter_by(numero_os=numero).one()
    os_service._movimentar_estoque_os(db_session, os_, saida=True)   # o que o finalizar faz
    db_session.commit()
    assert estoque(db_session, insumos["mdf"]) == 7                    # não baixou de novo


def test_separou_metade_o_finalizar_baixa_o_resto(client, header_com_token, na_separacao, insumos, db_session):
    numero, _ = na_separacao()
    bipar(client, header_com_token, numero, codigo="MDF-15")
    os_ = db_session.query(OrdemServico).filter_by(numero_os=numero).one()
    os_service._movimentar_estoque_os(db_session, os_, saida=True)
    db_session.commit()
    assert estoque(db_session, insumos["mdf"]) == 7                    # 1 na separação + 2 no fechamento


def test_cancelar_devolve_o_separado(client, header_com_token, na_separacao, insumos, db_session):
    numero, _ = na_separacao()
    bipar(client, header_com_token, numero, codigo="MDF-15", quantidade=2)
    assert estoque(db_session, insumos["mdf"]) == 8
    r = client.put(f"{OS}/{numero}/cancelar", json={"motivo": "Cliente desistiu"}, headers=header_com_token)
    assert r.status_code == 200, r.text
    assert estoque(db_session, insumos["mdf"]) == 10
    mdf = next(i for i in os_atual(client, header_com_token, numero)["itens"] if i["produto_id"] == insumos["mdf"])
    assert mdf["quantidade_separada"] is None


def test_estornar_e_as_travas_de_volta(client, header_com_token, na_separacao, insumos, db_session):
    numero, v1 = na_separacao()
    r = bipar(client, header_com_token, numero, codigo="MDF-15")
    item_id = next(i["item_id"] for i in r.json()["itens"] if i["produto_id"] == insumos["mdf"])

    # com material separado: não volta para antes da separação nem aprova outra versão
    r = client.post(f"{FAB}/os/{numero}/voltar", json={"fase": "AGUARDANDO_SINAL", "motivo": "teste"},
                    headers=header_com_token)
    assert r.status_code == 409
    v2 = nova_versao(client, header_com_token, numero, copiar_de=v1)
    acao(client, header_com_token, v2["id"], "enviar")
    assert acao(client, header_com_token, v2["id"], "aprovar").status_code == 409

    r = client.post(f"{FAB}/os/{numero}/separacao/estornar",
                    json={"item_id": item_id, "quantidade": 1, "motivo": "chapa errada"}, headers=header_com_token)
    assert r.status_code == 200
    assert estoque(db_session, insumos["mdf"]) == 10


def test_trava_da_etapa_e_tudo_separado(client, header_com_token, na_separacao, travar):
    numero, _ = na_separacao()
    travar()
    r = avancar(client, header_com_token, numero)
    assert r.status_code == 409
    assert "Falta separar" in r.json()["detail"]["travas"][0]
    separar_tudo(client, header_com_token, numero)
    assert avancar(client, header_com_token, numero).json()["fase"] == "EM_PRODUCAO"


# --- margem ------------------------------------------------------------------------------------

def test_margem_orcada_e_real(client, header_com_token, na_separacao, db_session):
    numero, _ = na_separacao()
    m = client.get(f"{FAB}/os/{numero}/margem", headers=header_com_token).json()
    assert (m["preco"], m["completo"], m["margem_real_bp"]) == (550000, False, None)
    custo_orcado = m["custo_orcado"]
    assert custo_orcado == 25946 + 528 + 51892 + 3000

    separar_tudo(client, header_com_token, numero)
    m = client.get(f"{FAB}/os/{numero}/margem", headers=header_com_token).json()
    # Real: as chapas INTEIRAS que saíram (3 × R$ 300 + 1 rolo × R$ 20 + 6 × R$ 5)
    assert (m["completo"], m["custo_real"]) == (True, 90000 + 2000 + 3000)
    assert m["margem_real_bp"] == round((550000 - 95000) * 10000 / 550000)


def test_quem_nao_ve_custo_nao_ve_margem_mas_o_almoxarife_separa(client, header_com_token, na_separacao, como):
    numero, _ = na_separacao()
    como(recebimento_compra=True, view_receiving=True)
    assert client.get(f"{FAB}/os/{numero}/separacao").status_code == 200
    assert client.get(f"{FAB}/os/{numero}/margem").status_code == 403


# --- F5: terceirizados -------------------------------------------------------------------------

@pytest.fixture
def com_compras(monkeypatch):
    from app.core import modulos as modulos_mod
    monkeypatch.setattr(modulos_mod.licenca_service, "modulos_da_licenca", lambda _db: ["COMPRAS"])


@pytest.fixture
def central(db_session) -> int:
    f = Fornecedor(nome="Central de Corte Rápido", cnpj="55555555000155", tipo="produto", ativo=True)
    db_session.add(f)
    db_session.commit()
    return f.id


def com_terceirizado(insumos):
    arvore = cozinha(insumos)
    arvore[0]["moveis"].append({"nome": "Painel ripado", "preco_venda": 180000, "terceirizado": True,
                                "custo_terceiro": 60000, "materiais": []})
    return arvore


def test_pedido_a_central_de_corte_recebe_sem_estoque_e_libera_a_etapa(
    client, header_com_token, na_separacao, insumos, central, com_compras, travar, db_session,
):
    numero, v1 = na_separacao(com_terceirizado(insumos))
    travar()
    separar_tudo(client, header_com_token, numero)
    r = avancar(client, header_com_token, numero)
    assert r.status_code == 409
    assert any("Painel ripado (sem pedido" in t for t in r.json()["detail"]["travas"])

    orc = client.get(f"{FAB}/orcamentos/{v1}", headers=header_com_token).json()
    painel = next(m for m in orc["ambientes"][0]["moveis"] if m["nome"] == "Painel ripado")
    r = client.post(f"{FAB}/moveis/{painel['id']}/pedido-servico",
                    json={"fornecedor_id": central, "valor": 62000, "observacao": "Arquivo do corte por e-mail"},
                    headers=header_com_token)
    assert r.status_code == 201, r.text
    pedido_id = r.json()["pedido_compra_id"]

    pedido = client.get(f"{PEDIDOS}/{pedido_id}", headers=header_com_token).json()
    assert (pedido["tipo"], pedido["valor_total"]) == ("SERVICO", 62000)
    # editar pela tela de pedido apagaria o serviço: recusado
    assert client.put(f"{PEDIDOS}/{pedido_id}", json={"fornecedor_id": central, "itens": []},
                      headers=header_com_token).status_code == 409

    assert client.post(f"{PEDIDOS}/{pedido_id}/enviar", headers=header_com_token).status_code == 200
    antes = estoque(db_session, insumos["mdf"])
    r = client.post(f"{PEDIDOS}/{pedido_id}/recebimentos", json={
        "itens": [{"pedido_item_id": pedido["itens"][0]["id"], "quantidade": 1}], "lancar_contas_pagar": False,
    }, headers=header_com_token)
    assert r.status_code in (200, 201), r.text
    assert r.json()["situacao"] == "RECEBIDO"
    assert estoque(db_session, insumos["mdf"]) == antes                # serviço não mexe no estoque

    assert avancar(client, header_com_token, numero).json()["fase"] == "EM_PRODUCAO"
    m = client.get(f"{FAB}/os/{numero}/margem", headers=header_com_token).json()
    assert [(t["nome"], t["custo_orcado"], t["custo_real"]) for t in m["terceirizados"]] == [
        ("Cozinha — Painel ripado", 60000, 62000)]


def test_so_movel_terceirizado_da_versao_aprovada(client, header_com_token, na_separacao, insumos, central, com_compras):
    numero, v1 = na_separacao()
    orc = client.get(f"{FAB}/orcamentos/{v1}", headers=header_com_token).json()
    aereo = orc["ambientes"][0]["moveis"][0]
    r = client.post(f"{FAB}/moveis/{aereo['id']}/pedido-servico", json={"fornecedor_id": central, "valor": 100},
                    headers=header_com_token)
    assert r.status_code == 409


def test_pedido_de_servico_exige_o_modulo_compras(client, header_com_token, na_separacao, insumos, central, monkeypatch):
    from app.core import modulos as modulos_mod
    monkeypatch.setattr(modulos_mod.licenca_service, "modulos_da_licenca", lambda _db: [])
    numero, v1 = na_separacao(com_terceirizado(insumos))
    orc = client.get(f"{FAB}/orcamentos/{v1}", headers=header_com_token).json()
    painel = next(m for m in orc["ambientes"][0]["moveis"] if m["nome"] == "Painel ripado")
    r = client.post(f"{FAB}/moveis/{painel['id']}/pedido-servico", json={"fornecedor_id": central, "valor": 100},
                    headers=header_com_token)
    assert r.status_code == 403
