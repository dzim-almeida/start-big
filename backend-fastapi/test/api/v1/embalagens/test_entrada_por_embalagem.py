# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/embalagens/test_entrada_por_embalagem.py
# DESCRIÇÃO: Entrada de estoque por embalagem (plano de embalagens, fase 2).
# ---------------------------------------------------------------------------

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.estoque import Estoque
from app.db.models.produto import Produto


@pytest.fixture
def cerveja(client: TestClient, db_session: Session, header_com_token) -> dict:
    produto = Produto(nome="Cerveja Lata 350ml", codigo_produto="CERV-350", unidade_medida="UN", ativo=True)
    produto.estoque = Estoque(quantidade=10, valor_varejo=450, custo_medio=300)
    db_session.add(produto)
    db_session.commit()
    embalagens = client.put(
        f"/api/v1/produtos/{produto.id}/embalagens",
        json={"embalagens": [
            {"sigla": "FD", "fator": 12},
            {"sigla": "CX", "fator": 24},
            {"sigla": "PCT", "fator": 6, "usa_na_entrada": False},
        ]},
        headers=header_com_token,
    ).json()
    return {"id": produto.id, **{e["sigla"]: e["id"] for e in embalagens}}


def entrar(client, headers, produto_id, **dados):
    return client.post(f"/api/v1/produtos/{produto_id}/movimentacoes", json={"tipo": "ENTRADA", **dados}, headers=headers)


def test_tres_caixas_viram_72_unidades_com_custo_por_unidade(client: TestClient, header_com_token, cerveja):
    r = entrar(client, header_com_token, cerveja["id"], quantidade=3, custo_unitario=12000, embalagem_id=cerveja["CX"])
    assert r.status_code == 201, r.text
    mov = r.json()
    # O estoque e o custo ficam SEMPRE na unidade; a embalagem é o registro de como entrou.
    assert mov["quantidade"] == 72 and mov["custo_unitario"] == 500
    assert (mov["embalagem_sigla"], mov["embalagem_fator"], mov["quantidade_embalagem"]) == ("CX", 24, 3)
    assert mov["quantidade_posterior"] == 82

    produto = client.get(f"/api/v1/produtos/{cerveja['id']}", headers=header_com_token).json()
    assert produto["estoque"]["quantidade"] == 82
    # Custo médio: (10 × 3,00 + 72 × 5,00) / 82 = 4,76
    assert produto["estoque"]["custo_medio"] == 476


def test_entrada_em_unidade_continua_igual(client: TestClient, header_com_token, cerveja):
    mov = entrar(client, header_com_token, cerveja["id"], quantidade=5, custo_unitario=320).json()
    assert mov["quantidade"] == 5 and mov["custo_unitario"] == 320
    assert mov["embalagem_id"] is None and mov["embalagem_sigla"] is None


def test_embalagem_so_vale_na_entrada(client: TestClient, header_com_token, cerveja):
    r = client.post(
        f"/api/v1/produtos/{cerveja['id']}/movimentacoes",
        json={"tipo": "SAIDA", "quantidade": 1, "embalagem_id": cerveja["FD"]},
        headers=header_com_token,
    )
    assert r.status_code == 422 and "só vale na entrada" in r.text


def test_embalagem_sem_uso_na_entrada_ou_de_outro_produto_e_recusada(client: TestClient, header_com_token, cerveja):
    assert entrar(client, header_com_token, cerveja["id"], quantidade=1, embalagem_id=cerveja["PCT"]).status_code == 422
    assert entrar(client, header_com_token, cerveja["id"], quantidade=1, embalagem_id=99999).status_code == 422


def test_quantidade_quebrada_de_embalagem_e_recusada(client: TestClient, header_com_token, cerveja):
    assert entrar(client, header_com_token, cerveja["id"], quantidade=1.5, embalagem_id=cerveja["FD"]).status_code == 422
