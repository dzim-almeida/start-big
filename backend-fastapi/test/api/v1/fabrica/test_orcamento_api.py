# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/fabrica/test_orcamento_api.py
# DESCRIÇÃO: Orçamento por móvel que gera a OS (docs/marcenaria-fabrica-plano.md, F2).
#
# O que não pode errar:
# - só a OS de Planejados aberta com o modo ligado entra no trilho; o resto
#   (Reforma, modo desligado, outros segmentos) fica exatamente como era;
# - aprovar escreve na OS um item por móvel (o preço) e um por insumo
#   SOMADO (chapas inteiras, com a perda) — e aprovar outra versão TROCA
#   esses itens, sem duplicar e sem tocar no que foi lançado à mão;
# - o item gerado não se edita pela OS: muda por uma nova versão;
# - a chapa aprovada já é reserva (Compras, fase 6) sem nada novo.
# ---------------------------------------------------------------------------

from datetime import date, timedelta

import pytest

from app.db.models.produto import Produto
from app.services.compras.demanda_os import demandas_por_produto

from .conftest import CHAPA_MM2

M2 = 1_000_000
OS = "/api/v1/ordens-servico"
FAB = "/api/v1/fabrica"


def nova_versao(client, headers, numero_os, copiar_de=None):
    corpo = {"copiar_de": copiar_de} if copiar_de else {}
    r = client.post(f"{FAB}/os/{numero_os}/orcamentos", json=corpo, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def salvar(client, headers, orcamento_id, ambientes, **extra):
    corpo = {"perda_bp": 1000, "sinal_bp": 5000, "ambientes": ambientes, **extra}
    return client.put(f"{FAB}/orcamentos/{orcamento_id}", json=corpo, headers=headers)


def cozinha(insumos, preco_aereo=240000, preco_balcao=310000):
    """Aéreo com 4 m² de MDF e 12 m de fita; balcão com 8 m² de MDF e 6 dobradiças."""
    return [{
        "nome": "Cozinha",
        "moveis": [
            {"nome": "Armário aéreo", "largura_mm": 1800, "altura_mm": 700, "profundidade_mm": 350,
             "preco_venda": preco_aereo, "materiais": [
                 {"produto_id": insumos["mdf"], "consumo": 4 * M2},
                 {"produto_id": insumos["fita"], "consumo": 12_000},
             ]},
            {"nome": "Balcão pia", "preco_venda": preco_balcao, "materiais": [
                {"produto_id": insumos["mdf"], "consumo": 8 * M2},
                {"produto_id": insumos["dobradica"], "consumo": 6},
            ]},
        ],
    }]


def acao(client, headers, orcamento_id, nome, **corpo):
    return client.post(f"{FAB}/orcamentos/{orcamento_id}/{nome}", json=corpo or None, headers=headers)


def os_atual(client, headers, numero_os):
    r = client.get(f"{OS}/{numero_os}", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture
def aprovada(client, header_com_token, modo_fabrica, abrir_os, insumos):
    """OS de cozinha com a v1 aprovada."""
    os_ = abrir_os()
    v1 = nova_versao(client, header_com_token, os_["numero_os"])
    assert salvar(client, header_com_token, v1["id"], cozinha(insumos)).status_code == 200
    assert acao(client, header_com_token, v1["id"], "enviar").status_code == 200
    r = acao(client, header_com_token, v1["id"], "aprovar")
    assert r.status_code == 200, r.text
    return {"numero_os": os_["numero_os"], "os_id": os_["id"], "v1": v1["id"]}


# --- quem entra no trilho (D0) -------------------------------------------------------

def test_planejados_com_modo_ligado_nasce_na_medicao(client, header_com_token, modo_fabrica, abrir_os):
    assert abrir_os()["fase_fabrica"] == "MEDICAO"


def test_sem_mexer_no_seletor_vale_o_tipo_padrao_da_tela(client, header_com_token, modo_fabrica, abrir_os):
    # A tela mostra "Planejados" e só grava o tipo quando o atendente troca.
    assert abrir_os(tipo=None)["fase_fabrica"] == "MEDICAO"


def test_reforma_continua_de_balcao(client, header_com_token, modo_fabrica, abrir_os):
    assert abrir_os(tipo="reforma_moveis", nome="Guarda-roupa")["fase_fabrica"] is None


def test_modo_desligado_nao_muda_nada(client, header_com_token, modo_fabrica, abrir_os):
    modo_fabrica(False)
    os_ = abrir_os()
    assert os_["fase_fabrica"] is None
    r = client.get(f"{FAB}/os/{os_['numero_os']}/orcamentos", headers=header_com_token)
    assert r.status_code == 409


def test_desligar_depois_nao_tira_a_os_do_trilho(client, header_com_token, modo_fabrica, abrir_os):
    os_ = abrir_os()
    modo_fabrica(False)
    assert os_atual(client, header_com_token, os_["numero_os"])["fase_fabrica"] == "MEDICAO"
    assert client.get(f"{FAB}/os/{os_['numero_os']}/orcamentos", headers=header_com_token).status_code == 200


def test_fora_da_marcenaria_nao_existe(client, header_com_token, modo_fabrica, abrir_os, segmento):
    os_ = abrir_os()
    segmento("oficina_mecanica")
    r = client.get(f"{FAB}/os/{os_['numero_os']}/orcamentos", headers=header_com_token)
    assert r.status_code == 403


# --- versões e árvore -----------------------------------------------------------------

def test_primeira_versao_tira_a_os_da_medicao(client, header_com_token, modo_fabrica, abrir_os):
    os_ = abrir_os()
    v1 = nova_versao(client, header_com_token, os_["numero_os"])
    assert (v1["versao"], v1["situacao"], v1["editavel"]) == (1, "RASCUNHO", True)
    assert os_atual(client, header_com_token, os_["numero_os"])["fase_fabrica"] == "ELABORACAO"
    assert nova_versao(client, header_com_token, os_["numero_os"])["versao"] == 2


def test_salvar_calcula_custos_totais_e_o_que_vai_para_a_os(client, header_com_token, modo_fabrica, abrir_os, insumos):
    os_ = abrir_os()
    v1 = nova_versao(client, header_com_token, os_["numero_os"])
    r = salvar(client, header_com_token, v1["id"], cozinha(insumos))
    assert r.status_code == 200, r.text
    orc = r.json()

    assert orc["total"] == 550000
    assert orc["sinal_valor"] == 275000
    aereo = orc["ambientes"][0]["moveis"][0]
    assert aereo["medidas"] == "1800×700×350"
    # MDF: 4 m² + 10% = 4,4 m² de uma chapa de R$ 300 (5,0875 m²) = R$ 259,46
    # Fita: 12 m + 10% = 13,2 m de um rolo de R$ 20 (50 m)      = R$ 5,28
    assert [m["custo"] for m in aereo["materiais"]] == [25946, 528]
    assert aereo["custo"] == 25946 + 528

    # 12 m² de MDF somados + 10% = 13,2 m² → 3 chapas (não 1 + 2 arredondando por móvel)
    insumos_os = {i["produto_id"]: i["quantidade"] for i in orc["insumos"]}
    assert insumos_os == {insumos["mdf"]: 3, insumos["fita"]: 1, insumos["dobradica"]: 6}


def test_produto_que_nao_e_insumo_e_recusado(client, header_com_token, modo_fabrica, abrir_os, insumos):
    os_ = abrir_os()
    v1 = nova_versao(client, header_com_token, os_["numero_os"])
    arvore = [{"nome": "Sala", "moveis": [{"nome": "Rack", "preco_venda": 1000,
                                           "materiais": [{"produto_id": insumos["comum"], "consumo": 1}]}]}]
    r = salvar(client, header_com_token, v1["id"], arvore)
    assert r.status_code == 422
    assert "Cola branca 1kg" in r.json()["detail"]


def test_custo_copiado_fica_e_linha_nova_pega_o_de_hoje(client, header_com_token, modo_fabrica, abrir_os, insumos, db_session):
    os_ = abrir_os()
    v1 = nova_versao(client, header_com_token, os_["numero_os"])
    orc = salvar(client, header_com_token, v1["id"], cozinha(insumos)).json()
    linha_mdf = orc["ambientes"][0]["moveis"][0]["materiais"][0]
    assert linha_mdf["custo_unitario"] == 30000

    db_session.get(Produto, insumos["mdf"]).estoque.custo_medio = 36000
    db_session.commit()

    arvore = cozinha(insumos)
    arvore[0]["moveis"][0]["materiais"][0]["id"] = linha_mdf["id"]   # a mesma linha
    orc = salvar(client, header_com_token, v1["id"], arvore).json()
    custos = [m["custo_unitario"] for mov in orc["ambientes"][0]["moveis"] for m in mov["materiais"]
              if m["produto_id"] == insumos["mdf"]]
    assert custos == [30000, 36000]


def test_copiar_versao_leva_a_arvore(client, header_com_token, modo_fabrica, abrir_os, insumos):
    os_ = abrir_os()
    v1 = nova_versao(client, header_com_token, os_["numero_os"])
    salvar(client, header_com_token, v1["id"], cozinha(insumos), validade=str(date.today() + timedelta(days=10)))
    v2 = nova_versao(client, header_com_token, os_["numero_os"], copiar_de=v1["id"])
    assert v2["versao"] == 2
    assert v2["total"] == 550000
    assert len(v2["ambientes"][0]["moveis"]) == 2


# --- enviar ------------------------------------------------------------------------------

def test_enviar_exige_movel_com_preco(client, header_com_token, modo_fabrica, abrir_os, insumos):
    os_ = abrir_os()
    v1 = nova_versao(client, header_com_token, os_["numero_os"])
    assert acao(client, header_com_token, v1["id"], "enviar").status_code == 422   # vazio
    salvar(client, header_com_token, v1["id"], cozinha(insumos, preco_balcao=0))
    r = acao(client, header_com_token, v1["id"], "enviar")
    assert r.status_code == 422
    assert "Balcão pia" in r.json()["detail"]


def test_enviado_nao_se_edita(client, header_com_token, modo_fabrica, abrir_os, insumos):
    os_ = abrir_os()
    v1 = nova_versao(client, header_com_token, os_["numero_os"])
    salvar(client, header_com_token, v1["id"], cozinha(insumos))
    r = acao(client, header_com_token, v1["id"], "enviar")
    assert r.json()["situacao"] == "ENVIADO"
    assert os_atual(client, header_com_token, os_["numero_os"])["fase_fabrica"] == "AGUARDANDO_APROVACAO"
    assert salvar(client, header_com_token, v1["id"], cozinha(insumos)).status_code == 409


# --- aprovar ---------------------------------------------------------------------------------

def test_aprovar_escreve_moveis_e_insumos_na_os(client, header_com_token, aprovada, insumos):
    os_ = os_atual(client, header_com_token, aprovada["numero_os"])
    assert os_["fase_fabrica"] == "AGUARDANDO_SINAL"
    assert os_["valor_total"] == 550000

    moveis = [i for i in os_["itens"] if i["tipo"] == "SERVICO"]
    assert [(i["nome"], i["valor_total"], i["visivel_cliente"]) for i in moveis] == [
        ("Cozinha — Armário aéreo (1800×700×350)", 240000, True),
        ("Cozinha — Balcão pia", 310000, True),
    ]
    insumos_os = {i["produto_id"]: (i["quantidade"], i["valor_total"], i["visivel_cliente"], i["custo_unitario"])
                  for i in os_["itens"] if i["tipo"] == "PRODUTO"}
    assert insumos_os == {
        insumos["mdf"]: (3, 0, False, 30000),
        insumos["fita"]: (1, 0, False, 2000),
        insumos["dobradica"]: (6, 0, False, 500),
    }
    assert all(i["fabrica_orcamento_id"] == aprovada["v1"] for i in os_["itens"])


def test_chapa_aprovada_ja_e_reserva_para_compras(client, header_com_token, aprovada, insumos, db_session):
    demandas = demandas_por_produto(db_session, [insumos["mdf"]])
    assert [(d.numero_os, d.quantidade) for d in demandas[insumos["mdf"]]] == [(aprovada["numero_os"], 3)]


def test_aprovar_outra_versao_troca_os_itens_sem_duplicar(client, header_com_token, aprovada, insumos):
    numero = aprovada["numero_os"]
    # Item lançado à mão: fica.
    r = client.post(f"{OS}/{numero}/itens", json={
        "tipo": "SERVICO", "nome": "Frete da obra", "unidade_medida": "UN", "quantidade": 1, "valor_unitario": 15000,
    }, headers=header_com_token)
    assert r.status_code in (200, 201), r.text

    v2 = nova_versao(client, header_com_token, numero, copiar_de=aprovada["v1"])
    arvore = cozinha(insumos)
    arvore[0]["moveis"].pop()          # o cliente desistiu do balcão
    salvar(client, header_com_token, v2["id"], arvore)
    acao(client, header_com_token, v2["id"], "enviar")
    assert acao(client, header_com_token, v2["id"], "aprovar").status_code == 200

    os_ = os_atual(client, header_com_token, numero)
    nomes = sorted(i["nome"] for i in os_["itens"])
    assert nomes == sorted(["Cozinha — Armário aéreo (1800×700×350)", "MDF Branco 15mm",
                            "Fita de borda branca 22mm", "Frete da obra"])
    mdf = next(i for i in os_["itens"] if i["produto_id"] == insumos["mdf"])
    assert mdf["quantidade"] == 1                      # 4,4 m² → 1 chapa
    assert os_["valor_total"] == 240000 + 15000

    versoes = {v["versao"]: v for v in client.get(f"{FAB}/os/{numero}/orcamentos", headers=header_com_token).json()}
    assert (versoes[1]["situacao"], versoes[2]["situacao"]) == ("RECUSADO", "APROVADO")
    assert "versão 2" in client.get(f"{FAB}/orcamentos/{aprovada['v1']}", headers=header_com_token).json()["recusado_motivo"]


def test_item_gerado_nao_se_edita_pela_os(client, header_com_token, aprovada):
    numero = aprovada["numero_os"]
    item = os_atual(client, header_com_token, numero)["itens"][0]
    r = client.put(f"{OS}/{numero}/itens/{item['id']}", json={"quantidade": 9}, headers=header_com_token)
    assert r.status_code == 409
    assert client.delete(f"{OS}/{numero}/itens/{item['id']}", headers=header_com_token).status_code == 409


def test_aprovar_so_o_enviado(client, header_com_token, modo_fabrica, abrir_os, insumos):
    os_ = abrir_os()
    v1 = nova_versao(client, header_com_token, os_["numero_os"])
    salvar(client, header_com_token, v1["id"], cozinha(insumos))
    assert acao(client, header_com_token, v1["id"], "aprovar").status_code == 409


def test_vencido_nao_se_aprova(client, header_com_token, modo_fabrica, abrir_os, insumos):
    os_ = abrir_os()
    v1 = nova_versao(client, header_com_token, os_["numero_os"])
    salvar(client, header_com_token, v1["id"], cozinha(insumos), validade=str(date.today() - timedelta(days=1)))
    acao(client, header_com_token, v1["id"], "enviar")
    assert client.get(f"{FAB}/orcamentos/{v1['id']}", headers=header_com_token).json()["situacao"] == "VENCIDO"
    r = acao(client, header_com_token, v1["id"], "aprovar")
    assert r.status_code == 409
    assert "vencido" in r.json()["detail"]


# --- recusar -----------------------------------------------------------------------------------

def test_recusar_volta_a_orcar(client, header_com_token, modo_fabrica, abrir_os, insumos):
    os_ = abrir_os()
    v1 = nova_versao(client, header_com_token, os_["numero_os"])
    salvar(client, header_com_token, v1["id"], cozinha(insumos))
    acao(client, header_com_token, v1["id"], "enviar")
    r = acao(client, header_com_token, v1["id"], "recusar", motivo="Achou caro")
    assert (r.json()["situacao"], r.json()["recusado_motivo"]) == ("RECUSADO", "Achou caro")
    assert os_atual(client, header_com_token, os_["numero_os"])["fase_fabrica"] == "ELABORACAO"


# --- não-regressão (F12) --------------------------------------------------------------------------

def test_os_comum_continua_editando_itens(client, header_com_token, modo_fabrica, abrir_os):
    modo_fabrica(False)
    numero = abrir_os()["numero_os"]
    r = client.post(f"{OS}/{numero}/itens", json={
        "tipo": "SERVICO", "nome": "Cozinha metro linear", "unidade_medida": "M", "quantidade": 3, "valor_unitario": 90000,
    }, headers=header_com_token)
    assert r.status_code in (200, 201), r.text
    item = next(i for i in r.json()["itens"])
    assert item["fabrica_orcamento_id"] is None
    r = client.put(f"{OS}/{numero}/itens/{item['id']}", json={"quantidade": 4}, headers=header_com_token)
    assert r.status_code == 200, r.text
    assert client.delete(f"{OS}/{numero}/itens/{item['id']}", headers=header_com_token).status_code in (200, 204)


# --- busca de insumo ------------------------------------------------------------------

def test_busca_traz_so_insumos(client, header_com_token, modo_fabrica, insumos):
    r = client.get(f"{FAB}/insumos", headers=header_com_token)
    assert r.status_code == 200
    nomes = [i["nome"] for i in r.json()]
    assert nomes == ["Dobradiça 35mm", "Fita de borda branca 22mm", "MDF Branco 15mm"]   # sem a cola
    mdf = client.get(f"{FAB}/insumos", params={"busca": "mdf"}, headers=header_com_token).json()
    assert [(i["unidade_consumo"], i["consumo_por_unidade"], i["custo_unitario"]) for i in mdf] == [("M2", CHAPA_MM2, 30000)]
