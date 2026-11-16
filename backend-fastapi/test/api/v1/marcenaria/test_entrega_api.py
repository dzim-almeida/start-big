# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/marcenaria/test_entrega_api.py
# DESCRICAO: Entrega e instalacao da OS da marcenaria pela API (Spec 13A,
#            secao 11, casos 01-24).
#
#            O que nao pode errar:
#              - a aprovacao cria uma entrega por ambiente aprovado (copia do checklist);
#              - "com ressalvas" exige pendencia; corrigir grava evento;
#              - a foto e da OS (galeria) e excluir pela entrega tira da galeria;
#              - a OS guarda a menor data de instalacao ainda pendente (o Compras le);
#              - desfazer bloqueado com entrega registrada; nenhum preco.
# ---------------------------------------------------------------------------

import io
from datetime import date, datetime, timedelta

import pytest
from PIL import Image

from app.core.enum import OrdemServicoStatus
from app.db.models.configuracao_marcenaria import CHECKLIST_PADRAO, ConfiguracaoMarcenaria
from app.db.models.empresa import Empresa
from app.db.models.funcionario import Funcionario
from app.db.models.marcenaria import MarcenariaEvento
from app.db.models.marcenaria.entrega import MarcenariaAgendamento, MarcenariaEntrega
from app.db.models.ordem_servico import OrdemServico
from app.services.compras import demanda_os

from test.apoio_orcamento_marcenaria import URL_MARCENARIA, aprovar, ids_dos_moveis, os_da_api

HOJE = date.today()
AMANHA = HOJE + timedelta(days=1)
ONTEM = HOJE - timedelta(days=1)


# =========================
# Ajudantes
# =========================

class Entrega:
    """Atalho para a API da entrega de uma OS."""

    def __init__(self, api, numero_os: str):
        self.api, self.numero_os = api, numero_os

    def req(self, metodo: str, caminho: str = "", **kwargs):
        return self.api.client.request(metodo, f"{URL_MARCENARIA}/os/{self.numero_os}{caminho}",
                                       headers=self.api.header, **kwargs)

    def ler(self) -> dict:
        r = self.req("GET", "/entrega")
        assert r.status_code == 200, r.text
        return r.json()

    def escrever(self, metodo: str, caminho: str, json: dict = None, esperado: int = 200, **kwargs):
        r = self.req(metodo, caminho, json=json, **kwargs)
        assert r.status_code == esperado, r.text
        return r.json()

    def entrega(self, ambiente: str, dados: dict = None) -> dict:
        return next(e for e in (dados or self.ler())["entregas"] if e["ambiente"] == ambiente)

    def registrar(self, ambiente: str, esperado: int = 200, **corpo) -> dict:
        entrega = self.entrega(ambiente)
        return self.escrever("POST", f"/entrega/{entrega['id']}/registrar",
                             {"situacao": "CONFORME", **corpo}, esperado=esperado)

    def agendar(self, ambientes: list[str], montadores: list[int], data: date = AMANHA, esperado: int = 200,
                **extra) -> dict:
        dados = self.ler()
        ids = [self.entrega(nome, dados)["ambiente_id"] for nome in ambientes]
        return self.escrever("POST", "/agendamentos",
                             {"data": data.isoformat(), "ambiente_ids": ids, "montadores": montadores, **extra},
                             esperado=esperado)

    def foto(self, ambiente: str, tipo: str = "TERMO", esperado: int = 200) -> dict:
        entrega = self.entrega(ambiente)
        r = self.req("POST", f"/entrega/{entrega['id']}/fotos", data={"tipo": tipo},
                     files={"arquivo": ("termo.png", _png(), "image/png")})
        assert r.status_code == esperado, r.text
        return r.json()


def _png() -> bytes:
    """Uma imagem de verdade (o pipeline da OS valida e converte)."""
    saida = io.BytesIO()
    Image.new("RGB", (40, 30), "white").save(saida, format="PNG")
    return saida.getvalue()


def _movel(nome: str) -> dict:
    return {"nome": nome, "quantidade": 1, "largura_mm": 700, "altura_mm": 2200, "profundidade_mm": 600,
            "mao_obra": {"modo": "FIXA", "centavos": 10000, "horas_centesimos": 0}, "insumos": []}


def _aprovar_obra(api, cliente_id: int, ambientes=("Cozinha Gourmet", "Closet"), recusado: str = "Varanda",
                  insumos: list = None) -> tuple[dict, str]:
    """Um orcamento com os ambientes dados (um movel cada) e um ambiente cujo movel
    fica FORA da aprovacao. Devolve (detalhe aprovado, numero da OS)."""
    orc = api.criar(cliente_id=cliente_id, projeto_nome="Apto 802", endereco_obra="Av. das Américas, 4200")
    d = orc
    for nome in (*ambientes, recusado):
        d = api.ok("POST", f"/{orc['id']}/ambientes", rev=d["revisao"], esperado=201, json={"nome": nome})
        amb = next(a for a in d["ambientes"] if a["nome"] == nome)["id"]
        movel = {**_movel(f"Móvel de {nome}"), "insumos": insumos or []}
        d = api.ok("POST", f"/{orc['id']}/ambientes/{amb}/moveis", rev=d["revisao"], esperado=201, json=movel)
    fora = next(m["id"] for a in d["ambientes"] if a["nome"] == recusado for m in a["moveis"])
    d = aprovar(api, d, movel_ids=[i for i in ids_dos_moveis(d) if i != fora])
    return d, d["os"]["numero_os"]


@pytest.fixture(autouse=True)
def _fotos_numa_pasta_temporaria(tmp_path, monkeypatch):
    """As fotos dos testes vao para uma pasta descartavel, nunca para a pasta de dados da maquina."""
    monkeypatch.setattr("app.core.imagem.BASE_DIR", str(tmp_path))


@pytest.fixture
def obra(api, cliente_id) -> Entrega:
    _d, numero = _aprovar_obra(api, cliente_id)
    return Entrega(api, numero)


@pytest.fixture
def montadores(db_session) -> dict[str, int]:
    """Carlos e Davi, funcionarios ativos; Edu, que saiu da empresa."""
    empresa = db_session.query(Empresa).first()
    pessoas = {nome: Funcionario(empresa_id=empresa.id, nome=nome, ativo=(nome != "Edu"))
               for nome in ("Carlos", "Davi", "Edu")}
    db_session.add_all(pessoas.values())
    db_session.commit()
    return {nome: f.id for nome, f in pessoas.items()}


def _status_da_os(db, numero: str, status: OrdemServicoStatus) -> None:
    db.query(OrdemServico).filter_by(numero_os=numero).one().status = status
    db.commit()


def _data_instalacao(db, numero: str):
    db.expire_all()
    return db.query(OrdemServico).filter_by(numero_os=numero).one().data_instalacao


def _eventos(db, tipo: str) -> list[MarcenariaEvento]:
    db.expire_all()
    return db.query(MarcenariaEvento).filter_by(tipo=tipo).all()


# =========================
# Entregas na aprovacao (01-02)
# =========================

def test_01_aprovar_cria_uma_entrega_por_ambiente_aprovado(obra):
    dados = obra.ler()
    assert [e["ambiente"] for e in dados["entregas"]] == ["Cozinha Gourmet", "Closet"]   # Varanda ficou fora
    cozinha = dados["entregas"][0]
    assert cozinha["situacao"] == "PENDENTE"
    assert [i["texto"] for i in cozinha["checklist"]] == CHECKLIST_PADRAO
    assert {i["marcacao"] for i in cozinha["checklist"]} == {None}
    assert cozinha["moveis"] == [{"nome": "Móvel de Cozinha Gourmet", "quantidade": 1,
                                  "medidas": {"largura_mm": 700, "altura_mm": 2200, "profundidade_mm": 600}}]
    assert dados["projeto"]["codigo"].startswith("PRJ-")
    assert (dados["projeto"]["nome"], dados["projeto"]["endereco_obra"]) == ("Apto 802", "Av. das Américas, 4200")
    assert dados["cliente"] == {"nome": "Dona Marta", "telefone": "11987654321"}
    assert dados["resumo"] == {"entregues": 0, "total": 2, "todos_entregues": False,
                               "ambientes_pendentes": ["Cozinha Gourmet", "Closet"], "pendencias_abertas": []}
    # Nenhum preco em lugar nenhum (P4).
    texto = str(dados).lower()
    assert not any(p in texto for p in ("custo", "preco", "valor", "margem", "centavos"))


def test_02_mudar_o_checklist_da_configuracao_nao_mexe_na_os(obra, db_session):
    db_session.query(ConfiguracaoMarcenaria).one().checklist_vistoria = ["Só isto"]
    db_session.commit()
    assert [i["texto"] for i in obra.entrega("Closet")["checklist"]] == CHECKLIST_PADRAO


def test_checklist_editavel_enquanto_pendente_com_as_regras_da_04a(obra, montadores):
    closet = obra.entrega("Closet")
    dados = obra.escrever("PUT", f"/entrega/{closet['id']}/checklist", {"itens": ["  Espelho fixado ", "Portas"]})
    assert [i["texto"] for i in obra.entrega("Closet", dados)["checklist"]] == ["Espelho fixado", "Portas"]
    r = obra.escrever("PUT", f"/entrega/{closet['id']}/checklist", {"itens": ["Portas", "portas"]}, esperado=422)
    assert r["detail"] == "Checklist: há itens repetidos."
    obra.registrar("Closet", montadores=[montadores["Carlos"]])
    r = obra.escrever("PUT", f"/entrega/{closet['id']}/checklist", {"itens": ["X"]}, esperado=409)
    assert r["detail"]["mensagem"] == "O checklist só muda enquanto a entrega está pendente."


# =========================
# Agendamento (03-05, 16-17, 19-22)
# =========================

def test_03_agendar_a_cozinha_com_carlos_e_davi(obra, montadores, db_session):
    dados = obra.agendar(["Cozinha Gourmet"], [montadores["Carlos"], montadores["Davi"]], hora_inicio="08:00")
    (agendamento,) = dados["agendamentos"]
    assert agendamento["ambientes"] == ["Cozinha Gourmet"]
    assert [m["nome"] for m in agendamento["montadores"]] == ["Carlos", "Davi"]
    assert (agendamento["hora_inicio"], agendamento["atrasado"], agendamento["editavel"]) == ("08:00", False, True)
    assert dados["avisos"] == []
    assert obra.entrega("Cozinha Gourmet", dados)["agendamento"]["id"] == agendamento["id"]
    assert obra.entrega("Closet", dados)["agendamento"] is None
    assert len(_eventos(db_session, "AGENDAMENTO_CRIADO")) == 1


def test_04_montador_em_outra_os_no_mesmo_dia_e_aceito_com_aviso(api, cliente_id, obra, montadores):
    obra.agendar(["Cozinha Gourmet"], [montadores["Carlos"]], hora_inicio="08:00")
    _d, outra = _aprovar_obra(api, cliente_id, ambientes=("Sala",), recusado="Lavanderia")
    dados = Entrega(api, outra).agendar(["Sala"], [montadores["Carlos"], montadores["Davi"]])
    (aviso,) = dados["avisos"]
    assert aviso["codigo"] == "MONTADOR_OCUPADO"
    assert aviso["mensagem"] == (f"Carlos já tem instalação em {AMANHA:%d/%m} às 08:00 "
                                 f"na {obra.numero_os} (Dona Marta).")
    assert len(dados["agendamentos"]) == 1                               # salvo mesmo assim


def test_05_agendar_ambiente_ja_entregue_e_422(obra, montadores):
    obra.registrar("Closet", montadores=[montadores["Carlos"]])
    r = obra.agendar(["Closet"], [montadores["Carlos"]], esperado=422)
    assert r["detail"] == "O ambiente Closet já foi entregue."


def test_agendar_sem_ambiente_ou_montador_e_montador_inativo(obra, montadores):
    r = obra.agendar([], [montadores["Carlos"]], esperado=422)
    assert r["detail"] == "Escolha pelo menos um ambiente e um montador."
    r = obra.agendar(["Closet"], [montadores["Edu"]], esperado=422)
    assert r["detail"] == "Funcionário não encontrado ou inativo."
    r = obra.agendar(["Closet"], [montadores["Carlos"]], hora_inicio="25:00", esperado=422)
    assert "08:00" in str(r["detail"])


def test_16_agendamento_de_ontem_sem_registro_esta_atrasado(api, obra, montadores):
    obra.agendar(["Closet"], [montadores["Carlos"]], data=ONTEM)
    assert obra.ler()["agendamentos"][0]["atrasado"] is True
    r = api.client.get(f"{URL_MARCENARIA}/instalacoes", params={"atrasadas": "true"}, headers=api.header)
    assert [i["numero_os"] for i in r.json()["itens"]] == [obra.numero_os]
    obra.registrar("Closet", montadores=[montadores["Carlos"]])
    r = api.client.get(f"{URL_MARCENARIA}/instalacoes", params={"atrasadas": "true"}, headers=api.header)
    assert r.json()["itens"] == []                                      # registrado: nao esta mais atrasado


def test_17_agendamento_com_entrega_registrada_vira_historico(obra, montadores):
    dados = obra.agendar(["Closet"], [montadores["Carlos"]])
    aid = dados["agendamentos"][0]["id"]
    obra.registrar("Closet", montadores=[montadores["Carlos"]])
    assert obra.ler()["agendamentos"][0]["editavel"] is False
    corpo = {"data": AMANHA.isoformat(), "ambiente_ids": dados["agendamentos"][0]["ambiente_ids"],
             "montadores": [montadores["Davi"]]}
    r = obra.escrever("PUT", f"/agendamentos/{aid}", corpo, esperado=409)
    assert r["detail"]["mensagem"] == "Este agendamento já tem entrega registrada e não pode mais ser alterado."
    obra.escrever("DELETE", f"/agendamentos/{aid}", esperado=409)


def test_editar_e_excluir_agendamento_pendente(obra, montadores, db_session):
    dados = obra.agendar(["Closet"], [montadores["Carlos"]])
    aid = dados["agendamentos"][0]["id"]
    corpo = {"data": (AMANHA + timedelta(days=2)).isoformat(), "hora_inicio": "13:30",
             "ambiente_ids": dados["agendamentos"][0]["ambiente_ids"], "montadores": [montadores["Davi"]]}
    dados = obra.escrever("PUT", f"/agendamentos/{aid}", corpo)
    assert ([m["nome"] for m in dados["agendamentos"][0]["montadores"]], dados["agendamentos"][0]["hora_inicio"]) \
        == (["Davi"], "13:30")
    assert obra.escrever("DELETE", f"/agendamentos/{aid}")["agendamentos"] == []
    assert len(_eventos(db_session, "AGENDAMENTO_ALTERADO")) == len(_eventos(db_session, "AGENDAMENTO_EXCLUIDO")) == 1


def test_19_instalacoes_por_montador_e_periodo(api, obra, montadores):
    obra.agendar(["Cozinha Gourmet"], [montadores["Carlos"]])
    obra.agendar(["Closet"], [montadores["Davi"]], data=AMANHA + timedelta(days=7))
    r = api.client.get(f"{URL_MARCENARIA}/instalacoes", params={"montador_id": montadores["Carlos"]},
                       headers=api.header)
    (item,) = r.json()["itens"]
    assert item["ambientes"][0]["nome"] == "Cozinha Gourmet" and item["ambientes"][0]["situacao"] == "PENDENTE"
    assert (item["cliente"], item["endereco_obra"], item["projeto"]) == ("Dona Marta", "Av. das Américas, 4200", "Apto 802")
    r = api.client.get(f"{URL_MARCENARIA}/instalacoes",
                       params={"de": AMANHA.isoformat(), "ate": (AMANHA + timedelta(days=1)).isoformat()},
                       headers=api.header)
    assert [i["ambientes"][0]["nome"] for i in r.json()["itens"]] == ["Cozinha Gourmet"]
    # Sem filtro: na ordem da data.
    r = api.client.get(f"{URL_MARCENARIA}/instalacoes", headers=api.header)
    assert [i["ambientes"][0]["nome"] for i in r.json()["itens"]] == ["Cozinha Gourmet", "Closet"]


def test_20_a_22_data_de_instalacao_da_os_acompanha_a_agenda(obra, montadores, db_session):
    tres, dez = AMANHA + timedelta(days=3), AMANHA + timedelta(days=10)
    obra.agendar(["Cozinha Gourmet"], [montadores["Carlos"]], data=tres)
    dados = obra.agendar(["Closet"], [montadores["Carlos"]], data=dez)
    assert _data_instalacao(db_session, obra.numero_os) == tres                 # 20: a menor
    obra.registrar("Cozinha Gourmet", montadores=[montadores["Carlos"]])
    assert _data_instalacao(db_session, obra.numero_os) == dez                  # 21: a cozinha saiu da fila
    closet = next(a for a in dados["agendamentos"] if a["ambientes"] == ["Closet"])
    obra.escrever("DELETE", f"/agendamentos/{closet['id']}")
    assert _data_instalacao(db_session, obra.numero_os) is None                 # 22: nada a instalar


def test_23_compras_atende_primeiro_a_os_que_instala_antes(api, cliente_id, produto, montadores, db_session):
    chapa = produto("MDF Branco 18mm")
    insumos = [{"produto_id": chapa, "quantidade_milesimos": 2000}]
    _d, antiga = _aprovar_obra(api, cliente_id, ambientes=("Sala",), recusado="Lavanderia", insumos=insumos)
    _d, nova = _aprovar_obra(api, cliente_id, ambientes=("Quarto",), recusado="Banheiro", insumos=insumos)
    ordem = lambda: [d.numero_os for d in demanda_os.demandas_por_produto(db_session, [chapa])[chapa]]  # noqa: E731
    assert ordem() == [antiga, nova]                                   # sem agenda: quem abriu primeiro
    Entrega(api, nova).agendar(["Quarto"], [montadores["Carlos"]], data=AMANHA)
    Entrega(api, antiga).agendar(["Sala"], [montadores["Davi"]], data=AMANHA + timedelta(days=20))
    db_session.expire_all()
    assert ordem() == [nova, antiga]                                   # a mais nova instala antes


def test_24_lista_de_os_igual_a_antes(api, obra, montadores):
    antes = os_da_api(api, obra.numero_os)
    obra.agendar(["Closet"], [montadores["Carlos"]])
    depois = os_da_api(api, obra.numero_os)
    assert set(depois) == set(antes)                                   # nenhuma chave nova na OS


# =========================
# Registro e correcao (06-09, 12, 15)
# =========================

def test_06_registrar_conforme_sem_foto_avisa(obra, montadores, db_session):
    dados = obra.registrar("Closet", montadores=[montadores["Carlos"], montadores["Davi"]],
                           recebido_por="  Ana (síndica) ", checklist=["ok", "ok", "nao_ok", None, "ok"],
                           observacoes="Tudo certo.")
    closet = obra.entrega("Closet", dados)
    assert (closet["situacao"], closet["data_entrega"], closet["recebido_por"]) == ("CONFORME", HOJE.isoformat(),
                                                                                    "Ana (síndica)")
    assert [m["nome"] for m in closet["montadores"]] == ["Carlos", "Davi"]
    assert [i["marcacao"] for i in closet["checklist"]] == ["ok", "ok", "nao_ok", None, "ok"]
    assert [a["codigo"] for a in dados["avisos"]] == ["SEM_FOTO_TERMO"]
    assert dados["resumo"]["entregues"] == 1 and dados["resumo"]["todos_entregues"] is False
    (evento,) = _eventos(db_session, "ENTREGA_REGISTRADA")
    assert evento.descricao == "Entrega de Closet registrada: Conforme."


def test_registro_com_foto_do_termo_nao_avisa_e_montador_que_saiu_vale(obra, montadores):
    obra.foto("Closet", "TERMO")
    dados = obra.registrar("Closet", montadores=[montadores["Edu"]])    # saiu depois, mas montou
    assert dados["avisos"] == []


def test_07_com_ressalvas_sem_pendencia_e_422(obra):
    r = obra.registrar("Closet", situacao="COM_RESSALVAS", pendencias=["  "], esperado=422)
    assert r["detail"] == "Com ressalvas, informe pelo menos uma pendência."


def test_08_com_ressalvas_com_duas_pendencias(obra):
    dados = obra.registrar("Closet", situacao="COM_RESSALVAS",
                           pendencias=["Porta do aéreo 2 desalinhada", "Falta puxador"])
    closet = obra.entrega("Closet", dados)
    assert [(p["descricao"], p["situacao"]) for p in closet["pendencias"]] == [
        ("Porta do aéreo 2 desalinhada", "ABERTA"), ("Falta puxador", "ABERTA")]
    assert [p["descricao"] for p in dados["resumo"]["pendencias_abertas"]] == [
        "Porta do aéreo 2 desalinhada", "Falta puxador"]


def test_09_corrigir_de_conforme_para_com_ressalvas(obra, db_session):
    obra.registrar("Closet")
    dados = obra.registrar("Closet", situacao="COM_RESSALVAS", pendencias=["Riscado"], data_entrega=ONTEM.isoformat())
    assert obra.entrega("Closet", dados)["data_entrega"] == ONTEM.isoformat()
    (evento,) = _eventos(db_session, "ENTREGA_CORRIGIDA")
    assert evento.descricao == "Entrega de Closet corrigida: Conforme → Com ressalvas. 1 pendência(s) anotada(s)."


def test_registro_valida_data_e_marcacoes(obra):
    r = obra.registrar("Closet", data_entrega=AMANHA.isoformat(), esperado=422)
    assert r["detail"] == "A data da entrega não pode ser no futuro."
    r = obra.registrar("Closet", checklist=["ok"], esperado=422)
    assert r["detail"] == "As marcações não conferem com o checklist do ambiente."


def test_12_ultimo_ambiente_registrado_traz_todos_entregues(obra):
    assert obra.registrar("Closet")["resumo"]["todos_entregues"] is False
    assert obra.registrar("Cozinha Gourmet")["resumo"]["todos_entregues"] is True


def test_15_registrar_com_a_os_finalizada_e_409(obra, db_session):
    _status_da_os(db_session, obra.numero_os, OrdemServicoStatus.FINALIZADA)
    assert obra.ler()["os"]["editavel"] is False
    r = obra.registrar("Closet", esperado=409)
    assert r["detail"]["codigo"] == "OS_FECHADA"


# =========================
# Fotos (10-11)
# =========================

def test_10_foto_do_termo_vai_para_a_galeria_da_os_e_para_a_entrega(api, obra):
    dados = obra.foto("Closet", "TERMO")
    (foto,) = obra.entrega("Closet", dados)["fotos"]
    assert foto["tipo"] == "TERMO" and foto["url"]
    galeria = os_da_api(api, obra.numero_os)["fotos"]
    assert [f["id"] for f in galeria] == [foto["os_foto_id"]]


def test_11_excluir_a_foto_pela_entrega_tira_da_galeria(api, obra):
    dados = obra.foto("Closet", "MONTAGEM")
    (foto,) = obra.entrega("Closet", dados)["fotos"]
    closet = obra.entrega("Closet", dados)
    dados = obra.escrever("DELETE", f"/entrega/{closet['id']}/fotos/{foto['id']}")
    assert obra.entrega("Closet", dados)["fotos"] == []
    assert os_da_api(api, obra.numero_os)["fotos"] == []


def test_foto_apagada_pela_galeria_da_os_some_da_entrega(api, obra):
    dados = obra.foto("Closet", "TERMO")
    (foto,) = obra.entrega("Closet", dados)["fotos"]
    r = api.client.delete(f"/api/v1/ordens-servico/{obra.numero_os}/fotos/{foto['os_foto_id']}", headers=api.header)
    assert r.status_code == 204, r.text
    assert obra.entrega("Closet")["fotos"] == []


def test_foto_de_tipo_invalido_e_422_sem_gravar(api, obra):
    obra.foto("Closet", "SELFIE", esperado=422)
    assert os_da_api(api, obra.numero_os)["fotos"] == []


# =========================
# Pendencias e resumo (13-14)
# =========================

def test_13_resumo_lista_pendencia_aberta_e_ambiente_nao_entregue(obra):
    obra.registrar("Cozinha Gourmet", situacao="COM_RESSALVAS", pendencias=["Porta do aéreo 2 desalinhada"])
    r = obra.req("GET", "/entrega/resumo")
    assert r.status_code == 200, r.text
    resumo = r.json()
    assert resumo["ambientes_pendentes"] == ["Closet"]
    (pendencia,) = resumo["pendencias_abertas"]
    assert (pendencia["ambiente"], pendencia["descricao"]) == ("Cozinha Gourmet", "Porta do aéreo 2 desalinhada")


def test_14_resolver_e_criar_pendencia_com_a_os_finalizada(obra, db_session):
    dados = obra.registrar("Closet", situacao="COM_RESSALVAS", pendencias=["Riscado"])
    closet = obra.entrega("Closet", dados)
    pid = closet["pendencias"][0]["id"]
    _status_da_os(db_session, obra.numero_os, OrdemServicoStatus.FINALIZADA)
    dados = obra.escrever("POST", f"/entrega/{closet['id']}/pendencias/{pid}/resolver",
                          {"resolucao": "Trocada a porta", "data": HOJE.isoformat()})
    pendencia = obra.entrega("Closet", dados)["pendencias"][0]
    assert (pendencia["situacao"], pendencia["resolucao"], pendencia["resolvida_por"]) == (
        "RESOLVIDA", "Trocada a porta", "Admin Master")
    obra.escrever("POST", f"/entrega/{closet['id']}/pendencias/{pid}/resolver", {"resolucao": "x"}, esperado=409)
    dados = obra.escrever("POST", f"/entrega/{closet['id']}/pendencias/{pid}/reabrir")
    assert obra.entrega("Closet", dados)["pendencias"][0]["resolucao"] is None
    dados = obra.escrever("POST", f"/entrega/{closet['id']}/pendencias", {"descricao": "Cliente ligou: gaveta"})
    assert len(obra.entrega("Closet", dados)["pendencias"]) == 2
    assert {e.tipo for e in db_session.query(MarcenariaEvento).all()} >= {
        "PENDENCIA_RESOLVIDA", "PENDENCIA_REABERTA", "PENDENCIA_CRIADA"}


def test_pendencia_so_depois_do_registro(obra):
    closet = obra.entrega("Closet")
    r = obra.escrever("POST", f"/entrega/{closet['id']}/pendencias", {"descricao": "Algo"}, esperado=422)
    assert r["detail"] == "Registre a entrega do ambiente antes de anotar pendências."


# =========================
# Desfazer, permissao e capacidade (18)
# =========================

def test_18_desfazer_bloqueado_com_entrega_registrada(api, obra):
    obra.registrar("Closet")
    motivos = api.ok("GET", f"/por-os/{obra.numero_os}")["motivos_desfazer"]
    assert "Já há entrega registrada (Closet)." in motivos


def test_18_desfazer_so_com_agendamento_apaga_tudo(api, cliente_id, montadores, db_session):
    d, numero = _aprovar_obra(api, cliente_id)
    Entrega(api, numero).agendar(["Closet"], [montadores["Carlos"]])
    assert _data_instalacao(db_session, numero) == AMANHA
    r = api.req("POST", f"/{d['id']}/desfazer-aprovacao", rev=d["revisao"],
                json={"motivo": "Cliente mudou de ideia", "destino_sinal": "CREDITO"})
    assert r.status_code == 200, r.text
    db_session.expire_all()
    assert db_session.query(MarcenariaEntrega).count() == 0
    assert db_session.query(MarcenariaAgendamento).count() == 0
    assert _data_instalacao(db_session, numero) is None


def test_permissao_de_os_e_capacidade(api, obra, como, mudar_segmento):
    como(view_orcamentos_marcenaria=True)
    assert obra.req("GET", "/entrega").status_code == 403
    como(servico=True)
    assert obra.req("GET", "/entrega").status_code == 200
    mudar_segmento("informatica")
    assert obra.req("GET", "/entrega").status_code == 404
    assert api.client.get(f"{URL_MARCENARIA}/instalacoes", headers=api.header).status_code == 404


def test_os_sem_orcamento_e_404(api, obra):
    r = api.client.get(f"{URL_MARCENARIA}/os/OS-2099-999999/entrega", headers=api.header)
    assert r.status_code == 404 and r.json()["detail"] == "Esta OS não veio de um orçamento."


def test_instalacoes_ignora_os_cancelada(api, obra, montadores, db_session):
    obra.agendar(["Closet"], [montadores["Carlos"]])
    _status_da_os(db_session, obra.numero_os, OrdemServicoStatus.CANCELADA)
    r = api.client.get(f"{URL_MARCENARIA}/instalacoes", headers=api.header)
    assert r.json()["itens"] == []


def test_datas_em_utc_e_hora_de_criacao(obra, montadores, db_session):
    obra.agendar(["Closet"], [montadores["Carlos"]])
    db_session.expire_all()
    agendamento = db_session.query(MarcenariaAgendamento).one()
    assert isinstance(agendamento.criado_em, datetime) and agendamento.criado_por_nome == "Admin Master"
