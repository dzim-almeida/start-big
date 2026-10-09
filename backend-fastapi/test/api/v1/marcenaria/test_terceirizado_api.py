# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/marcenaria/test_terceirizado_api.py
# DESCRICAO: Moveis terceirizados da OS da marcenaria (Spec 11A, secao 11,
#            casos 01-18), pela API, com e sem o modulo Compras.
#
#            O que nao pode errar:
#              - com o Compras: UM pedido de SERVICO por central, e a situacao
#                do movel acompanha o pedido (o Compras nao muda);
#              - sem o Compras: o acompanhamento a mao;
#              - conferir/problema/voltar nos dois modos;
#              - desfazer bloqueado com pedido; cancelar a OS so avisa;
#              - nenhum valor sem `view_custos_marcenaria`.
# ---------------------------------------------------------------------------

from datetime import timedelta

import pytest

from app.core.tempo import hoje_local
from app.db.models.conta_pagar import ContaPagar
from app.db.models.marcenaria import MarcenariaEvento
from app.db.models.marcenaria.ambiente import MarcenariaMovel
from app.db.models.movimentacao_estoque import MovimentacaoEstoque
from app.db.models.pedido_compra import PedidoCompra, SituacaoPedido, TipoPedido
from app.db.models.usuario import Usuario

from test.apoio_orcamento_marcenaria import EMAIL_MASTER, URL_MARCENARIA, aprovar

OS_URL = "/api/v1/ordens-servico"
COMPRAS_URL = "/api/v1/compras/pedidos"


# =========================
# Ajudantes
# =========================

@pytest.fixture
def licenca(monkeypatch):
    """Define os modulos da licenca (sem chamar: nenhuma licenca = sem o Compras)."""
    from app.services import licenca as licenca_service

    def _definir(*modulos: str):
        monkeypatch.setattr(licenca_service, "modulos_da_licenca", lambda _db: list(modulos))
    return _definir


class Terceirizados:
    """Atalho para a API dos terceirizados de uma OS."""

    def __init__(self, api, numero_os: str):
        self.api, self.numero_os = api, numero_os

    def req(self, metodo: str, caminho: str = "", **kwargs):
        return self.api.client.request(metodo, f"{URL_MARCENARIA}/os/{self.numero_os}/terceirizados{caminho}",
                                       headers=self.api.header, **kwargs)

    def ler(self) -> dict:
        r = self.req("GET")
        assert r.status_code == 200, r.text
        return r.json()

    def movel(self, nome: str) -> dict:
        return next(m for m in self.ler()["moveis"] if m["nome"] == nome)

    def post(self, caminho: str, json: dict = None, esperado: int = 200):
        r = self.req("POST", caminho, json=json if json is not None else {})
        assert r.status_code == esperado, r.text
        return r.json()


def _movel_terceirizado(nome: str, central: int) -> dict:
    return {
        "nome": nome, "quantidade": 1, "largura_mm": 700, "altura_mm": 2200, "profundidade_mm": 600,
        "tipo_producao": "TERCEIRIZADA", "central_fornecedor_id": central, "terceirizado_centavos": 38000,
        "mao_obra": {"modo": "FIXA", "centavos": 10000, "horas_centesimos": 0}, "insumos": [],
    }


@pytest.fixture
def obra(api, fornecedor, produto, cliente_id):
    """OS com Torre Quente e Torre Fria (central Madeiranit), Painel (central Outra)
    e um Balcao INTERNO. Devolve (Terceirizados, {nome: movel_id}, id da Madeiranit)."""
    madeiranit, outra = fornecedor("Madeiranit"), fornecedor("Outra Central")
    chapa = produto("Chapa MDP", valor_entrada=15000, sofre_perda=False)
    orc = api.criar(cliente_id=cliente_id, projeto_nome="Apto 802")
    d = api.ok("POST", f"/{orc['id']}/ambientes", rev=orc["revisao"], esperado=201, json={"nome": "Cozinha Gourmet"})
    amb = d["ambientes"][0]["id"]
    for corpo in (_movel_terceirizado("Torre Quente", madeiranit), _movel_terceirizado("Torre Fria", madeiranit),
                  _movel_terceirizado("Painel", outra),
                  {"nome": "Balcão", "quantidade": 1, "mao_obra": {"modo": "FIXA", "centavos": 10000, "horas_centesimos": 0},
                   "insumos": [{"produto_id": chapa, "quantidade_milesimos": 1000}]}):
        d = api.ok("POST", f"/{orc['id']}/ambientes/{amb}/moveis", rev=d["revisao"], esperado=201, json=corpo)
    d = aprovar(api, d)
    ids = {m["nome"]: m["id"] for a in d["ambientes"] for m in a["moveis"]}
    return Terceirizados(api, d["os"]["numero_os"]), ids, madeiranit


def _pedir(t: Terceirizados, ids: list[int], esperado: int = 200, **extra):
    return t.post("/pedir", {"movel_ids": ids, **extra}, esperado)


def _pedido(db, pedido_id: int) -> PedidoCompra:
    db.expire_all()
    return db.get(PedidoCompra, pedido_id)


# =========================
# Leitura (01, 18)
# =========================

def test_01_aprovados_nascem_a_pedir_sem_pedido(obra):
    t, _ids, madeiranit = obra
    leitura = t.ler()
    assert [m["nome"] for m in leitura["moveis"]] == ["Torre Quente", "Torre Fria", "Painel"]   # sem o Balcao interno
    torre = leitura["moveis"][0]
    assert (torre["situacao"], torre["pedido"], torre["atrasado"], torre["previsao"]) == ("A_PEDIR", None, False, None)
    assert torre["central"] == {"id": madeiranit, "nome": "Madeiranit", "telefone": None}
    assert torre["medidas"] == {"largura_mm": 700, "altura_mm": 2200, "profundidade_mm": 600}
    assert leitura["modo_compras"] is False                    # sem licenca = sem o Compras
    assert leitura["os"]["editavel"] is True


def test_18_valor_orcado_so_com_custos(obra, como):
    t, _ids, _m = obra
    assert t.movel("Torre Quente")["valor_orcado_centavos"] == 38000   # master ve
    como(servico=True)
    assert "valor_orcado_centavos" not in t.movel("Torre Quente")
    como(servico=True, view_custos_marcenaria=True)
    assert t.movel("Torre Quente")["valor_orcado_centavos"] == 38000


# =========================
# Com o Compras (02-08, 14-17)
# =========================

def test_02_pedir_dois_cria_um_pedido_de_servico_em_rascunho(obra, licenca, db_session):
    licenca("COMPRAS")
    t, ids, madeiranit = obra
    resposta = _pedir(t, [ids["Torre Quente"], ids["Torre Fria"]], previsao_entrega="2026-12-01", observacao="Urgente")

    pedido = _pedido(db_session, resposta["pedido"]["id"])
    assert (pedido.tipo, pedido.situacao, pedido.fornecedor_id) == (TipoPedido.SERVICO, SituacaoPedido.RASCUNHO, madeiranit)
    assert [(i.produto_id, i.unidade_compra, i.quantidade, i.custo_unitario) for i in pedido.itens] == [
        (None, "SV", 1, 38000), (None, "SV", 1, 38000)]
    assert pedido.itens[0].descricao == f"Serviço: Cozinha Gourmet — Torre Quente (700 × 2200 × 600 mm) · {t.numero_os}"
    assert (pedido.valor_total, str(pedido.previsao_entrega), pedido.observacao) == (76000, "2026-12-01", "Urgente")
    assert resposta["pedido"]["codigo"] == pedido.codigo and resposta["pedido"]["valor_total_centavos"] == 76000
    db_session.expire_all()
    assert db_session.get(MarcenariaMovel, ids["Torre Quente"]).pedido_compra_id == pedido.id
    torre = next(m for m in resposta["terceirizados"]["moveis"] if m["nome"] == "Torre Quente")
    assert torre["situacao"] == "A_PEDIR"                                   # rascunho ainda nao saiu
    assert torre["pedido"] == {"origem": "COMPRAS", "id": pedido.id, "codigo": pedido.codigo, "situacao": "RASCUNHO"}
    assert resposta["terceirizados"]["modo_compras"] is True
    evento = db_session.query(MarcenariaEvento).filter_by(tipo="TERCEIRIZADO_PEDIDO").one()
    assert evento.descricao == f"Pedido {pedido.codigo} à central Madeiranit: Torre Quente, Torre Fria."


def test_03_centrais_diferentes_no_mesmo_pedido_e_422(obra, licenca):
    licenca("COMPRAS")
    t, ids, _m = obra
    r = _pedir(t, [ids["Torre Quente"], ids["Painel"]], esperado=422)
    assert r["detail"] == "Os móveis do mesmo pedido precisam ser da mesma central."


def test_movel_interno_e_422_e_de_outra_os_e_404(obra, licenca):
    licenca("COMPRAS")
    t, ids, _m = obra
    assert _pedir(t, [ids["Balcão"]], esperado=422)["detail"] == "Este móvel não é terceirizado."
    assert _pedir(t, [999999], esperado=404)["detail"] == "Este móvel não faz parte desta OS."


def test_04_pedir_de_novo_e_409(obra, licenca):
    licenca("COMPRAS")
    t, ids, _m = obra
    codigo = _pedir(t, [ids["Torre Quente"]])["pedido"]["codigo"]
    r = _pedir(t, [ids["Torre Quente"]], esperado=409)
    assert r["detail"] == {"codigo": "JA_PEDIDO", "mensagem": f"O móvel Torre Quente já está no pedido {codigo}."}


def test_05_a_08_situacao_acompanha_o_pedido(api, obra, licenca, db_session):
    licenca("COMPRAS", "FINANCEIRO")
    t, ids, _m = obra
    pedido_id = _pedir(t, [ids["Torre Quente"]], previsao_entrega=str(hoje_local() + timedelta(days=10)))["pedido"]["id"]

    r = api.client.post(f"{COMPRAS_URL}/{pedido_id}/enviar", headers=api.header)              # 05: pelo Compras
    assert r.status_code == 200, r.text
    torre = t.movel("Torre Quente")
    assert (torre["situacao"], torre["previsao"], torre["atrasado"]) == ("ENVIADO", str(hoje_local() + timedelta(days=10)), False)
    assert torre["enviado_em"] == str(hoje_local())

    item_id = _pedido(db_session, pedido_id).itens[0].id                                      # 06: recebe
    r = api.client.post(f"{COMPRAS_URL}/{pedido_id}/recebimentos", headers=api.header,
                        json={"itens": [{"pedido_item_id": item_id, "quantidade": 1}]})
    assert r.status_code == 201, r.text
    torre = t.movel("Torre Quente")
    assert (torre["situacao"], torre["recebido_em"]) == ("RECEBIDO", str(hoje_local()))
    db_session.expire_all()
    conta = db_session.query(ContaPagar).filter(ContaPagar.recebimento_compra_id.is_not(None)).one()   # lancada pelo Compras
    assert (conta.valor, conta.plano_conta_id) == (38000, None)                              # sem categoria (17)
    assert db_session.query(MovimentacaoEstoque).count() == 0                                # servico nao entra no estoque

    leitura = t.post("/conferir", {"movel_ids": [ids["Torre Quente"]]})                      # 07
    torre = next(m for m in leitura["moveis"] if m["nome"] == "Torre Quente")
    assert (torre["situacao"], torre["conferido_em"]) == ("CONFERIDO", str(hoje_local()))


def test_08_cancelar_o_pedido_no_compras_volta_a_pedir(api, obra, licenca):
    licenca("COMPRAS")
    t, ids, _m = obra
    pedido_id = _pedir(t, [ids["Torre Quente"]])["pedido"]["id"]
    r = api.client.post(f"{COMPRAS_URL}/{pedido_id}/cancelar", json={"motivo": "Central sem prazo"}, headers=api.header)
    assert r.status_code == 200, r.text
    torre = t.movel("Torre Quente")
    assert (torre["situacao"], torre["pedido"]) == ("A_PEDIR", None)
    assert _pedir(t, [ids["Torre Quente"]])["pedido"]["id"] != pedido_id                    # pode pedir de novo


def test_09_sem_o_compras_pedir_e_403(obra):
    t, ids, _m = obra
    r = _pedir(t, [ids["Torre Quente"]], esperado=403)
    assert r["detail"]["codigo"] == "MODULO_NAO_CONTRATADO"


def test_pedir_exige_a_permissao_de_compras(obra, licenca, como, db_session):
    licenca("COMPRAS")
    t, ids, _m = obra
    como(servico=True)                                                                       # OS sim, compras nao
    _pedir(t, [ids["Torre Quente"]], esperado=403)
    token = como(servico=True, manage_purchases=True)
    # O pedido grava quem criou (chave para `usuarios`): o token tem de ser de um usuario real.
    token["sub"] = str(db_session.query(Usuario).filter_by(email=EMAIL_MASTER).one().id)
    resposta = _pedir(t, [ids["Torre Quente"]])
    assert "valor_total_centavos" in resposta["pedido"]                                      # quem gerencia compras ve


def test_14_acao_manual_num_movel_com_pedido_do_compras_e_409(obra, licenca):
    licenca("COMPRAS")
    t, ids, _m = obra
    _pedir(t, [ids["Torre Quente"]])
    for caminho, corpo in (("/enviar-manual", {"movel_ids": [ids["Torre Quente"]]}),
                           ("/receber-manual", {"movel_ids": [ids["Torre Quente"]]})):
        r = t.post(caminho, corpo, esperado=409)
        assert r["detail"] == {"codigo": "PEDIDO_NO_COMPRAS", "mensagem": "Este móvel tem pedido no Compras: envie e receba por lá."}
    assert t.post(f"/{ids['Torre Quente']}/voltar", esperado=409)["detail"]["codigo"] == "PEDIDO_NO_COMPRAS"


def test_15_desfazer_bloqueado_com_pedido_em_rascunho(api, obra, licenca):
    licenca("COMPRAS")
    t, ids, _m = obra
    codigo = _pedir(t, [ids["Torre Quente"]])["pedido"]["codigo"]
    resumo = api.ok("GET", f"/por-os/{t.numero_os}")
    assert resumo["pode_desfazer"] is False
    assert (f"Já há pedido à central Madeiranit ({codigo}). Cancele o pedido no Compras "
            "e volte o móvel para 'A pedir' antes de desfazer.") in resumo["motivos_desfazer"]


def test_16_cancelar_os_avisa_e_nao_mexe_no_pedido(api, obra, licenca, db_session):
    licenca("COMPRAS", "FINANCEIRO")
    t, ids, _m = obra
    pedido_id = _pedir(t, [ids["Torre Quente"]])["pedido"]["id"]
    api.client.post(f"{COMPRAS_URL}/{pedido_id}/enviar", headers=api.header)
    item_id = _pedido(db_session, pedido_id).itens[0].id
    api.client.post(f"{COMPRAS_URL}/{pedido_id}/recebimentos", headers=api.header,
                    json={"itens": [{"pedido_item_id": item_id, "quantidade": 1}]})

    r = api.client.put(f"{OS_URL}/{t.numero_os}/cancelar", json={"motivo": "Cliente desistiu"}, headers=api.header)
    assert r.status_code == 200, r.text

    pedido = _pedido(db_session, pedido_id)
    evento = db_session.query(MarcenariaEvento).filter_by(tipo="TERCEIRIZADOS_EM_OS_CANCELADA").one()
    assert evento.descricao == (f"Há móveis pedidos à central para esta OS: Torre Quente ({pedido.codigo}, Recebido). "
                                "Combine com a central.")
    assert pedido.situacao == SituacaoPedido.RECEBIDO                                         # intacto
    assert db_session.query(ContaPagar).filter_by(status="PENDENTE").count() == 1            # a conta tambem
    assert t.ler()["os"]["editavel"] is False
    assert t.post("/conferir", {"movel_ids": [ids["Torre Quente"]]}, esperado=409)["detail"]["codigo"] == "OS_FECHADA"


# =========================
# Sem o Compras (10-13)
# =========================

def test_10_enviar_manual_com_previsao_vencida_fica_atrasado(obra, db_session):
    t, ids, _m = obra
    ontem = hoje_local() - timedelta(days=1)
    leitura = t.post("/enviar-manual", {"movel_ids": [ids["Torre Quente"], ids["Torre Fria"]],
                                        "pedido": " 4521 ", "previsao": str(ontem)})
    torre = next(m for m in leitura["moveis"] if m["nome"] == "Torre Quente")
    assert (torre["situacao"], torre["atrasado"], torre["previsao"]) == ("ENVIADO", True, str(ontem))
    assert torre["pedido"] == {"origem": "MANUAL", "numero": "4521"}
    assert torre["enviado_em"] == str(hoje_local())
    evento = db_session.query(MarcenariaEvento).filter_by(tipo="TERCEIRIZADO_ENVIADO").one()
    assert evento.descricao == (f"Pedido à central Madeiranit anotado (nº 4521, previsão {ontem:%d/%m/%Y}): "
                                "Torre Quente, Torre Fria.")


def test_11_receber_e_conferir_a_mao(obra):
    t, ids, _m = obra
    torre = [ids["Torre Quente"]]
    t.post("/enviar-manual", {"movel_ids": torre})
    leitura = t.post("/receber-manual", {"movel_ids": torre, "data": "2026-10-01"})
    assert next(m for m in leitura["moveis"] if m["nome"] == "Torre Quente")["recebido_em"] == "2026-10-01"
    assert t.movel("Torre Quente")["situacao"] == "RECEBIDO"
    t.post("/conferir", {"movel_ids": torre})
    assert t.movel("Torre Quente")["situacao"] == "CONFERIDO"


def test_fora_de_ordem_e_409(obra):
    t, ids, _m = obra
    r = t.post("/receber-manual", {"movel_ids": [ids["Torre Quente"]]}, esperado=409)
    assert r["detail"] == {"codigo": "TRANSICAO_INVALIDA", "mensagem": "Ação não permitida: o móvel Torre Quente está a pedir."}
    assert t.post("/conferir", {"movel_ids": [ids["Torre Quente"]]}, esperado=409)["detail"]["codigo"] == "TRANSICAO_INVALIDA"


def test_12_problema_deixa_recebido_e_conferir_limpa(obra, db_session):
    t, ids, _m = obra
    torre = ids["Torre Quente"]
    t.post("/enviar-manual", {"movel_ids": [torre]})
    t.post("/receber-manual", {"movel_ids": [torre]})
    t.post("/conferir", {"movel_ids": [torre]})

    t.post(f"/{torre}/problema", {"texto": "  Porta riscada  "})
    movel = t.movel("Torre Quente")
    assert (movel["situacao"], movel["problema"], movel["conferido_em"]) == ("RECEBIDO", "Porta riscada", None)
    assert t.post(f"/{torre}/problema", {"texto": "   "}, esperado=422)

    t.post("/conferir", {"movel_ids": [torre]})
    assert (t.movel("Torre Quente")["situacao"], t.movel("Torre Quente")["problema"]) == ("CONFERIDO", None)


def test_13_voltar_um_passo_ate_a_pedir(obra):
    t, ids, _m = obra
    torre = ids["Torre Quente"]
    t.post("/enviar-manual", {"movel_ids": [torre], "pedido": "4521", "previsao": "2026-12-01"})
    t.post("/receber-manual", {"movel_ids": [torre]})
    t.post("/conferir", {"movel_ids": [torre]})

    for esperada in ("RECEBIDO", "ENVIADO", "A_PEDIR"):
        t.post(f"/{torre}/voltar")
        assert t.movel("Torre Quente")["situacao"] == esperada
    movel = t.movel("Torre Quente")
    assert (movel["pedido"], movel["previsao"], movel["enviado_em"]) == (None, None, None)   # A pedir limpa
    assert t.post(f"/{torre}/voltar", esperado=409)["detail"]["codigo"] == "TRANSICAO_INVALIDA"


def test_13_voltar_de_conferido_com_pedido_do_compras(api, obra, licenca, db_session):
    licenca("COMPRAS")
    t, ids, _m = obra
    pedido_id = _pedir(t, [ids["Torre Quente"]])["pedido"]["id"]
    api.client.post(f"{COMPRAS_URL}/{pedido_id}/enviar", headers=api.header)
    item_id = _pedido(db_session, pedido_id).itens[0].id
    api.client.post(f"{COMPRAS_URL}/{pedido_id}/recebimentos", headers=api.header,
                    json={"itens": [{"pedido_item_id": item_id, "quantidade": 1}], "lancar_contas_pagar": False})
    t.post("/conferir", {"movel_ids": [ids["Torre Quente"]]})
    t.post(f"/{ids['Torre Quente']}/voltar")
    assert t.movel("Torre Quente")["situacao"] == "RECEBIDO"


def test_desfazer_bloqueado_com_envio_manual(api, obra):
    t, ids, _m = obra
    t.post("/enviar-manual", {"movel_ids": [ids["Painel"]]})
    motivos = api.ok("GET", f"/por-os/{t.numero_os}")["motivos_desfazer"]
    assert ("Já há pedido à central Outra Central para o móvel Painel. "
            "Volte o móvel para 'A pedir' antes de desfazer.") in motivos


# =========================
# Lista geral (D17), permissao e capacidade
# =========================

def test_lista_geral_atrasados_primeiro_e_filtros(api, obra, cliente_id):
    t, ids, madeiranit = obra
    ontem = str(hoje_local() - timedelta(days=1))
    t.post("/enviar-manual", {"movel_ids": [ids["Torre Fria"]], "previsao": ontem})

    def lista(**params):
        r = api.client.get(f"{URL_MARCENARIA}/terceirizados", params=params, headers=api.header)
        assert r.status_code == 200, r.text
        return r.json()["itens"]

    todos = lista()
    assert [i["nome"] for i in todos][0] == "Torre Fria"                         # o atrasado primeiro
    assert {i["nome"] for i in todos} == {"Torre Quente", "Torre Fria", "Painel"}
    assert todos[0]["numero_os"] == t.numero_os and todos[0]["cliente"] == "Dona Marta"
    assert [i["nome"] for i in lista(atrasados=True)] == ["Torre Fria"]
    assert {i["nome"] for i in lista(situacao="A_PEDIR")} == {"Torre Quente", "Painel"}
    assert {i["nome"] for i in lista(central_id=madeiranit)} == {"Torre Quente", "Torre Fria"}
    r = api.client.get(f"{URL_MARCENARIA}/terceirizados", params={"situacao": "XYZ"}, headers=api.header)
    assert r.status_code == 422


def test_permissao_de_os_e_capacidade(obra, como, mudar_segmento):
    t, _ids, _m = obra
    como(view_orcamentos_marcenaria=True)
    assert t.req("GET").status_code == 403
    como(servico=True)
    assert t.req("GET").status_code == 200
    mudar_segmento("serigrafia")
    r = t.req("GET")
    assert r.status_code == 404
