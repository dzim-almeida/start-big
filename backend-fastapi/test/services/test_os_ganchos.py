# ---------------------------------------------------------------------------
# ARQUIVO: test/services/test_os_ganchos.py
# DESCRICAO: ⚠️ Ganchos do ciclo de vida da OS (Spec 09A da marcenaria, §6.1 e
#            §7; casos 13, 14, 22 e 23), num segmento EM PRODUCAO (informatica).
#
#            Sem gancho, a OS se comporta como sempre; com gancho, ele roda
#            dentro da transacao (falhou = nada gravado) e recebe o status
#            anterior no cancelamento.
# ---------------------------------------------------------------------------

import pytest
from fastapi.testclient import TestClient

from app.db.models.conta_pagar import ContaPagar
from app.db.models.ordem_servico import OrdemServico
from app.main import app
from app.services import ordem_servico_ganchos as ganchos_os

from test.apoio_orcamento_marcenaria import _criar_loja

OS_URL = "/api/v1/ordens-servico"


@pytest.fixture
def client():
    """SEM `with`: o lifespan nao roda (nada no banco real da maquina)."""
    yield TestClient(app)


@pytest.fixture
def loja(client, db_session) -> dict:
    return _criar_loja(client, "assistencia_tecnica")


@pytest.fixture
def nova_os(client, loja):
    """Cria uma OS de informatica de R$ 350,00 e devolve o numero."""
    cliente = client.post("/api/v1/clientes/cliente_pf", json={"nome": "Seu Jorge", "cpf": "11144477735", "tipo": "PF"},
                          headers=loja).json()["id"]

    def _nova() -> str:
        r = client.post(f"{OS_URL}/", json={
            "cliente_id": cliente, "prioridade": "NORMAL", "defeito_relatado": "Tela quebrada", "dados_adicionais": {},
            "objeto": {"marca": "Apple", "modelo": "iPhone 11", "numero_serie": "ABC12345"},
            "itens": [{"tipo": "SERVICO", "nome": "Troca de tela", "unidade_medida": "UN", "quantidade": 1,
                       "valor_unitario": 35000}],
        }, headers=loja)
        assert r.status_code == 201, r.text
        return r.json()["numero_os"]
    return _nova


@pytest.fixture
def pix(client, loja) -> int:
    return client.post("/api/v1/formas-pagamento/", json={"nome": "PIX", "ativo": True}, headers=loja).json()["id"]


def _finalizar(client, loja, numero, pix):
    return client.put(f"{OS_URL}/{numero}/finalizar", json={
        "situacao_equipamento": "REPARADO", "pagamentos": [{"forma_pagamento_id": pix, "valor": 35000}],
    }, headers=loja)


def _resumo(os_: dict) -> tuple:
    """O que precisa ser IGUAL com e sem ganchos (sem ids, numeros e datas)."""
    return (os_["status"], os_["valor_bruto"], os_["valor_total"], os_["valor_entrada"],
            [(p["valor"], p["forma_pagamento"]["nome"]) for p in os_["pagamentos"]],
            [(i["nome"], i["valor_total"], i["origem"]) for i in os_["itens"]])


def test_14_sem_ganchos_e_com_ganchos_a_os_fica_igual(client, loja, nova_os, pix, monkeypatch, db_session):
    """Os ganchos da marcenaria estao registrados (api.py); numa OS de informatica eles saem na hora."""
    assert ganchos_os.ao_finalizar, "a marcenaria registra o RT na finalizacao"
    com = nova_os()
    r_com = _finalizar(client, loja, com, pix)

    for lista in ("ao_finalizar", "ao_reabrir", "ao_cancelar"):
        monkeypatch.setattr(ganchos_os, lista, [])             # o sistema de antes da Spec 09A
    sem = nova_os()
    r_sem = _finalizar(client, loja, sem, pix)

    assert r_com.status_code == r_sem.status_code == 200
    assert _resumo(r_com.json()) == _resumo(r_sem.json())
    assert db_session.query(ContaPagar).count() == 0            # nenhuma conta de RT


def test_14b_reabrir_e_cancelar_iguais(client, loja, nova_os, pix, monkeypatch):
    def _ciclo() -> tuple:
        numero = nova_os()
        assert _finalizar(client, loja, numero, pix).status_code == 200
        reaberta = client.put(f"{OS_URL}/{numero}/reabrir", json={"cliente_pagou": True}, headers=loja)
        cancelada = client.put(f"{OS_URL}/{numero}/cancelar", json={"motivo": "teste"}, headers=loja)
        return reaberta.status_code, _resumo(reaberta.json()), cancelada.status_code, _resumo(cancelada.json())

    com = _ciclo()
    for lista in ("ao_finalizar", "ao_reabrir", "ao_cancelar"):
        monkeypatch.setattr(ganchos_os, lista, [])
    assert _ciclo() == com


def test_13_gancho_que_falha_desfaz_a_finalizacao(client, loja, nova_os, pix, monkeypatch, db_session):
    def _quebra(db, os_, usuario, contexto):
        raise RuntimeError("gancho com defeito")
    monkeypatch.setattr(ganchos_os, "ao_finalizar", [_quebra])
    numero = nova_os()

    try:
        r = _finalizar(client, loja, numero, pix)
        assert r.status_code == 500
    except RuntimeError:
        pass                                                    # o TestClient pode repassar a excecao

    db_session.expire_all()
    os_ = db_session.query(OrdemServico).filter_by(numero_os=numero).one()
    assert os_.status.value == "ABERTA" and list(os_.pagamentos) == []


def test_22_23_cancelamento_recebe_o_status_anterior(client, loja, nova_os, pix, monkeypatch):
    vistos = []
    monkeypatch.setattr(ganchos_os, "ao_cancelar", [lambda db, os_, usuario, contexto: vistos.append(contexto)])

    aberta = nova_os()
    client.put(f"{OS_URL}/{aberta}/cancelar", json={"motivo": "x"}, headers=loja)
    finalizada = nova_os()
    _finalizar(client, loja, finalizada, pix)
    client.put(f"{OS_URL}/{finalizada}/cancelar", json={"motivo": "x"}, headers=loja)

    assert vistos == [{"status_anterior": "ABERTA"}, {"status_anterior": "FINALIZADA"}]


def test_registrar_nao_duplica():
    lista = []
    gancho = lambda *a: None  # noqa: E731
    ganchos_os.registrar(lista, gancho)
    ganchos_os.registrar(lista, gancho)
    assert lista == [gancho]
