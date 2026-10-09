# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/test_produto_sofre_perda.py
# DESCRICAO: Spec 04A da marcenaria -- `sofre_perda` no contrato do produto
#            (casos 05 a 08).
#
#            A coluna ja existia (fabrica F1); a Spec 04A so a expoe. E aditiva:
#            nenhum segmento precisa enviar, e o padrao `false` e o
#            comportamento de sempre (PR1).
# ---------------------------------------------------------------------------

import pytest
from fastapi.testclient import TestClient

from app.core.enum import MovimentacaoTipo
from app.db.models.movimentacao_estoque import MovimentacaoEstoque
from app.main import app

from test.conftest import TEST_HWID, TEST_USER_EMAIL, TEST_USER_PASSWORD

URL = "/api/v1/produtos"


@pytest.fixture
def client():
    """Cliente HTTP SEM `with`: o lifespan (create_all e migracoes no banco real
    da maquina) nao roda. O banco destes testes e o SQLite em memoria do conftest."""
    yield TestClient(app)


@pytest.fixture
def header(client, db_session, create_test_empresa) -> dict:
    """Login do usuario master da empresa de teste (sem segmento: vale para todos)."""
    r = client.post("/api/v1/auth/login", data={
        "username": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD, "hwid": TEST_HWID,
    })
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _produto(codigo: str, **extra) -> dict:
    """Corpo minimo de criacao de produto; `extra` acrescenta campos."""
    return {
        "nome": f"Produto {codigo}",
        "codigo_produto": codigo,
        "unidade_medida": "UN",
        "estoque": {"valor_varejo": 1000, "quantidade": 5},
        **extra,
    }


def test_criar_sem_o_campo_grava_false(client, header):
    """Caso 05: quem nunca ouviu falar do campo (todos os segmentos) nao muda nada."""
    r = client.post(f"{URL}/", json=_produto("SP-05"), headers=header)
    assert r.status_code == 201, r.text
    assert r.json()["sofre_perda"] is False


def test_criar_com_true_grava_true(client, header):
    """Caso 06: a chapa de MDF da marcenaria."""
    r = client.post(f"{URL}/", json=_produto("SP-06", sofre_perda=True), headers=header)
    assert r.status_code == 201, r.text
    assert r.json()["sofre_perda"] is True


def test_editar_para_true_registra_no_historico(client, header, db_session):
    """Caso 07: a mudanca aparece no historico do produto como "Sofre perda alterado"."""
    produto_id = client.post(f"{URL}/", json=_produto("SP-07"), headers=header).json()["id"]

    r = client.put(f"{URL}/{produto_id}", json={"sofre_perda": True}, headers=header)

    assert r.status_code == 200, r.text
    assert r.json()["sofre_perda"] is True
    db_session.expire_all()                                   # le o que o endpoint gravou
    edicoes = (
        db_session.query(MovimentacaoEstoque)
        .filter(MovimentacaoEstoque.produto_id == produto_id,
                MovimentacaoEstoque.tipo == MovimentacaoTipo.EDICAO_DADOS)
        .all()
    )
    assert [m.observacao for m in edicoes] == ["Sofre perda alterado"]


@pytest.mark.parametrize("corpo", [{"nome": "Chapa renomeada"}, {"sofre_perda": None}],
                         ids=["sem_o_campo", "null_explicito"])
def test_editar_sem_o_campo_mantem_o_valor(client, header, corpo):
    """Caso 08: ausente (ou null) = nao muda. O null nao pode virar erro de banco."""
    produto_id = client.post(f"{URL}/", json=_produto("SP-08", sofre_perda=True), headers=header).json()["id"]

    r = client.put(f"{URL}/{produto_id}", json=corpo, headers=header)

    assert r.status_code == 200, r.text
    assert r.json()["sofre_perda"] is True
