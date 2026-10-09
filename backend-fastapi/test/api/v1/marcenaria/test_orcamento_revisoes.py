# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/marcenaria/test_orcamento_revisoes.py
# DESCRICAO: Orcamento de marcenaria, pedidos das Revisoes 1, 2 e 3 da
#            Spec 06A (casos 34 a 51): erros com `codigo`, simulacao,
#            projetos, contagens, D24a, D31, contato na proposta, eventos de
#            envio, RT padrao e valor previsto por arquiteto.
# ---------------------------------------------------------------------------

import pytest

from app.db.models.configuracao_marcenaria import ConfiguracaoMarcenaria
from app.db.models.marcenaria import MarcenariaMovel, MarcenariaOrcamento
from app.db.models.objeto_servico import ObjetoServico

from test.apoio_orcamento_marcenaria import montar_cenario_b

GERIR = {"manage_orcamentos_marcenaria": True}           # cargo: orcamentos sim, custos nao


@pytest.fixture
def cenario(api, produto, fornecedor, cliente_id) -> dict:
    return montar_cenario_b(api, produto, fornecedor, cliente=cliente_id)


def _master(api):
    """Volta ao token do master (tira o usuario simulado pelo `como`)."""
    from app.core.depends import get_current_active_user
    from app.main import app
    app.dependency_overrides.pop(get_current_active_user, None)


# =========================
# Revisao 1: erros com codigo (34, 35)
# =========================

def test_34_revisao_antiga_tem_codigo(api):
    orc = api.criar()
    api.ok("PATCH", f"/{orc['id']}", rev=1, json={"projeto_nome": "Cozinha"})

    r = api.req("PATCH", f"/{orc['id']}", rev=1, json={"projeto_nome": "x"})

    assert r.status_code == 409
    assert r.json()["detail"]["codigo"] == "REVISAO_DESATUALIZADA"


def test_35_desconto_maior_que_o_bruto_aponta_o_campo(api, cenario):
    r = api.req("PATCH", f"/{cenario['id']}", rev=cenario["revisao"],
                json={"desconto": {"modo": "VALOR", "valor": 972516}})     # bruto + 1 centavo

    assert r.status_code == 422
    assert r.json()["detail"] == {
        "codigo": "CALCULO_INVALIDO", "campo": "desconto",
        "mensagem": "O desconto não pode ser maior que o total do orçamento.",
    }
    assert api.detalhe(cenario["id"])["desconto"] == {"modo": "PERCENTUAL", "valor": 500}   # nada gravado


@pytest.mark.parametrize("corpo, campo", [
    ({"sinal": {"modo": "PERCENTUAL", "valor": 10001}}, "sinal"),
    ({"markup_bp": 100001}, "markup"),
    ({"perda_bp": 5001}, "perda"),
    ({"custo_hora_centavos": -1}, "custo_hora"),
])
def test_35b_outros_campos_do_motor(api, cenario, corpo, campo):
    r = api.req("PATCH", f"/{cenario['id']}", rev=cenario["revisao"], json=corpo)

    assert r.status_code == 422
    assert (r.json()["detail"]["codigo"], r.json()["detail"]["campo"]) == ("CALCULO_INVALIDO", campo)


# =========================
# D24a: chave de custo ausente mantem (36)
# =========================

def test_36_sem_view_custos_put_sem_mao_obra_mantem(api, cenario, como):
    torre = cenario["ambientes"][0]["moveis"][0]
    como(**GERIR)

    d = api.ok("PUT", f"/{cenario['id']}/moveis/{torre['id']}", rev=cenario["revisao"], json={
        "nome": "Torre Quente (nova)", "quantidade": 1,
        "tipo_producao": "TERCEIRIZADA", "central_fornecedor_id": torre["central"]["fornecedor_id"],
        "insumos": [{"id": i["id"], "quantidade_milesimos": i["quantidade_milesimos"]} for i in torre["insumos"]],
    })

    assert d["ambientes"][0]["moveis"][0]["nome"] == "Torre Quente (nova)"
    _master(api)
    salvo = api.detalhe(cenario["id"])["ambientes"][0]["moveis"][0]
    assert salvo["mao_obra"] == {"modo": "FIXA", "centavos": 30000, "horas_centesimos": 0}
    assert salvo["terceirizado_centavos"] == 38000
    assert salvo["calculo"]["preco_unit_centavos"] == 422275           # o preco nao mudou


# =========================
# Simular (37, 38)
# =========================

def test_37_simular_insumo_sem_custo_nao_grava(api, cenario, produto, db_session):
    pid = produto("Puxador novo")                                        # sem custo nenhum
    moveis_antes = db_session.query(MarcenariaMovel).count()

    r = api.ok("POST", f"/{cenario['id']}/moveis/simular", json={
        "nome": "Gaveteiro", "insumos": [{"produto_id": pid, "quantidade_milesimos": 2000}],
    })

    assert r["insumos"] == [{"produto_id": pid, "custo_unit_centavos": 0, "custo_origem": "SEM_CUSTO", "sofre_perda": True}]
    assert r["avisos"] == ["INSUMO_SEM_CUSTO"]
    assert "rt_linha_centavos" not in r["calculo"]
    assert db_session.query(MarcenariaMovel).count() == moveis_antes
    assert api.detalhe(cenario["id"])["revisao"] == cenario["revisao"]


def test_38_simular_e_salvar_dao_o_mesmo_preco(api, cenario, produto):
    pid = produto("MDF Branco 15mm", valor_entrada=24000)
    movel = {
        "nome": "Painel TV", "quantidade": 2,
        "mao_obra": {"modo": "HORAS", "centavos": 0, "horas_centesimos": 250},
        "insumos": [{"produto_id": pid, "quantidade_milesimos": 1300}],
    }

    simulado = api.ok("POST", f"/{cenario['id']}/moveis/simular", json=movel)
    amb = cenario["ambientes"][0]["id"]
    d = api.ok("POST", f"/{cenario['id']}/ambientes/{amb}/moveis", rev=cenario["revisao"], esperado=201, json=movel)

    salvo = d["ambientes"][0]["moveis"][-1]["calculo"]
    assert simulado["calculo"]["preco_unit_centavos"] == salvo["preco_unit_centavos"]
    assert simulado["calculo"]["preco_total_centavos"] == salvo["preco_total_centavos"]


def test_38b_simular_sem_view_custos_so_precos(api, cenario, produto, como):
    pid = produto("MDF Branco 15mm", valor_entrada=24000)
    como(**GERIR)

    r = api.ok("POST", f"/{cenario['id']}/moveis/simular", json={
        "nome": "Painel", "insumos": [{"produto_id": pid, "quantidade_milesimos": 1000}],
    })

    assert set(r["calculo"]) == {"preco_unit_centavos", "preco_total_centavos"}
    assert r["insumos"] == [{"produto_id": pid, "sofre_perda": True}]


# =========================
# Projetos e contagens (39, 40)
# =========================

def _objeto(db, cliente_id: int, nome: str, ativo: bool = True, endereco: str | None = None) -> int:
    objeto = ObjetoServico(cliente_id=cliente_id, marca="", modelo=nome, numero_serie=f"PRJ-{nome[:6]}",
                           ativo=ativo, dados_adicionais={"endereco_obra": endereco} if endereco else {})
    db.add(objeto)
    db.commit()
    return objeto.id


def test_39_projetos_so_ativos_do_cliente(api, cliente_id, db_session, loja):
    outro = api.client.post("/api/v1/clientes/cliente_pf", json={
        "nome": "Seu Jorge", "cpf": "11144477735", "tipo": "PF",
    }, headers=loja).json()["id"]
    ativo = _objeto(db_session, cliente_id, "Cozinha apto 302", endereco="Av. das Américas, 4200")
    _objeto(db_session, cliente_id, "Closet antigo", ativo=False)
    _objeto(db_session, outro, "Sala do Jorge")

    r = api.ok("GET", "/projetos", params={"cliente_id": cliente_id})

    assert [(p["objeto_id"], p["nome"], p["endereco_obra"]) for p in r] == [
        (ativo, "Cozinha apto 302", "Av. das Américas, 4200"),
    ]
    assert r[0]["identificador"] == "PRJ-Cozinh" and len(r[0]["ultimo_uso"]) == 10


def test_39b_escolher_o_projeto_traz_nome_e_endereco(api, cliente_id, db_session):
    objeto = _objeto(db_session, cliente_id, "Cozinha apto 302", endereco="Av. das Américas, 4200")
    orc = api.criar(cliente_id=cliente_id)

    d = api.ok("PATCH", f"/{orc['id']}", rev=orc["revisao"], json={"objeto_id": objeto})

    assert d["projeto"] == {"objeto_id": objeto, "nome": "Cozinha apto 302", "endereco_obra": "Av. das Américas, 4200"}


def test_40_contagens_so_a_versao_mais_recente(api, cenario):
    d = api.ok("POST", f"/{cenario['id']}/enviar", rev=cenario["revisao"])
    v2 = api.ok("POST", f"/{d['id']}/nova-versao", rev=d["revisao"], esperado=201)
    api.ok("POST", f"/{v2['id']}/enviar", rev=v2["revisao"])
    api.criar()                                                          # mais um rascunho

    r = api.ok("GET", "/contagens")

    assert r == {"RASCUNHO": 1, "ENVIADO": 1, "VENCIDO": 0, "RECUSADO": 0, "APROVADO": 0,
                 "vence_em_3_dias": 0, "total": 2}


# =========================
# D31: anexos fora do rascunho (41)
# =========================

PDF = b"%PDF-1.4\n%%EOF\n"


def test_41_anexo_num_enviado_sem_somar_revisao(api, cenario, tmp_path, monkeypatch):
    from app.core import imagem
    monkeypatch.setattr(imagem, "BASE_DIR", str(tmp_path))
    d = api.ok("POST", f"/{cenario['id']}/enviar", rev=cenario["revisao"])

    r = api.req("POST", f"/{d['id']}/anexos", files={"arquivo": ("planta.pdf", PDF, "application/pdf")})
    assert r.status_code == 201, r.text
    anexo = r.json()
    r = api.req("PATCH", f"/{d['id']}/anexos/{anexo['id']}", json={"legenda": "Planta baixa"})
    assert r.status_code == 200 and r.json()["legenda"] == "Planta baixa"
    assert api.detalhe(d["id"])["revisao"] == d["revisao"]               # D31

    v2 = api.ok("POST", f"/{d['id']}/nova-versao", rev=d["revisao"], esperado=201)
    assert v2["id"] != d["id"]
    r = api.req("PATCH", f"/{d['id']}/anexos/{anexo['id']}", json={"legenda": "x"})   # v1 agora SUBSTITUIDO
    assert r.status_code == 409
    assert api.req("POST", f"/{d['id']}/anexos",
                   files={"arquivo": ("b.pdf", PDF, "application/pdf")}).status_code == 409


# =========================
# Vendedor padrao (42)
# =========================

def test_42_vendedor_padrao_e_o_funcionario_do_usuario(api, token_master, como):
    como(funcionario_id=token_master["funcionario_id"], **GERIR)

    d = api.criar()

    assert d["vendedor"]["id"] == token_master["funcionario_id"]
    assert d["vendedor"]["nome"] == "Admin Master"


# =========================
# Revisao 2: contato e eventos de envio (43, 44)
# =========================

def test_43_contato_sai_mesmo_sem_view_custos(api, cenario, como, db_session):
    from app.db.models.funcionario import Funcionario
    vendedor = db_session.get(Funcionario, cenario["vendedor"]["id"])
    vendedor.celular = "85988887777"
    db_session.commit()
    como(view_orcamentos_marcenaria=True)

    d = api.detalhe(cenario["id"])

    assert d["cliente"]["telefone"] == "11987654321"
    assert d["cliente"]["email"] == "marta@example.com"
    assert d["cliente"]["endereco"] == "Rua das Flores, 100 - Centro, Campinas - SP, CEP 13010-000"
    assert d["vendedor"]["telefone"] == "85988887777"


def test_44_dois_envios_dois_eventos_com_o_total_de_cada_um(api, cenario):
    d = api.ok("POST", f"/{cenario['id']}/enviar", rev=cenario["revisao"])
    primeiro_total = d["calculo"]["total_centavos"]
    d = api.ok("POST", f"/{d['id']}/voltar-a-editar", rev=d["revisao"])
    d = api.ok("PATCH", f"/{d['id']}", rev=d["revisao"], json={"desconto": {"modo": "PERCENTUAL", "valor": 1000}})
    d = api.ok("POST", f"/{d['id']}/enviar", rev=d["revisao"])

    envios = [e for e in api.ok("GET", f"/{d['id']}/historico") if e["tipo"] == "ORCAMENTO_ENVIADO"]

    assert [e["dados"]["total_centavos"] for e in envios] == [d["calculo"]["total_centavos"], primeiro_total]
    assert primeiro_total == 923889
    assert envios[1]["descricao"].startswith("Enviado com total de R$ 9.238,89, válido até ")


# =========================
# Revisao 3: RT padrao, arquitetos, previsto e % efetivo (45-51)
# =========================

def test_45_criar_copia_o_rt_padrao(api, db_session):
    api.criar()                                                          # cria a configuracao
    config = db_session.query(ConfiguracaoMarcenaria).first()
    config.rt_padrao_bp = 800
    db_session.commit()

    d = api.criar()

    assert d["parametros"]["rt_padrao_bp"] == 800
    assert db_session.get(MarcenariaOrcamento, d["id"]).rt_padrao_bp == 800


def test_46_sem_view_custos_arquiteto_sem_percentual_recebe_o_padrao(api, fornecedor, como):
    orc = api.criar()
    orc = api.ok("PATCH", f"/{orc['id']}", rev=orc["revisao"], json={"rt_padrao_bp": 800})
    arquiteto = fornecedor("Studio Renascer")
    como(**GERIR)

    api.ok("PUT", f"/{orc['id']}/rt", rev=orc["revisao"], json={"arquitetos": [{"fornecedor_id": arquiteto}]})

    _master(api)
    assert [(a["fornecedor_id"], a["rt_bp"]) for a in api.detalhe(orc["id"])["arquitetos"]] == [(arquiteto, 800)]


def test_47_sem_view_custos_mandar_percentual_e_403(api, fornecedor, como):
    orc = api.criar()
    como(**GERIR)

    r = api.req("PUT", f"/{orc['id']}/rt", rev=orc["revisao"],
                json={"arquitetos": [{"fornecedor_id": fornecedor("Studio"), "rt_bp": 500}]})

    assert r.status_code == 403


def test_48_arquiteto_ja_gravado_mantem_o_percentual(api, fornecedor):
    orc = api.criar()
    arquiteto = fornecedor("Studio Renascer")
    d = api.ok("PUT", f"/{orc['id']}/rt", rev=orc["revisao"],
               json={"arquitetos": [{"fornecedor_id": arquiteto, "rt_bp": 600}]})

    d = api.ok("PUT", f"/{orc['id']}/rt", rev=d["revisao"], json={"arquitetos": [{"fornecedor_id": arquiteto}]})

    assert [a["rt_bp"] for a in d["arquitetos"]] == [600]


def test_48b_arquiteto_inexistente_ou_inativo(api, fornecedor):
    orc = api.criar()
    for fid in (9999, fornecedor("Inativo", ativo=False)):
        r = api.req("PUT", f"/{orc['id']}/rt", rev=orc["revisao"], json={"arquitetos": [{"fornecedor_id": fid}]})
        assert r.status_code == 422 and r.json()["detail"] == "Arquiteto não encontrado."


def test_48c_lista_vazia_remove_o_arquiteto(api, cenario):
    d = api.ok("PUT", f"/{cenario['id']}/rt", rev=cenario["revisao"], json={"arquitetos": []})

    assert d["arquitetos"] == [] and d["calculo"]["rt_total_centavos"] == 0


def test_49_dois_arquitetos_repartem_pelo_maior_resto(api, produto, fornecedor, cliente_id):
    arquitetos = [{"fornecedor_id": fornecedor("Studio A"), "rt_bp": 500},
                  {"fornecedor_id": fornecedor("Studio B"), "rt_bp": 300}]

    d = montar_cenario_b(api, produto, fornecedor, cliente=cliente_id, arquitetos=arquitetos)

    previstos = [a["valor_previsto_centavos"] for a in d["arquitetos"]]
    assert previstos == [46194, 27717] and sum(previstos) == 73911 == d["calculo"]["rt_total_centavos"]


def test_50_percentuais_efetivos_e_custo_do_ambiente(cenario):
    assert (cenario["calculo"]["desconto_bp_efetivo"], cenario["calculo"]["sinal_bp_efetivo"]) == (500, 4000)
    assert cenario["ambientes"][0]["custo_centavos"] == 436850


def test_51_sem_view_custos_sem_rt_mas_com_percentuais_efetivos(api, cenario, como):
    como(**GERIR)

    d = api.detalhe(cenario["id"])

    assert "rt_padrao_bp" not in d["parametros"]
    assert all(set(a) == {"fornecedor_id", "nome"} for a in d["arquitetos"])
    assert (d["calculo"]["desconto_bp_efetivo"], d["calculo"]["sinal_bp_efetivo"]) == (500, 4000)


# =========================
# D20 na corrida: outro computador grava ENTRE a leitura e a gravacao
# =========================

def _outro_computador_grava_no_meio(monkeypatch, modulo):
    """Depois da conferencia da revisao, outro computador soma 1 nela no banco.

    E a janela que a conferencia simples nao ve: as duas escritas leram a
    mesma revisao, e a segunda gravaria por cima da primeira.
    """
    from sqlalchemy import text
    original = modulo.carregar_para_editar

    def _com_corrida(db, orcamento_id, revisao):
        orc = original(db, orcamento_id, revisao)            # conferiu: revisao certa
        db.execute(text("UPDATE marcenaria_orcamentos SET revisao = revisao + 1 WHERE id = :id"),
                   {"id": orcamento_id})                     # ...e o outro computador gravou
        return orc

    monkeypatch.setattr(modulo, "carregar_para_editar", _com_corrida)


def test_d20_corrida_no_cabecalho_responde_409(api, monkeypatch):
    from app.services.marcenaria import orcamento as servico
    orc = api.criar()
    _outro_computador_grava_no_meio(monkeypatch, servico)

    r = api.req("PATCH", f"/{orc['id']}", rev=orc["revisao"], json={"projeto_nome": "Por cima"})

    assert r.status_code == 409, r.text                     # coluna de versao (StaleDataError)
    assert r.json()["detail"]["codigo"] == "REVISAO_DESATUALIZADA"
    monkeypatch.undo()
    assert api.detalhe(orc["id"])["projeto"]["nome"] is None


def test_d20_corrida_so_na_arvore_responde_409(api, monkeypatch):
    from app.services.marcenaria import orcamento_arvore as arvore
    orc = api.criar()
    _outro_computador_grava_no_meio(monkeypatch, arvore)

    r = api.req("POST", f"/{orc['id']}/ambientes", rev=orc["revisao"], json={"nome": "Cozinha"})

    assert r.status_code == 409, r.text                     # conferencia depois da releitura
    assert r.json()["detail"]["codigo"] == "REVISAO_DESATUALIZADA"
    monkeypatch.undo()
    assert api.detalhe(orc["id"])["ambientes"] == []        # nada gravado


def test_d20_corrida_no_excluir_responde_409(api, monkeypatch):
    """Excluir nao passa pelo fecho da escrita: quem segura e a coluna de versao."""
    from sqlalchemy import text
    from app.services.marcenaria import orcamento as servico
    orc = api.criar()
    original = servico.conferir_revisao

    def _com_corrida(o, revisao):
        original(o, revisao)
        from sqlalchemy.orm import object_session
        object_session(o).execute(text("UPDATE marcenaria_orcamentos SET revisao = revisao + 1 WHERE id = :id"),
                                  {"id": o.id})
    monkeypatch.setattr(servico, "conferir_revisao", _com_corrida)

    r = api.req("DELETE", f"/{orc['id']}", rev=orc["revisao"])

    assert r.status_code == 409, r.text
    assert r.json()["detail"]["codigo"] == "REVISAO_DESATUALIZADA"
    monkeypatch.undo()
    assert api.req("GET", f"/{orc['id']}").status_code == 200     # continua la
