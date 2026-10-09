# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/marcenaria/test_producao_api.py
# DESCRICAO: Producao da OS da marcenaria pela API (Spec 12A, secao 11,
#            casos 01-18).
#
#            O que nao pode errar:
#              - a aprovacao copia as etapas da configuracao (e so na hora);
#              - concluir e idempotente e aceita lote, ate de moveis diferentes;
#              - o backend SO sugere o status da OS, nunca muda;
#              - terceirizado conferido conta como pronto;
#              - nenhum preco; desfazer bloqueado com a producao comecada.
# ---------------------------------------------------------------------------

import pytest

from app.core.enum import OrdemServicoStatus
from app.db.models.configuracao_marcenaria import ConfiguracaoMarcenaria
from app.db.models.marcenaria import MarcenariaEvento
from app.db.models.marcenaria.etapa import MarcenariaEtapa
from app.db.models.ordem_servico import OrdemServico

from test.apoio_orcamento_marcenaria import URL_MARCENARIA, aprovar

OS_URL = "/api/v1/ordens-servico"
PADRAO = ["Corte", "Borda", "Furação", "Montagem", "Embalagem"]


# =========================
# Ajudantes
# =========================

class Producao:
    """Atalho para a API da producao de uma OS."""

    def __init__(self, api, numero_os: str):
        self.api, self.numero_os = api, numero_os

    def req(self, metodo: str, caminho: str = "", **kwargs):
        return self.api.client.request(metodo, f"{URL_MARCENARIA}/os/{self.numero_os}/producao{caminho}",
                                       headers=self.api.header, **kwargs)

    def ler(self) -> dict:
        r = self.req("GET")
        assert r.status_code == 200, r.text
        return r.json()

    def movel(self, nome: str, producao: dict = None) -> dict:
        return next(m for m in (producao or self.ler())["moveis"] if m["nome"] == nome)

    def etapa(self, movel: str, nome: str, producao: dict = None) -> dict:
        return next(e for e in self.movel(movel, producao)["etapas"] if e["nome"] == nome)

    def escrever(self, metodo: str, caminho: str, json: dict = None, esperado: int = 200):
        r = self.req(metodo, caminho, json=json)
        assert r.status_code == esperado, r.text
        return r.json()

    def concluir(self, *etapa_ids: int, **extra) -> dict:
        return self.escrever("POST", "/etapas/concluir", {"etapa_ids": list(etapa_ids), **extra})


def _movel(nome: str, **extra) -> dict:
    return {"nome": nome, "quantidade": 1, "mao_obra": {"modo": "FIXA", "centavos": 10000, "horas_centesimos": 0},
            "insumos": [], **extra}


def _aprovar_obra(api, cliente_id: int, central: int, nomes_internos=("Balcão", "Aéreo")) -> tuple[dict, str]:
    """Os moveis internos dados + a Torre Quente terceirizada; aprovado inteiro."""
    orc = api.criar(cliente_id=cliente_id, projeto_nome="Apto 802")
    d = api.ok("POST", f"/{orc['id']}/ambientes", rev=orc["revisao"], esperado=201, json={"nome": "Cozinha"})
    amb = d["ambientes"][0]["id"]
    for nome in nomes_internos:
        d = api.ok("POST", f"/{orc['id']}/ambientes/{amb}/moveis", rev=d["revisao"], esperado=201, json=_movel(nome))
    d = api.ok("POST", f"/{orc['id']}/ambientes/{amb}/moveis", rev=d["revisao"], esperado=201, json=_movel(
        "Torre Quente", tipo_producao="TERCEIRIZADA", central_fornecedor_id=central, terceirizado_centavos=38000))
    d = aprovar(api, d)
    return d, d["os"]["numero_os"]


@pytest.fixture
def obra(api, fornecedor, cliente_id) -> Producao:
    _d, numero = _aprovar_obra(api, cliente_id, fornecedor("Madeiranit"))
    return Producao(api, numero)


def _status_da_os(db, numero: str, status: OrdemServicoStatus) -> None:
    db.query(OrdemServico).filter_by(numero_os=numero).one().status = status
    db.commit()


def _terceirizado(api, numero: str, ate: str) -> None:
    """Leva a Torre (sem o Compras) ate RECEBIDO ou CONFERIDO."""
    base = f"{URL_MARCENARIA}/os/{numero}/terceirizados"
    torre = next(m for m in api.client.get(base, headers=api.header).json()["moveis"] if m["nome"] == "Torre Quente")
    for passo in ("/enviar-manual", "/receber-manual") + (("/conferir",) if ate == "CONFERIDO" else ()):
        r = api.client.post(f"{base}{passo}", json={"movel_ids": [torre["movel_id"]]}, headers=api.header)
        assert r.status_code == 200, r.text


def _todas(producao: dict, *moveis: str) -> list[int]:
    return [e["id"] for m in producao["moveis"] if m["nome"] in moveis for e in m["etapas"]]


# =========================
# Etapas na aprovacao (01-03)
# =========================

def test_01_aprovacao_cria_as_etapas_padrao_nos_internos(obra):
    producao = obra.ler()
    balcao = obra.movel("Balcão", producao)
    assert [e["nome"] for e in balcao["etapas"]] == PADRAO
    assert {e["status"] for e in balcao["etapas"]} == {"PENDENTE"}
    assert (balcao["pronto"], balcao["sem_etapas"], balcao["proxima_etapa"]) == (False, False, "Corte")
    torre = obra.movel("Torre Quente", producao)
    assert "etapas" not in torre and torre["terceirizado"]["situacao"] == "A_PEDIR" and torre["pronto"] is False
    assert producao["progresso"] == {"etapas_concluidas": 0, "etapas_total": 10, "moveis_prontos": 0, "moveis_total": 3}
    assert producao["producao_concluida"] is False and producao["sugestao_status"] is None
    assert producao["os"]["editavel"] is True and producao["os"]["previsao"]


def test_02_mudar_a_configuracao_nao_mexe_na_os(obra, db_session):
    db_session.query(ConfiguracaoMarcenaria).one().etapas_producao = ["Corte", "Pintura"]
    db_session.commit()
    assert [e["nome"] for e in obra.movel("Balcão")["etapas"]] == PADRAO


def test_03_configuracao_vazia_deixa_sem_etapas_e_aplicar_padrao_resolve(api, fornecedor, cliente_id, db_session):
    api.criar()                                                       # garante a configuracao
    db_session.query(ConfiguracaoMarcenaria).one().etapas_producao = []
    db_session.commit()
    _d, numero = _aprovar_obra(api, cliente_id, fornecedor("Madeiranit"), nomes_internos=("Balcão",))
    p = Producao(api, numero)
    balcao = p.movel("Balcão")
    assert (balcao["sem_etapas"], balcao["etapas"], balcao["pronto"]) == (True, [], False)

    db_session.query(ConfiguracaoMarcenaria).one().etapas_producao = ["Corte", "Montagem"]
    db_session.commit()
    producao = p.escrever("POST", f"/moveis/{balcao['movel_id']}/aplicar-padrao")
    assert [e["nome"] for e in p.movel("Balcão", producao)["etapas"]] == ["Corte", "Montagem"]
    assert p.escrever("POST", f"/moveis/{balcao['movel_id']}/aplicar-padrao", esperado=409)["detail"]["codigo"] == "JA_TEM_ETAPAS"


# =========================
# Editar a lista (04-06)
# =========================

def test_04_incluir_pintura_depois_da_montagem_e_tirar_a_furacao(obra):
    balcao = obra.movel("Balcão")
    por_nome = {e["nome"]: e["id"] for e in balcao["etapas"]}
    lista = [{"id": por_nome["Corte"], "nome": "Corte"}, {"id": por_nome["Borda"], "nome": "Borda"},
             {"id": por_nome["Montagem"], "nome": "Montagem"}, {"nome": "Pintura"},
             {"id": por_nome["Embalagem"], "nome": "Embalagem"}]
    producao = obra.escrever("PUT", f"/moveis/{balcao['movel_id']}/etapas", {"etapas": lista})
    etapas = obra.movel("Balcão", producao)["etapas"]
    assert [(e["nome"], e["ordem"]) for e in etapas] == [("Corte", 1), ("Borda", 2), ("Montagem", 3), ("Pintura", 4), ("Embalagem", 5)]
    assert etapas[0]["id"] == por_nome["Corte"]                       # a mesma etapa, nao uma copia


def test_04_trocar_dois_nomes_de_lugar_nao_bate_na_unicidade(obra):
    balcao = obra.movel("Balcão")
    ids = [e["id"] for e in balcao["etapas"]]
    lista = [{"id": ids[0], "nome": "Borda"}, {"id": ids[1], "nome": "Corte"}] + \
            [{"id": e["id"], "nome": e["nome"]} for e in balcao["etapas"][2:]]
    producao = obra.escrever("PUT", f"/moveis/{balcao['movel_id']}/etapas", {"etapas": lista})
    assert [e["nome"] for e in obra.movel("Balcão", producao)["etapas"]][:2] == ["Borda", "Corte"]


def test_05_remover_ou_renomear_etapa_concluida_e_409(obra):
    balcao = obra.movel("Balcão")
    corte = balcao["etapas"][0]
    obra.concluir(corte["id"])
    sem_corte = [{"id": e["id"], "nome": e["nome"]} for e in balcao["etapas"][1:]]
    r = obra.escrever("PUT", f"/moveis/{balcao['movel_id']}/etapas", {"etapas": sem_corte}, esperado=409)
    assert r["detail"] == {"codigo": "ETAPA_CONCLUIDA",
                           "mensagem": "A etapa Corte está concluída: reabra antes de remover ou renomear."}
    renomeada = [{"id": corte["id"], "nome": "Corte CNC"}] + sem_corte
    obra.escrever("PUT", f"/moveis/{balcao['movel_id']}/etapas", {"etapas": renomeada}, esperado=409)


def test_06_nomes_repetidos_vazios_e_limites_sao_422(obra):
    balcao = obra.movel("Balcão")
    url = f"/moveis/{balcao['movel_id']}/etapas"
    r = obra.escrever("PUT", url, {"etapas": [{"nome": "Corte"}, {"nome": "corte"}]}, esperado=422)
    assert r["detail"] == "Etapas: há itens repetidos."
    assert obra.escrever("PUT", url, {"etapas": []}, esperado=422)["detail"] == "Etapas: informe de 1 a 20 itens."
    assert obra.escrever("PUT", url, {"etapas": [{"nome": "x" * 61}]}, esperado=422)["detail"] == \
        "Etapas: cada item pode ter até 60 caracteres."
    torre = obra.movel("Torre Quente")
    assert obra.escrever("PUT", f"/moveis/{torre['movel_id']}/etapas", {"etapas": [{"nome": "Corte"}]}, esperado=422)


# =========================
# Transicoes (07-09)
# =========================

def test_07_concluir_direto_do_pendente_grava_quem_fez(obra, db_session):
    corte = obra.etapa("Balcão", "Corte")
    producao = obra.concluir(corte["id"])
    etapa = obra.etapa("Balcão", "Corte", producao)
    assert etapa["status"] == "CONCLUIDA" and etapa["concluida_em"]
    assert (etapa["responsavel"], etapa["concluida_por"]) == ("Admin Master", "Admin Master")
    assert obra.movel("Balcão", producao)["proxima_etapa"] == "Borda"


def test_iniciar_reabrir_e_responsavel_escolhido(obra, db_session):
    from app.db.models.funcionario import Funcionario
    joao = db_session.query(Funcionario).first()
    borda = obra.etapa("Balcão", "Borda")
    producao = obra.escrever("POST", "/etapas/iniciar", {"etapa_ids": [borda["id"]],
                                                          "responsavel_funcionario_id": joao.id})
    etapa = obra.etapa("Balcão", "Borda", producao)
    assert (etapa["status"], etapa["responsavel"], etapa["responsavel_funcionario_id"]) == ("EM_EXECUCAO", joao.nome, joao.id)
    assert etapa["iniciada_em"]
    producao = obra.escrever("POST", f"/etapas/{borda['id']}/reabrir")
    etapa = obra.etapa("Balcão", "Borda", producao)
    assert (etapa["status"], etapa["iniciada_em"], etapa["responsavel"]) == ("PENDENTE", None, None)
    r = obra.escrever("POST", "/etapas/iniciar", {"etapa_ids": [borda["id"]], "responsavel_funcionario_id": 999999},
                      esperado=422)
    assert r["detail"] == "Funcionário não encontrado ou inativo."


def test_08_concluir_duas_vezes_nao_muda_quem_concluiu(obra, como, db_session):
    corte = obra.etapa("Balcão", "Corte")
    obra.concluir(corte["id"])
    como(servico=True)                                                # outra pessoa, mesmo clique
    producao = obra.concluir(corte["id"])
    assert obra.etapa("Balcão", "Corte", producao)["concluida_por"] == "Admin Master"
    assert db_session.query(MarcenariaEvento).filter_by(tipo="ETAPAS_CONCLUIDAS").count() == 1


def test_09_concluir_em_todos_e_um_evento(obra, db_session):
    producao = obra.escrever("POST", "/etapas/concluir-em-todos", {"nome": "corte"})
    assert {obra.etapa(m, "Corte", producao)["status"] for m in ("Balcão", "Aéreo")} == {"CONCLUIDA"}
    assert producao["progresso"]["etapas_concluidas"] == 2
    (evento,) = db_session.query(MarcenariaEvento).filter_by(tipo="ETAPAS_CONCLUIDAS").all()
    assert evento.descricao == "Etapa Corte concluída em 2 móveis por Admin Master."
    r = obra.escrever("POST", "/etapas/concluir-em-todos", {"nome": "Laqueação"}, esperado=422)
    assert r["detail"] == "Nenhum móvel desta OS tem a etapa Laqueação."


def test_lote_vazio_e_422(obra):
    assert obra.escrever("POST", "/etapas/concluir", {"etapa_ids": []}, esperado=422)["detail"] == "Escolha pelo menos uma etapa."


# =========================
# Sugestao de status (10-14)
# =========================

def test_10_primeira_etapa_numa_os_aberta_sugere_em_producao(obra):
    producao = obra.concluir(obra.etapa("Balcão", "Corte")["id"])
    assert producao["sugestao_status"] == {"de": "ABERTA", "para": "EM_ANDAMENTO", "rotulo": "Em Produção"}
    producao = obra.concluir(obra.etapa("Balcão", "Borda")["id"])
    assert producao["sugestao_status"] is None                        # so na mudanca (D17)


def test_11_tudo_pronto_com_terceirizado_conferido_sugere_aguardando_entrega(api, obra, db_session):
    _terceirizado(api, obra.numero_os, "CONFERIDO")
    _status_da_os(db_session, obra.numero_os, OrdemServicoStatus.EM_ANDAMENTO)
    producao = obra.concluir(*_todas(obra.ler(), "Balcão", "Aéreo"))
    assert producao["producao_concluida"] is True
    assert producao["progresso"] == {"etapas_concluidas": 10, "etapas_total": 10, "moveis_prontos": 3, "moveis_total": 3}
    assert producao["sugestao_status"] == {"de": "EM_ANDAMENTO", "para": "AGUARDANDO_RETIRADA", "rotulo": "Aguardando Entrega"}
    # O backend nunca muda o status sozinho (P2).
    db_session.expire_all()
    assert db_session.query(OrdemServico).filter_by(numero_os=obra.numero_os).one().status == OrdemServicoStatus.EM_ANDAMENTO


def test_12_terceirizado_so_recebido_nao_conclui(api, obra, db_session):
    _terceirizado(api, obra.numero_os, "RECEBIDO")
    _status_da_os(db_session, obra.numero_os, OrdemServicoStatus.EM_ANDAMENTO)
    producao = obra.concluir(*_todas(obra.ler(), "Balcão", "Aéreo"))
    assert (producao["producao_concluida"], producao["sugestao_status"]) == (False, None)


def test_11a_conferir_o_ultimo_terceirizado_tambem_sugere(api, obra, db_session):
    _terceirizado(api, obra.numero_os, "RECEBIDO")
    _status_da_os(db_session, obra.numero_os, OrdemServicoStatus.EM_ANDAMENTO)
    obra.concluir(*_todas(obra.ler(), "Balcão", "Aéreo"))
    torre = obra.movel("Torre Quente")
    r = api.client.post(f"{URL_MARCENARIA}/os/{obra.numero_os}/terceirizados/conferir",
                        json={"movel_ids": [torre["movel_id"]]}, headers=api.header)
    assert r.status_code == 200, r.text
    assert r.json()["sugestao_status"]["para"] == "AGUARDANDO_RETIRADA"   # o terceirizado foi o ultimo a ficar pronto


def test_13_reabrir_e_concluir_de_novo_sugere_de_novo(api, obra, db_session):
    _terceirizado(api, obra.numero_os, "CONFERIDO")
    _status_da_os(db_session, obra.numero_os, OrdemServicoStatus.EM_ANDAMENTO)
    obra.concluir(*_todas(obra.ler(), "Balcão", "Aéreo"))
    corte = obra.etapa("Balcão", "Corte")
    assert obra.escrever("POST", f"/etapas/{corte['id']}/reabrir")["sugestao_status"] is None
    assert obra.concluir(corte["id"])["sugestao_status"]["para"] == "AGUARDANDO_RETIRADA"


def test_14_os_ja_aguardando_retirada_nao_sugere(api, obra, db_session):
    _terceirizado(api, obra.numero_os, "CONFERIDO")
    _status_da_os(db_session, obra.numero_os, OrdemServicoStatus.AGUARDANDO_RETIRADA)
    assert obra.concluir(*_todas(obra.ler(), "Balcão", "Aéreo"))["sugestao_status"] is None


# =========================
# OS fechada, desfazer, quadro e etapa de fora (15-18)
# =========================

def test_15_os_finalizada_e_so_leitura(obra, db_session):
    corte = obra.etapa("Balcão", "Corte")
    _status_da_os(db_session, obra.numero_os, OrdemServicoStatus.FINALIZADA)
    assert obra.ler()["os"]["editavel"] is False
    r = obra.escrever("POST", "/etapas/concluir", {"etapa_ids": [corte["id"]]}, esperado=409)
    assert r["detail"]["codigo"] == "OS_FECHADA"


def test_16_desfazer_bloqueado_com_producao_comecada(api, obra):
    obra.escrever("POST", "/etapas/concluir-em-todos", {"nome": "Corte"})
    obra.escrever("POST", "/etapas/iniciar", {"etapa_ids": [obra.etapa("Balcão", "Borda")["id"]]})
    motivos = api.ok("GET", f"/por-os/{obra.numero_os}")["motivos_desfazer"]
    assert "A produção já começou (Corte concluída em 2 móveis; Borda em execução em 1 móvel)." in motivos


def test_desfazer_sem_producao_apaga_as_etapas(api, fornecedor, cliente_id, db_session, forma_pagamento):
    d, numero = _aprovar_obra(api, cliente_id, fornecedor("Madeiranit"))
    assert db_session.query(MarcenariaEtapa).count() == 10
    r = api.req("POST", f"/{d['id']}/desfazer-aprovacao", rev=d["revisao"],
                json={"motivo": "Cliente mudou de ideia", "destino_sinal": "CREDITO"})
    assert r.status_code == 200, r.text
    db_session.expire_all()
    assert db_session.query(MarcenariaEtapa).count() == 0


def test_17_quadro_da_fabrica(api, fornecedor, cliente_id):
    central = fornecedor("Madeiranit")
    numeros = [_aprovar_obra(api, cliente_id, central)[1] for _ in range(3)]
    primeira = Producao(api, numeros[0])
    primeira.escrever("POST", "/etapas/concluir-em-todos", {"nome": "Corte"})

    r = api.client.get(f"{URL_MARCENARIA}/producao", headers=api.header)
    assert r.status_code == 200, r.text
    itens = {i["numero_os"]: i for i in r.json()["itens"]}
    assert set(numeros) <= set(itens)
    linha = itens[numeros[0]]
    assert linha["progresso"] == {"etapas_concluidas": 2, "etapas_total": 10, "moveis_prontos": 0, "moveis_total": 3}
    assert linha["proxima_etapa"] == {"nome": "Borda", "moveis": 2}
    assert (linha["cliente"], linha["projeto"], linha["rotulo_status"]) == ("Dona Marta", "Apto 802", "Aberta")
    assert itens[numeros[1]]["proxima_etapa"] == {"nome": "Corte", "moveis": 2}
    chaves = {k for i in r.json()["itens"] for k in i} | {k for i in r.json()["itens"] for k in i["progresso"]}
    assert not [k for k in chaves if any(p in k for p in ("custo", "preco", "valor", "margem"))]


def test_18_etapa_de_outra_os_no_lote_e_404_e_nada_muda(api, obra, fornecedor, cliente_id):
    _d, outra = _aprovar_obra(api, cliente_id, fornecedor("Outra"))
    de_fora = Producao(api, outra).etapa("Balcão", "Corte")["id"]
    corte = obra.etapa("Balcão", "Corte")["id"]
    r = obra.escrever("POST", "/etapas/concluir", {"etapa_ids": [corte, de_fora]}, esperado=404)
    assert r["detail"] == "Etapa não encontrada nesta OS."
    assert obra.etapa("Balcão", "Corte")["status"] == "PENDENTE"


def test_permissao_de_os_e_capacidade(obra, como, mudar_segmento):
    como(view_orcamentos_marcenaria=True)
    assert obra.req("GET").status_code == 403
    como(servico=True)
    assert obra.req("GET").status_code == 200
    mudar_segmento("serigrafia")
    assert obra.req("GET").status_code == 404


def test_nenhum_preco_na_producao(obra):
    def chaves(valor):
        if isinstance(valor, dict):
            return set(valor) | {k for v in valor.values() for k in chaves(v)}
        if isinstance(valor, list):
            return {k for v in valor for k in chaves(v)}
        return set()
    assert not [k for k in chaves(obra.ler()) if any(p in k for p in ("custo", "preco", "valor", "margem"))]
