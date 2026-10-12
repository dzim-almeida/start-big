# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/marcenaria/test_aprovacao_api.py
# DESCRICAO: Aprovacao do orcamento de marcenaria e geracao da OS
#            (Spec 08A, §12, casos 01-22, 24-27, 31-36 e 40-44).
#
#            O que nao pode errar:
#              - a OS nasce com os MESMOS numeros do motor (bruto e total);
#              - o sinal so entra na OS se foi recebido;
#              - os itens do orcamento ficam travados na OS;
#              - qualquer erro no meio nao deixa OS nem orcamento pela metade;
#              - desfazer cancela a OS pelas regras de sempre (PIN, credito).
# ---------------------------------------------------------------------------

from datetime import timedelta

import pytest

from app.core.tempo import hoje_local
from app.db.models.cliente import Cliente
from app.db.models.estoque import Estoque
from app.db.models.marcenaria import MarcenariaEvento, MarcenariaMovelInsumo, MarcenariaOrcamento
from app.db.models.movimentacao_estoque import MovimentacaoEstoque
from app.db.models.objeto_servico import ObjetoServico
from app.db.models.ordem_servico import OrdemServico
from app.db.models.produto import Produto

from test.apoio_orcamento_marcenaria import aprovar, ids_dos_moveis, montar_cenario_b, os_da_api

GERIR = {"manage_orcamentos_marcenaria": True}           # cargo: orcamentos sim, custos nao
ITENS_URL = "/api/v1/ordens-servico/{numero}/itens"
MSG_TRAVA = "Este item veio do orçamento. Para mudar, desfaça a aprovação ou crie uma nova versão do orçamento."


@pytest.fixture
def cenario(api, produto, fornecedor, cliente_id) -> dict:
    """Cenario B da Spec 05 (Torre terceirizada + 2 Balcoes internos + instalacao)."""
    return montar_cenario_b(api, produto, fornecedor, cliente=cliente_id)


@pytest.fixture
def enviado(api, cenario) -> dict:
    return api.ok("POST", f"/{cenario['id']}/enviar", rev=cenario["revisao"])


def _servicos(os_: dict) -> list[dict]:
    return [i for i in os_["itens"] if i["tipo"] == "SERVICO"]


def _pecas(os_: dict) -> list[dict]:
    return [i for i in os_["itens"] if i["tipo"] == "PRODUTO"]


def _eventos(db, tipo: str) -> list[MarcenariaEvento]:
    return db.query(MarcenariaEvento).filter_by(tipo=tipo).all()


# =========================
# A OS que nasce (01, 02, 06, 34-36)
# =========================

def test_01_aprovar_tudo_com_sinal_recebido(api, enviado, forma_pagamento):
    pix = forma_pagamento("PIX")

    d = aprovar(api, enviado, sinal={"recebido": True, "forma_pagamento_id": pix})

    assert d["status"] == "APROVADO" and d["revisao"] == enviado["revisao"] + 1
    os_ = os_da_api(api, d["os"]["numero_os"])
    assert os_["status"] == "ABERTA"
    assert (os_["valor_bruto"], os_["desconto"], os_["valor_total"]) == (972515, 48626, 923889)
    assert (os_["valor_entrada"], os_["forma_pagamento_entrada"]["id"]) == (369556, pix)
    assert [i["nome"] for i in _servicos(os_)] == [
        "Torre Quente — Cozinha Gourmet", "Balcão — Cozinha Gourmet", "Instalação e montagem",
    ]
    assert os_["funcionario"]["id"] == enviado["vendedor"]["id"]                       # O7
    assert os_["dados_adicionais"]["tipo_trabalho"] == "planejados"
    assert os_["defeito_relatado"].startswith(f"Móveis planejados conforme orçamento {enviado['codigo']} v1")
    assert os_["data_previsao"][:10] == (hoje_local() + timedelta(days=30)).isoformat()
    assert d["aprovacao"]["sinal_recebido_centavos"] == 369556
    assert [m["os_item_id"] is not None for m in d["ambientes"][0]["moveis"]] == [True, True]


def test_02_sinal_nao_recebido_fica_so_combinado(api, enviado, db_session):
    d = aprovar(api, enviado, sinal={"recebido": False})

    assert os_da_api(api, d["os"]["numero_os"])["valor_entrada"] == 0
    orc = db_session.get(MarcenariaOrcamento, d["id"])
    assert (orc.resumo_aprovado_sinal_centavos, orc.sinal_recebido_centavos) == (369556, 0)


def test_06_custo_do_item_e_custo_mais_rt(api, enviado):
    os_ = os_da_api(api, aprovar(api, enviado)["os"]["numero_os"])

    torre, balcao, instalacao = _servicos(os_)
    assert (torre["valor_unitario"], torre["custo_unitario"]) == (422275, 254343)
    assert (balcao["quantidade"], balcao["custo_unitario"]) == (2, 122794)
    assert (instalacao["valor_unitario"], instalacao["custo_unitario"]) == (142500, 85830)


def test_34_35_36_pecas_embutidas_so_dos_internos(api, enviado):
    os_ = os_da_api(api, aprovar(api, enviado)["os"]["numero_os"])

    pecas = {p["nome"]: p for p in _pecas(os_)}
    assert set(pecas) == {"MDF Branco TX 18mm", "Corrediça Tandem"}    # Torre e terceirizada (D1d)
    assert pecas["MDF Branco TX 18mm"]["quantidade"] == 3               # 1,0 x 2 x 1,1 = 2,2 -> 3
    assert pecas["Corrediça Tandem"]["quantidade"] == 6                 # sem perda: 3 x 2
    for p in pecas.values():
        assert (p["valor_unitario"], p["visivel_cliente"], p["origem"], p["status_aprovacao"]) == (
            0, False, "ORCAMENTO_MARCENARIA", "APROVADO",
        )
    assert pecas["Corrediça Tandem"]["unidade_medida"] == "OUTROS"     # "PAR" fora do enum
    assert all(i["origem"] == "ORCAMENTO_MARCENARIA" for i in os_["itens"])
    assert (os_["valor_bruto"], os_["valor_total"]) == (972515, 923889)   # as pecas somam zero


# =========================
# Aprovacao parcial e desconto (03, 04, 05)
# =========================

def test_03_so_a_torre_sem_instalacao(api, enviado, db_session):
    torre = enviado["ambientes"][0]["moveis"][0]["id"]

    d = aprovar(api, enviado, movel_ids=[torre], incluir_instalacao=False)

    os_ = os_da_api(api, d["os"]["numero_os"])
    assert [i["nome"] for i in os_["itens"]] == ["Torre Quente — Cozinha Gourmet"]   # terceirizada: sem pecas
    assert (os_["valor_bruto"], os_["desconto"], os_["valor_total"]) == (422275, 21114, 401161)
    assert [m["aprovado"] for m in d["ambientes"][0]["moveis"]] == [True, False]
    assert d["aprovacao"]["instalacao_aprovada"] is False
    assert d["aprovacao"]["total_centavos"] == 401161
    assert d["calculo"]["total_centavos"] == 923889            # o proposto continua no detalhe


def test_04_desconto_em_reais_maior_que_o_aprovado(api, enviado, db_session):
    torre = enviado["ambientes"][0]["moveis"][0]["id"]

    r = aprovar(api, enviado, movel_ids=[torre], incluir_instalacao=False, esperado=422,
                desconto={"modo": "VALOR", "valor": 500000})

    assert r.json()["detail"]["codigo"] == "CALCULO_INVALIDO" and r.json()["detail"]["campo"] == "desconto"
    assert db_session.query(OrdemServico).count() == 0
    assert api.detalhe(enviado["id"])["status"] == "ENVIADO"


def test_05_desconto_novo_vai_para_o_orcamento_e_o_evento(api, enviado, db_session):
    d = aprovar(api, enviado, desconto={"modo": "PERCENTUAL", "valor": 1000})

    assert d["desconto"] == {"modo": "PERCENTUAL", "valor": 1000}
    (evento,) = _eventos(db_session, "ORCAMENTO_APROVADO")
    assert evento.dados["desconto_centavos"] == 97252             # 10% de 972.515
    assert evento.os_id == d["os"]["id"]


# =========================
# Projeto (07, 08)
# =========================

def test_07_projeto_existente_e_reaproveitado(api, produto, fornecedor, cliente_id, db_session, forma_pagamento):
    objeto = ObjetoServico(cliente_id=cliente_id, marca="", modelo="Apto 802", numero_serie="PRJ-2026-000777",
                           ativo=True, dados_adicionais={})
    db_session.add(objeto)
    db_session.commit()
    d = montar_cenario_b(api, produto, fornecedor, cliente=cliente_id)
    d = api.ok("PATCH", f"/{d['id']}", rev=d["revisao"], json={"objeto_id": objeto.id, "endereco_obra": "Rua Nova, 1"})

    d = aprovar(api, d)

    assert db_session.query(ObjetoServico).count() == 1                      # nenhum objeto novo
    assert os_da_api(api, d["os"]["numero_os"])["objeto"]["id"] == objeto.id
    db_session.expire_all()
    assert db_session.get(ObjetoServico, objeto.id).dados_adicionais["endereco_obra"] == "Rua Nova, 1"


def test_08_projeto_novo_vira_objeto_com_codigo_prj(api, enviado, db_session):
    d = aprovar(api, enviado)

    objeto = db_session.get(ObjetoServico, d["projeto"]["objeto_id"])
    assert objeto.numero_serie.startswith("PRJ-") and objeto.modelo == "Residencial Alpha Ville - Apto 802"


# =========================
# Barreiras (09, 10, 11, 12, 13)
# =========================

def test_09_sem_vendedor(api, enviado):
    d = api.ok("POST", f"/{enviado['id']}/voltar-a-editar", rev=enviado["revisao"])
    d = api.ok("PATCH", f"/{d['id']}", rev=d["revisao"], json={"funcionario_id": None})

    r = aprovar(api, d, esperado=422)

    assert r.json()["detail"] == "Informe o vendedor do orçamento antes de aprovar."


def test_10_movel_sem_preco(api, cenario, db_session):
    amb = cenario["ambientes"][0]["id"]
    d = api.ok("POST", f"/{cenario['id']}/ambientes/{amb}/moveis", rev=cenario["revisao"], esperado=201,
               json={"nome": "Nicho vazio"})                        # sem insumo, sem mao de obra: preco 0

    r = aprovar(api, d, esperado=422)

    assert r.json()["detail"] == "O móvel Nicho vazio está sem preço. Complete o móvel ou deixe-o de fora."
    assert db_session.query(OrdemServico).count() == 0


def test_11_aprovar_de_rascunho_registra_o_envio(api, cenario, db_session):
    d = aprovar(api, cenario)

    assert d["datas"]["envio"] is not None
    assert len(_eventos(db_session, "ORCAMENTO_ENVIADO")) == 1
    assert len(_eventos(db_session, "ORCAMENTO_APROVADO")) == 1


def test_12_aprovar_de_rascunho_sem_cliente(api, produto, fornecedor):
    d = montar_cenario_b(api, produto, fornecedor, cliente=None)

    r = aprovar(api, d, esperado=422)

    assert r.json()["detail"] == "Para aprovar, informe o cliente."


def test_13_falha_no_meio_desfaz_tudo(api, enviado, db_session, monkeypatch):
    from app.services.marcenaria import aprovacao

    def _quebra(*args, **kwargs):
        raise RuntimeError("falha simulada depois de criar a OS")
    monkeypatch.setattr(aprovacao, "registrar_evento", _quebra)

    try:
        r = aprovar(api, enviado, esperado=500)
    except RuntimeError:
        r = None                                     # o TestClient pode repassar a excecao
    assert r is None or r.status_code == 500

    monkeypatch.undo()
    db_session.expire_all()
    assert db_session.query(OrdemServico).count() == 0
    detalhe = api.detalhe(enviado["id"])
    assert detalhe["status"] == "ENVIADO" and detalhe["revisao"] == enviado["revisao"]
    assert all(m["aprovado"] is None for m in detalhe["ambientes"][0]["moveis"])


# =========================
# Trava dos itens na OS (14, 15, 30, 42)
# =========================

def test_14_30_42_item_do_orcamento_nao_se_edita_pela_os(api, enviado):
    numero = aprovar(api, enviado)["os"]["numero_os"]
    os_ = os_da_api(api, numero)
    torre, peca = _servicos(os_)[0], _pecas(os_)[0]

    for item in (torre, peca):
        r = api.client.put(f"{ITENS_URL.format(numero=numero)}/{item['id']}", json={"quantidade": 5}, headers=api.header)
        assert r.status_code == 409 and r.json()["detail"] == MSG_TRAVA
        r = api.client.delete(f"{ITENS_URL.format(numero=numero)}/{item['id']}", headers=api.header)
        assert r.status_code == 409 and r.json()["detail"] == MSG_TRAVA


def test_15_item_manual_na_mesma_os_continua_livre(api, enviado):
    numero = aprovar(api, enviado)["os"]["numero_os"]
    r = api.client.post(ITENS_URL.format(numero=numero), json={
        "tipo": "SERVICO", "nome": "Frete extra", "unidade_medida": "UN", "quantidade": 1, "valor_unitario": 5000,
        "origem": "ORCAMENTO_MARCENARIA",                 # 29: o campo e ignorado na criacao
    }, headers=api.header)
    assert r.status_code in (200, 201), r.text
    manual = next(i for i in r.json()["itens"] if i["nome"] == "Frete extra")
    assert manual["origem"] is None

    r = api.client.put(f"{ITENS_URL.format(numero=numero)}/{manual['id']}", json={"valor_unitario": 6000}, headers=api.header)
    assert r.status_code == 200, r.text
    assert api.client.delete(f"{ITENS_URL.format(numero=numero)}/{manual['id']}", headers=api.header).status_code == 204


# =========================
# Desfazer (16-22, 44)
# =========================

def _desfazer(api, d, esperado=200, **corpo):
    corpo = {"motivo": "Aprovado no orçamento errado", **corpo}
    r = api.req("POST", f"/{d['id']}/desfazer-aprovacao", rev=d["revisao"], json=corpo)
    assert r.status_code == esperado, r.text
    return r.json()


def test_16_desfazer_com_sinal_vira_credito(api, enviado, forma_pagamento, db_session, cliente_id):
    d = aprovar(api, enviado, sinal={"recebido": True, "forma_pagamento_id": forma_pagamento("PIX")})
    numero = d["os"]["numero_os"]

    d = _desfazer(api, d, destino_sinal="CREDITO")

    assert d["status"] == "ENVIADO" and d["os"] is None and d["aprovacao"] is None
    assert all(m["aprovado"] is None and m["os_item_id"] is None for m in d["ambientes"][0]["moveis"])
    assert os_da_api(api, numero)["status"] == "CANCELADA"
    db_session.expire_all()
    assert db_session.get(Cliente, cliente_id).saldo_credito == 369556
    assert len(_eventos(db_session, "APROVACAO_DESFEITA")) == 1


def test_17_desfazer_com_sinal_devolvido(api, enviado, forma_pagamento, db_session, cliente_id):
    d = aprovar(api, enviado, sinal={"recebido": True, "forma_pagamento_id": forma_pagamento("PIX")})
    numero = d["os"]["numero_os"]

    _desfazer(api, d, destino_sinal="DEVOLVIDO")

    assert os_da_api(api, numero)["valor_entrada"] == 0
    db_session.expire_all()
    assert (db_session.get(Cliente, cliente_id).saldo_credito or 0) == 0


def test_18_desfazer_com_os_em_andamento_e_bloqueado(api, enviado, db_session):
    d = aprovar(api, enviado)
    os_ = db_session.get(OrdemServico, d["os"]["id"])
    os_.status = "EM_ANDAMENTO"
    db_session.commit()

    corpo = _desfazer(api, api.detalhe(d["id"]), esperado=409)

    assert corpo["detail"]["codigo"] == "DESFAZER_BLOQUEADO"
    assert corpo["detail"]["motivos"] == ["A OS já não está aberta (status: Em Produção)."]
    assert api.detalhe(d["id"])["acoes"]["desfazer_aprovacao"] is False


def test_19_desfazer_pede_o_pin_quando_a_loja_exige(api, enviado, db_session):
    from app.core.security import hash_password
    from app.db.models.configuracao_seguranca import ConfiguracaoSeguranca
    d = aprovar(api, enviado)
    db_session.add(ConfiguracaoSeguranca(empresa_id=1, pin_gerente=hash_password("1234"), requer_pin_cancelar_os=True))
    db_session.commit()

    corpo = _desfazer(api, d, esperado=400)
    assert corpo["detail"] == "REQUER_APROVACAO_GERENTE"
    assert api.detalhe(d["id"])["status"] == "APROVADO"                  # nada mudou

    d = _desfazer(api, d, codigo_gerente="1234")
    assert d["status"] == "ENVIADO"


def test_20_desfazer_depois_da_validade_fica_vencido(api, enviado, db_session):
    d = aprovar(api, enviado)
    orc = db_session.get(MarcenariaOrcamento, d["id"])
    orc.data_validade = hoje_local() - timedelta(days=1)
    db_session.commit()

    d = _desfazer(api, api.detalhe(d["id"]))

    assert d["status"] == "VENCIDO"


def test_21_reaprovar_usando_o_credito(api, enviado, forma_pagamento, db_session, cliente_id):
    d = aprovar(api, enviado, sinal={"recebido": True, "forma_pagamento_id": forma_pagamento("PIX")})
    d = _desfazer(api, d)                                               # sinal vira credito
    assert d["acoes"]["aprovar"] is True

    d = aprovar(api, d, sinal={"recebido": True, "usar_credito_cliente": True})

    os_ = os_da_api(api, d["os"]["numero_os"])
    assert os_["valor_entrada"] == 369556 and os_["status"] == "ABERTA"
    db_session.expire_all()
    assert db_session.get(Cliente, cliente_id).saldo_credito == 0


def test_22_os_cancelada_pela_tela_de_os(api, enviado):
    d = aprovar(api, enviado)
    r = api.client.put(f"/api/v1/ordens-servico/{d['os']['numero_os']}/cancelar",
                       json={"motivo": "Cliente desistiu na produção"}, headers=api.header)
    assert r.status_code == 200, r.text

    d = api.detalhe(d["id"])

    assert d["status"] == "APROVADO" and d["os"]["status"] == "CANCELADA"
    assert d["acoes"]["nova_versao"] is True
    v2 = api.ok("POST", f"/{d['id']}/nova-versao", rev=d["revisao"], esperado=201)
    assert (v2["status"], v2["versao"]) == ("RASCUNHO", 2)


def test_44_desfazer_sem_retirada_nao_mexe_no_estoque(api, enviado, db_session):
    d = aprovar(api, enviado)

    _desfazer(api, d)

    assert db_session.query(MovimentacaoEstoque).count() == 0


# =========================
# API: recorte, trava, versoes, segmento (24-27)
# =========================

def test_24_simular_sem_view_custos(api, enviado, como):
    como(**GERIR)

    r = api.ok("POST", f"/{enviado['id']}/aprovacao/simular", json={"movel_ids": ids_dos_moveis(enviado)})

    assert not {"custo_total_centavos", "rt_total_centavos", "margem_liquida_centavos", "margem_liquida_bp"} & set(r)
    assert (r["total_centavos"], r["sinal_centavos"], r["saldo_centavos"]) == (923889, 369556, 554333)
    assert r["previsao_entrega"] == (hoje_local() + timedelta(days=30)).isoformat()


def test_24b_simular_nao_grava(api, enviado, db_session):
    api.ok("POST", f"/{enviado['id']}/aprovacao/simular", json={"movel_ids": ids_dos_moveis(enviado)[:1]})

    d = api.detalhe(enviado["id"])
    assert d["revisao"] == enviado["revisao"] and all(m["aprovado"] is None for m in d["ambientes"][0]["moveis"])
    assert db_session.query(OrdemServico).count() == 0


def test_25_aprovar_com_revisao_antiga(api, enviado):
    r = api.req("POST", f"/{enviado['id']}/aprovar", rev=enviado["revisao"] - 1,
                json={"movel_ids": ids_dos_moveis(enviado)})

    assert r.status_code == 409 and r.json()["detail"]["codigo"] == "REVISAO_DESATUALIZADA"


def test_26_aprovar_versao_substituida(api, enviado):
    api.ok("POST", f"/{enviado['id']}/nova-versao", rev=enviado["revisao"], esperado=201)
    v1 = api.detalhe(enviado["id"])

    r = aprovar(api, v1, esperado=409)

    assert r.json()["detail"]["codigo"] == "TRANSICAO_INVALIDA"


def test_26b_escolher_movel_de_outro_orcamento(api, enviado):
    r = aprovar(api, enviado, movel_ids=[99999], esperado=422)
    assert r.json()["detail"] == "Móvel não encontrado neste orçamento."
    r = aprovar(api, enviado, movel_ids=[], esperado=422)
    assert r.json()["detail"][0]["message"] == "Escolha pelo menos um móvel."


def test_26c_sinal_recebido_sem_forma_ou_maior_que_o_total(api, enviado):
    r = aprovar(api, enviado, esperado=422, sinal={"recebido": True})
    assert r.json()["detail"] == "Informe a forma de pagamento do sinal."
    r = aprovar(api, enviado, esperado=422, sinal={"recebido": True, "valor_centavos": 923890, "forma_pagamento_id": 1})
    assert r.json()["detail"] == "O sinal não pode ser maior que o total aprovado."


def test_27_fora_da_marcenaria(api, enviado, mudar_segmento):
    mudar_segmento("serigrafia")

    assert aprovar(api, enviado, esperado=404).status_code == 404
    assert api.req("POST", f"/{enviado['id']}/aprovacao/simular", json={"movel_ids": [1]}).status_code == 404


# =========================
# Resumo pela OS (31, 32, 33) e lista
# =========================

def test_31_por_os_com_permissao_so_de_os(api, enviado, como):
    numero = aprovar(api, enviado)["os"]["numero_os"]
    como(servico=True)                                     # so a permissao de OS

    r = api.ok("GET", f"/por-os/{numero}")

    assert r["codigo"] == enviado["codigo"] and r["total_aprovado_centavos"] == 923889
    assert [m["nome"] for m in r["moveis"]] == ["Torre Quente", "Balcão"]
    assert r["aprovado_por"] == "Admin Master" and r["pode_desfazer"] is True
    texto = str(r)
    assert "custo" not in texto and "margem" not in texto and "rt_" not in texto


def test_32_por_os_de_uma_os_sem_orcamento(api, enviado):
    assert api.req("GET", "/por-os/OS-2026-999999").status_code == 404


def test_33_por_os_le_o_sinal_lancado_depois_na_os(api, enviado, forma_pagamento):
    numero = aprovar(api, enviado)["os"]["numero_os"]
    pix = forma_pagamento("PIX")
    r = api.client.put(f"/api/v1/ordens-servico/{numero}", json={"valor_entrada": 100000,
                                                                 "forma_pagamento_entrada_id": pix}, headers=api.header)
    assert r.status_code == 200, r.text

    assert api.ok("GET", f"/por-os/{numero}")["sinal_recebido_centavos"] == 100000


def test_lista_mostra_o_total_aprovado_e_a_os(api, enviado):
    torre = enviado["ambientes"][0]["moveis"][0]["id"]
    d = aprovar(api, enviado, movel_ids=[torre], incluir_instalacao=False)

    (item,) = api.ok("GET", "/")["items"]

    assert (item["status"], item["resumo_total_centavos"], item["os_numero"]) == ("APROVADO", 401161, d["os"]["numero_os"])
    assert api.ok("GET", "/contagens")["APROVADO"] == 1


def test_aprovado_e_so_leitura(api, enviado):
    d = aprovar(api, enviado)

    r = api.req("PATCH", f"/{d['id']}", rev=d["revisao"], json={"projeto_nome": "x"})

    assert r.status_code == 409 and r.json()["detail"]["codigo"] == "STATUS_NAO_EDITAVEL"
    assert {k for k, v in d["acoes"].items() if v} == {"desfazer_aprovacao"}


# =========================
# Insumos (40, 41, 43)
# =========================

def test_40_insumo_de_produto_excluido_nao_vira_item(api, enviado, db_session):
    insumo = db_session.query(MarcenariaMovelInsumo).filter_by(descricao="Corrediça Tandem").all()
    for i in insumo:
        i.produto_id = None                                 # o produto sumiu do cadastro
    db_session.commit()

    os_ = os_da_api(api, aprovar(api, enviado)["os"]["numero_os"])

    assert [p["nome"] for p in _pecas(os_)] == ["MDF Branco TX 18mm"]


def test_41_compras_enxerga_a_peca_embutida(api, enviado, db_session):
    from app.services.compras.demanda_os import demandas_por_produto
    d = aprovar(api, enviado)
    mdf = db_session.query(Produto).filter_by(nome="MDF Branco TX 18mm").first()

    demandas = demandas_por_produto(db_session, [mdf.id])[mdf.id]

    assert [(x.numero_os, x.quantidade, x.pode_comprar) for x in demandas] == [(d["os"]["numero_os"], 3, True)]


def test_43_finalizar_sem_separar_baixa_as_pecas(api, enviado, forma_pagamento, db_session):
    pix = forma_pagamento("PIX")
    numero = aprovar(api, enviado)["os"]["numero_os"]
    mdf = db_session.query(Produto).filter_by(nome="MDF Branco TX 18mm").first()
    antes = db_session.get(Estoque, mdf.id).quantidade

    r = api.client.put(f"/api/v1/ordens-servico/{numero}/finalizar", json={
        "situacao_equipamento": "REPARADO",
        "pagamentos": [{"forma_pagamento_id": pix, "valor": 923889}],
    }, headers=api.header)
    assert r.status_code == 200, r.text

    db_session.expire_all()
    assert db_session.get(Estoque, mdf.id).quantidade == antes - 3
