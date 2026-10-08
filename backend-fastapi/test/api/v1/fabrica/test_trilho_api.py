# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/fabrica/test_trilho_api.py
# DESCRIÇÃO: O trilho da fábrica (docs/marcenaria-fabrica-plano.md, F3, §6).
#
# O que não pode errar:
# - o STATUS de sempre acompanha a etapa (lista, dashboard e relatórios
#   continuam funcionando sem saber das etapas), e não se troca à mão;
# - pendência: trava (409) com a chave ligada, aviso com motivo sem ela;
# - sem sinal (nem liberação) o material RESERVA mas não vira compra (RC04);
# - a fila de Compras atende quem instala primeiro (RC12);
# - quem só tem a permissão da OS não vê custo nem mexe no orçamento.
# ---------------------------------------------------------------------------

from datetime import date, timedelta

import pytest

from app.core.enum import OrdemServicoStatus
from app.db.models.configuracao_os import ConfiguracaoOS
from app.db.models.empresa import Empresa
from app.db.models.ordem_servico import OrdemServico
from app.db.models.ordem_servico_foto import OrdemServicoFoto
from app.services.compras import necessidades as necessidades_service
from app.services.compras.demanda_os import compras_da_os, demandas_por_produto
from app.services.fabrica import trilho

from .test_orcamento_api import FAB, OS, acao, cozinha, nova_versao, os_atual, salvar


def trilho_de(client, headers, numero):
    r = client.get(f"{FAB}/os/{numero}/trilho", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def avancar(client, headers, numero, motivo=None):
    return client.post(f"{FAB}/os/{numero}/avancar", json={"motivo": motivo} if motivo else {}, headers=headers)


@pytest.fixture
def travar(db_session):
    def _definir(ligado=True):
        empresa = db_session.query(Empresa).first()
        config = db_session.query(ConfiguracaoOS).filter_by(empresa_id=empresa.id).one()
        config.fabrica_travar_etapas = ligado
        db_session.commit()
    return _definir


@pytest.fixture
def os_aprovada(client, header_com_token, modo_fabrica, abrir_os, insumos):
    """Cozinha aprovada (R$ 5.500, sinal 50% = R$ 2.750), aguardando o sinal."""
    def _abrir(nome="Cozinha apto 302"):
        os_ = abrir_os(nome=nome)
        v1 = nova_versao(client, header_com_token, os_["numero_os"])
        assert salvar(client, header_com_token, v1["id"], cozinha(insumos)).status_code == 200
        assert acao(client, header_com_token, v1["id"], "enviar").status_code == 200
        assert acao(client, header_com_token, v1["id"], "aprovar").status_code == 200
        return os_["numero_os"]
    return _abrir


def pagar_sinal(db_session, numero, valor=275000):
    os_ = db_session.query(OrdemServico).filter_by(numero_os=numero).one()
    os_.valor_entrada = valor
    db_session.commit()


# --- status acompanha a etapa ------------------------------------------------------

def test_status_acompanha_a_etapa_do_orcamento(client, header_com_token, modo_fabrica, abrir_os, insumos):
    os_ = abrir_os()
    numero = os_["numero_os"]
    assert (os_["fase_fabrica"], os_["status"]) == ("MEDICAO", "ABERTA")

    v1 = nova_versao(client, header_com_token, numero)
    salvar(client, header_com_token, v1["id"], cozinha(insumos))
    acao(client, header_com_token, v1["id"], "enviar")
    atual = os_atual(client, header_com_token, numero)
    assert (atual["fase_fabrica"], atual["status"]) == ("AGUARDANDO_APROVACAO", "AGUARDANDO_APROVACAO")

    acao(client, header_com_token, v1["id"], "aprovar")
    t = trilho_de(client, header_com_token, numero)
    assert (t["fase"], t["status_os"]) == ("AGUARDANDO_SINAL", "AGUARDANDO_APROVACAO")
    assert [l["evento"] for l in t["log"]] == ["APROVACAO", "AVANCO", "AVANCO"]   # mais novo primeiro
    assert [e["situacao"] for e in t["etapas"]][:5] == ["FEITA", "FEITA", "FEITA", "ATUAL", "A_FAZER"]


def test_status_nao_se_troca_a_mao_na_os_da_fabrica(client, header_com_token, modo_fabrica, abrir_os):
    numero = abrir_os()["numero_os"]
    r = client.put(f"{OS}/{numero}", json={"status": "EM_ANDAMENTO"}, headers=header_com_token)
    assert r.status_code == 409


def test_os_comum_troca_status_como_sempre(client, header_com_token, modo_fabrica, abrir_os):
    modo_fabrica(False)
    numero = abrir_os()["numero_os"]
    r = client.put(f"{OS}/{numero}", json={"status": "EM_ANDAMENTO"}, headers=header_com_token)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "EM_ANDAMENTO"


# --- avançar: aviso × trava -------------------------------------------------------------

def test_sem_sinal_avancar_pede_motivo_e_o_log_guarda(client, header_com_token, os_aprovada):
    numero = os_aprovada()
    r = avancar(client, header_com_token, numero)
    assert r.status_code == 422
    assert r.json()["detail"]["codigo"] == "MOTIVO_OBRIGATORIO"
    assert "R$ 0,00 de R$ 2.750,00" in r.json()["detail"]["travas"][0]

    r = avancar(client, header_com_token, numero, motivo="Cliente paga amanhã, combinado")
    assert r.status_code == 200, r.text
    assert (r.json()["fase"], r.json()["status_os"]) == ("SEPARACAO_COMPRA", "AGUARDANDO_PECAS")
    assert r.json()["log"][1]["evento"] == "AVISO_IGNORADO"


def test_com_a_trava_ligada_nao_avanca(client, header_com_token, os_aprovada, travar):
    numero = os_aprovada()
    travar()
    r = avancar(client, header_com_token, numero, motivo="tanto faz")
    assert r.status_code == 409
    assert r.json()["detail"]["codigo"] == "TRAVA_PENDENTE"


def test_sinal_pago_avanca_sem_motivo(client, header_com_token, os_aprovada, travar, db_session):
    numero = os_aprovada()
    travar()
    pagar_sinal(db_session, numero)
    t = trilho_de(client, header_com_token, numero)
    assert t["travas"] == [{"codigo": "SINAL", "texto": "Sinal recebido: R$ 2.750,00 de R$ 2.750,00", "ok": True}]
    assert avancar(client, header_com_token, numero).json()["fase"] == "SEPARACAO_COMPRA"


def test_enviar_aprovar_e_finalizar_nao_passam_pelo_avancar(client, header_com_token, modo_fabrica, abrir_os, insumos):
    numero = abrir_os()["numero_os"]
    nova_versao(client, header_com_token, numero)                  # → ELABORACAO
    r = avancar(client, header_com_token, numero)
    assert r.status_code == 409
    assert "Envie a proposta" in r.json()["detail"]


def test_pronto_para_expedicao_exige_instalacao(client, header_com_token, os_aprovada, travar, db_session):
    numero = os_aprovada()
    os_ = db_session.query(OrdemServico).filter_by(numero_os=numero).one()
    os_.fase_fabrica = "PRONTO_EXPEDICAO"
    db_session.commit()
    travar()
    assert avancar(client, header_com_token, numero).status_code == 409
    r = client.put(f"{FAB}/os/{numero}/instalacao", json={"data_instalacao": str(date.today() + timedelta(days=7))},
                   headers=header_com_token)
    assert r.status_code == 200
    assert avancar(client, header_com_token, numero).json()["fase"] == "EM_INSTALACAO"


def test_medicao_trava_sem_foto(client, header_com_token, modo_fabrica, abrir_os, travar, db_session):
    travar()
    numero = abrir_os()["numero_os"]
    assert avancar(client, header_com_token, numero).status_code == 409
    os_ = db_session.query(OrdemServico).filter_by(numero_os=numero).one()
    db_session.add(OrdemServicoFoto(ordem_servico_id=os_.id, nome_arquivo="medicao.jpg", url="/fotos/medicao.jpg"))
    db_session.commit()
    assert avancar(client, header_com_token, numero).json()["fase"] == "ELABORACAO"


# --- voltar -----------------------------------------------------------------------------------

def test_voltar_pede_motivo_e_nao_passa_do_sinal_com_orcamento_aprovado(client, header_com_token, os_aprovada, db_session):
    numero = os_aprovada()
    pagar_sinal(db_session, numero)
    avancar(client, header_com_token, numero)                       # → SEPARACAO_COMPRA
    url = f"{FAB}/os/{numero}/voltar"
    assert client.post(url, json={"fase": "AGUARDANDO_SINAL"}, headers=header_com_token).status_code == 422
    r = client.post(url, json={"fase": "ELABORACAO", "motivo": "refazer"}, headers=header_com_token)
    assert r.status_code == 409
    r = client.post(url, json={"fase": "AGUARDANDO_SINAL", "motivo": "cheque voltou"}, headers=header_com_token)
    assert r.status_code == 200
    assert (r.json()["fase"], r.json()["status_os"], r.json()["log"][0]["evento"]) == (
        "AGUARDANDO_SINAL", "AGUARDANDO_APROVACAO", "RETROCESSO")


# --- finalizar, cancelar, reabrir --------------------------------------------------------------

def test_finalizar_com_trava_so_depois_da_vistoria(client, header_com_token, os_aprovada, travar, db_session):
    numero = os_aprovada()
    travar()
    os_ = db_session.query(OrdemServico).filter_by(numero_os=numero).one()
    with pytest.raises(Exception) as erro:
        trilho.assert_pode_finalizar(db_session, os_)
    assert "vistoria final" in str(erro.value.detail)

    os_.fase_fabrica = "VISTORIA_FINAL"
    trilho.assert_pode_finalizar(db_session, os_)                   # passa
    os_.status = OrdemServicoStatus.FINALIZADA
    trilho.ao_finalizar(db_session, os_, "Gerente")
    assert (os_.fase_fabrica, os_.status) == ("ENTREGUE", OrdemServicoStatus.FINALIZADA)

    os_.status = OrdemServicoStatus.EM_ANDAMENTO                   # o que o reabrir faz antes do gancho
    trilho.ao_reabrir(db_session, os_, "Gerente")
    assert (os_.fase_fabrica, os_.status) == ("VISTORIA_FINAL", OrdemServicoStatus.AGUARDANDO_RETIRADA)


# --- Compras: sinal (RC04) e fila pela instalação (RC12) ----------------------------------------

def test_sem_sinal_reserva_mas_nao_compra(client, header_com_token, os_aprovada, insumos, db_session):
    numero = os_aprovada()
    os_ = db_session.query(OrdemServico).filter_by(numero_os=numero).one()
    token = {"empresa_id": 1}

    demanda = demandas_por_produto(db_session, [insumos["mdf"]])[insumos["mdf"]][0]
    assert (demanda.quantidade, demanda.pode_comprar) == (3, False)
    assert compras_da_os(db_session, os_.id).compra_bloqueada is True
    itens = [i for g in necessidades_service.listar(db_session, token, True) for i in g.itens]
    assert not [i for i in itens if i.produto_id == insumos["mdf"]]       # nada a comprar ainda

    r = client.post(f"{FAB}/os/{numero}/liberar-compra", json={"motivo": "Cliente antigo, prazo curto"},
                    headers=header_com_token)
    assert r.status_code == 200
    assert (r.json()["pode_comprar"], r.json()["log"][0]["evento"]) == (True, "LIBERACAO_COMPRA")
    itens = [i for g in necessidades_service.listar(db_session, token, True) for i in g.itens]
    mdf = next(i for i in itens if i.produto_id == insumos["mdf"])
    assert (mdf.sugestao, mdf.reservado_os, mdf.origem) == (3, 3, "OS")


def test_fila_atende_quem_instala_primeiro(client, header_com_token, os_aprovada, insumos, db_session):
    primeira = os_aprovada("Cozinha A")
    segunda = os_aprovada("Cozinha B")
    fila = [d.numero_os for d in demandas_por_produto(db_session, [insumos["mdf"]])[insumos["mdf"]]]
    assert fila == [primeira, segunda]                                # sem data: quem abriu primeiro

    client.put(f"{FAB}/os/{segunda}/instalacao", json={"data_instalacao": str(date.today() + timedelta(days=3))},
               headers=header_com_token)
    client.put(f"{FAB}/os/{primeira}/instalacao", json={"data_instalacao": str(date.today() + timedelta(days=20))},
               headers=header_com_token)
    fila = [d.numero_os for d in demandas_por_produto(db_session, [insumos["mdf"]])[insumos["mdf"]]]
    assert fila == [segunda, primeira]


# --- linha "Fábrica" de Cargos ---------------------------------------------------------------------

def test_quem_so_tem_a_os_ve_sem_custo_e_nao_orca(client, header_com_token, os_aprovada, como):
    numero = os_aprovada()
    versoes = client.get(f"{FAB}/os/{numero}/orcamentos", headers=header_com_token).json()
    v1 = versoes[0]["id"]

    como(servico=True)
    orc = client.get(f"{FAB}/orcamentos/{v1}").json()
    assert orc["custo_total"] is None
    assert orc["ambientes"][0]["moveis"][0]["custo"] is None
    assert orc["total"] == 550000                                    # o preço continua visível
    assert client.post(f"{FAB}/os/{numero}/orcamentos", json={}).status_code == 403
    assert client.post(f"{FAB}/os/{numero}/liberar-compra", json={"motivo": "xxx"}).status_code == 403
    # mas acompanha o trilho
    assert client.get(f"{FAB}/os/{numero}/trilho").status_code == 200


def test_visualizar_da_fabrica_libera_o_custo(client, header_com_token, os_aprovada, como):
    numero = os_aprovada()
    v1 = client.get(f"{FAB}/os/{numero}/orcamentos", headers=header_com_token).json()[0]["id"]
    como(servico=True, fabrica=True, view_fabrica=True)
    assert client.get(f"{FAB}/orcamentos/{v1}").json()["custo_total"] == 25946 + 528 + 51892 + 3000
