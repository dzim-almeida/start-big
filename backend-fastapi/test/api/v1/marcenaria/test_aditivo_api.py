# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/marcenaria/test_aditivo_api.py
# DESCRICAO: ADITIVO do orcamento de marcenaria (remodelacao item 20): moveis a
#            mais para uma OS que ja existe.
#
#            O que nao pode errar:
#              - o aditivo nasce da OS com o cliente/projeto/parametros dela;
#              - aprovado, SOMA na mesma OS (nenhuma OS nova): itens, total,
#                material (sem duplicar o produto) e as abas (producao, entrega);
#              - desfazer volta a OS exatamente ao que era antes dele;
#              - o orcamento principal nao se desfaz com aditivo aprovado.
# ---------------------------------------------------------------------------

import pytest

from app.db.models.marcenaria import MarcenariaOrcamento
from app.db.models.ordem_servico import OrdemServico
from app.db.models.produto import Produto

from test.apoio_orcamento_marcenaria import URL_MARCENARIA, aprovar, montar_cenario_b, os_da_api


@pytest.fixture
def os_aprovada(api, produto, fornecedor, cliente_id) -> dict:
    """O cenario B aprovado inteiro: o orcamento principal e a OS dele."""
    d = montar_cenario_b(api, produto, fornecedor, cliente=cliente_id)
    d = api.ok("POST", f"/{d['id']}/enviar", rev=d["revisao"])
    return aprovar(api, d)


def _criar_aditivo(api, numero_os: str, esperado: int = 201):
    r = api.req("POST", f"/por-os/{numero_os}/aditivos")
    assert r.status_code == esperado, r.text
    return r.json() if esperado == 201 else r


def _id_produto(db_session, nome: str) -> int:
    return db_session.query(Produto).filter(Produto.nome == nome).one().id


def _aditivo_com_movel(api, db_session, produto, numero_os: str) -> dict:
    """Aditivo com 1 ambiente ("Escritório") e 1 movel interno: usa o MDF Branco
    (produto que a OS ja tem) e um produto novo (Puxador)."""
    a = _criar_aditivo(api, numero_os)
    d = api.ok("POST", f"/{a['id']}/ambientes", rev=a["revisao"], esperado=201, json={"nome": "Escritório"})
    amb = d["ambientes"][0]["id"]
    puxador = produto("Puxador Cava", valor_entrada=2500, sofre_perda=False)
    return api.ok("POST", f"/{a['id']}/ambientes/{amb}/moveis", rev=d["revisao"], esperado=201, json={
        "nome": "Escrivaninha", "quantidade": 1,
        "mao_obra": {"modo": "FIXA", "centavos": 20000, "horas_centesimos": 0},
        "insumos": [
            {"produto_id": _id_produto(db_session, "MDF Branco TX 18mm"), "quantidade_milesimos": 500},
            {"produto_id": puxador, "quantidade_milesimos": 2000},
        ],
    })


def _peca(os_: dict, nome: str) -> dict:
    return next(i for i in os_["itens"] if i["tipo"] == "PRODUTO" and i["nome"].startswith(nome))


# ---------------------------------------------------------------------------
# CRIAR
# ---------------------------------------------------------------------------

def test_criar_aditivo_copia_a_obra_da_os_sem_moveis(api, os_aprovada):
    numero = os_aprovada["os"]["numero_os"]
    a = _criar_aditivo(api, numero)

    assert a["status"] == "RASCUNHO" and a["codigo"] != os_aprovada["codigo"]
    assert a["aditivo_de"]["numero_os"] == numero
    assert a["cliente"]["id"] == os_aprovada["cliente"]["id"]
    assert a["projeto"]["nome"] == os_aprovada["projeto"]["nome"]
    assert a["parametros"] == os_aprovada["parametros"]                  # markup, perda, custo/hora...
    assert [x["fornecedor_id"] for x in a["arquitetos"]] == [x["fornecedor_id"] for x in os_aprovada["arquitetos"]]
    assert a["ambientes"] == []


def test_aditivo_nao_troca_cliente_nem_projeto(api, os_aprovada, cliente_id):
    a = _criar_aditivo(api, os_aprovada["os"]["numero_os"])
    r = api.req("PATCH", f"/{a['id']}", rev=a["revisao"], json={"cliente_id": None})
    assert r.status_code == 422, r.text
    assert "não mudam" in r.text


def test_os_fechada_ou_sem_orcamento_nao_recebe_aditivo(api, os_aprovada, db_session):
    numero = os_aprovada["os"]["numero_os"]
    _criar_aditivo(api, "OS-0000-999999", esperado=404)
    os_ = db_session.query(OrdemServico).filter_by(numero_os=numero).one()
    os_.status = "FINALIZADA"
    db_session.commit()
    r = _criar_aditivo(api, numero, esperado=409)
    assert r.json()["detail"]["codigo"] == "OS_FECHADA"


# ---------------------------------------------------------------------------
# APROVAR: soma na mesma OS
# ---------------------------------------------------------------------------

def test_aprovar_aditivo_soma_na_mesma_os(api, os_aprovada, db_session, produto):
    numero = os_aprovada["os"]["numero_os"]
    antes = os_da_api(api, numero)
    mdf_antes = _peca(antes, "MDF Branco")["quantidade"]

    a = _aditivo_com_movel(api, db_session, produto, numero)
    a = api.ok("POST", f"/{a['id']}/enviar", rev=a["revisao"])
    aprovado = aprovar(api, a)

    assert aprovado["status"] == "APROVADO" and aprovado["os"]["numero_os"] == numero
    assert db_session.query(OrdemServico).count() == 1                    # nenhuma OS nova
    depois = os_da_api(api, numero)
    assert depois["valor_bruto"] == antes["valor_bruto"] + a["calculo"]["bruto_centavos"]
    assert depois["valor_total"] == antes["valor_total"] + a["calculo"]["total_centavos"]
    nomes = [i["nome"] for i in depois["itens"] if i["tipo"] == "SERVICO"]
    assert "Escrivaninha — Escritório" in nomes
    # Material: o MDF que a OS ja tinha CRESCE (mesma linha); o puxador e peca nova.
    assert len([i for i in depois["itens"] if i["tipo"] == "PRODUTO" and i["nome"].startswith("MDF Branco")]) == 1
    assert _peca(depois, "MDF Branco")["quantidade"] >= mdf_antes
    assert _peca(depois, "Puxador")["quantidade"] == 2
    # O principal continua sendo "o orcamento da OS".
    principal = db_session.get(MarcenariaOrcamento, os_aprovada["id"])
    assert principal.status == "APROVADO" and principal.os_id == depois["id"]


def test_abas_da_os_mostram_o_aditivo(api, os_aprovada, db_session, produto):
    numero = os_aprovada["os"]["numero_os"]
    a = _aditivo_com_movel(api, db_session, produto, numero)
    aprovar(api, api.ok("POST", f"/{a['id']}/enviar", rev=a["revisao"]))

    producao = api.client.get(f"{URL_MARCENARIA}/os/{numero}/producao", headers=api.header).json()
    assert "Escrivaninha" in [m["nome"] for m in producao["moveis"]]
    entrega = api.client.get(f"{URL_MARCENARIA}/os/{numero}/entrega", headers=api.header).json()
    # Uma entrega por ambiente: o do principal primeiro, depois o do aditivo.
    assert [e["ambiente"] for e in entrega["entregas"]] == ["Cozinha Gourmet", "Escritório"]
    separacao = api.client.get(f"{URL_MARCENARIA}/os/{numero}/separacao", headers=api.header).json()
    assert any(linha["descricao"].startswith("Puxador") for linha in separacao["linhas"])
    # A aba Orcamento da OS lista o aditivo e soma o total aprovado.
    resumo = api.req("GET", f"/por-os/{numero}").json()
    assert [x["codigo"] for x in resumo["aditivos"]] == [a["codigo"]]
    assert resumo["total_geral_aprovado_centavos"] == (
        resumo["total_aprovado_centavos"] + resumo["aditivos"][0]["total_aprovado_centavos"]
    )
    # O quadro da fabrica continua com UMA linha para a OS.
    quadro = api.client.get(f"{URL_MARCENARIA}/producao", headers=api.header).json()
    assert [i["numero_os"] for i in quadro["itens"]].count(numero) == 1


# ---------------------------------------------------------------------------
# DESFAZER
# ---------------------------------------------------------------------------

def test_principal_nao_se_desfaz_com_aditivo_aprovado(api, os_aprovada, db_session, produto):
    numero = os_aprovada["os"]["numero_os"]
    a = _aditivo_com_movel(api, db_session, produto, numero)
    aprovar(api, api.ok("POST", f"/{a['id']}/enviar", rev=a["revisao"]))

    principal = api.detalhe(os_aprovada["id"])
    r = api.req("POST", f"/{principal['id']}/desfazer-aprovacao", rev=principal["revisao"],
                json={"motivo": "teste"})
    assert r.status_code == 409, r.text
    assert any("aditivo aprovado" in m for m in r.json()["detail"]["motivos"])


def test_desfazer_aditivo_volta_a_os_ao_que_era(api, os_aprovada, db_session, produto):
    numero = os_aprovada["os"]["numero_os"]
    antes = os_da_api(api, numero)
    a = _aditivo_com_movel(api, db_session, produto, numero)
    aprovado = aprovar(api, api.ok("POST", f"/{a['id']}/enviar", rev=a["revisao"]))

    r = api.req("POST", f"/{aprovado['id']}/desfazer-aprovacao", rev=aprovado["revisao"],
                json={"motivo": "Cliente desistiu da escrivaninha"})
    assert r.status_code == 200, r.text
    assert api.detalhe(aprovado["id"])["status"] == "ENVIADO"

    depois = os_da_api(api, numero)
    assert depois["status"] == antes["status"]                            # a OS NAO foi cancelada
    assert (depois["valor_bruto"], depois["valor_total"]) == (antes["valor_bruto"], antes["valor_total"])
    assert sorted((i["nome"], i["quantidade"]) for i in depois["itens"]) == \
        sorted((i["nome"], i["quantidade"]) for i in antes["itens"])
    # Sem aditivo aprovado, o principal volta a poder ser desfeito.
    assert api.req("GET", f"/por-os/{numero}").json()["pode_desfazer"] is True


# ---------------------------------------------------------------------------
# RT DO ARQUITETO NA FINALIZACAO
# ---------------------------------------------------------------------------

def test_finalizar_os_paga_o_rt_do_principal_e_do_aditivo(api, os_aprovada, db_session, produto, forma_pagamento):
    from app.db.models.conta_pagar import ContaPagar

    numero = os_aprovada["os"]["numero_os"]
    a = _aditivo_com_movel(api, db_session, produto, numero)
    aditivo = aprovar(api, api.ok("POST", f"/{a['id']}/enviar", rev=a["revisao"]))

    total = os_da_api(api, numero)["valor_total"]
    r = api.client.put(f"/api/v1/ordens-servico/{numero}/finalizar", json={
        "situacao_equipamento": "REPARADO",
        "pagamentos": [{"forma_pagamento_id": forma_pagamento("PIX"), "valor": total}],
    }, headers=api.header)
    assert r.status_code == 200, r.text

    db_session.expire_all()
    contas = db_session.query(ContaPagar).order_by(ContaPagar.id).all()
    # Uma conta por orcamento (o arquiteto e o mesmo): cada uma diz de qual codigo e.
    assert [os_aprovada["codigo"] in c.descricao for c in contas] == [True, False]
    assert [aditivo["codigo"] in c.descricao for c in contas] == [False, True]
    # A OS confere com a SOMA aprovada: nenhuma observacao de divergencia.
    assert all(c.observacao is None for c in contas)
