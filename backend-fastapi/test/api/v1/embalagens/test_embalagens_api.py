# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/embalagens/test_embalagens_api.py
# DESCRIÇÃO: Embalagens do produto (docs/produto-embalagens-plano.md, fase 1).
# ---------------------------------------------------------------------------

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.gtin import codigo_interno_embalagem, gtin_valido
from app.db.models.estoque import Estoque
from app.db.models.produto import Produto


def _produto(db: Session, nome: str, sku: str, ean: str | None = None) -> Produto:
    produto = Produto(nome=nome, codigo_produto=sku, codigo_barras=ean, unidade_medida="UN", ativo=True)
    produto.estoque = Estoque(quantidade=120, valor_varejo=450)
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto


@pytest.fixture
def cerveja(db_session: Session, header_com_token) -> Produto:
    return _produto(db_session, "Cerveja Lata 350ml", "CERV-350", "7891000100103")


@pytest.fixture
def refri(db_session: Session, header_com_token) -> Produto:
    return _produto(db_session, "Refrigerante 2L", "REFRI-2L", "7894900011517")


def url(produto: Produto) -> str:
    return f"/api/v1/produtos/{produto.id}/embalagens"


FARDO = {"sigla": "fd", "descricao": "Fardo com 12", "fator": 12, "codigo_barras": "17891000100100", "preco": 4500}


def test_cria_e_devolve_na_leitura_do_produto(client: TestClient, header_com_token, cerveja):
    resposta = client.put(url(cerveja), json={"embalagens": [FARDO]}, headers=header_com_token)
    assert resposta.status_code == 200, resposta.text
    [fardo] = resposta.json()
    assert fardo["sigla"] == "FD" and fardo["fator"] == 12 and fardo["preco"] == 4500

    produto = client.get(f"/api/v1/produtos/{cerveja.id}", headers=header_com_token).json()
    assert [e["sigla"] for e in produto["embalagens"]] == ["FD"]


def test_quantidade_nao_e_fixa_e_varias_embalagens_por_produto(client: TestClient, header_com_token, cerveja):
    embalagens = [
        {"sigla": "PCT", "fator": 6},
        {"sigla": "FD", "fator": 15},
        {"sigla": "CX", "fator": 24, "desconto_bp": 500},
    ]
    resposta = client.put(url(cerveja), json={"embalagens": embalagens}, headers=header_com_token)
    assert resposta.status_code == 200, resposta.text
    # Ordenadas pelo fator.
    assert [(e["sigla"], e["fator"]) for e in resposta.json()] == [("PCT", 6), ("FD", 15), ("CX", 24)]


def test_fator_1_e_codigo_adicional_da_unidade(client: TestClient, header_com_token, cerveja):
    adicional = {"sigla": "UN", "fator": 1, "codigo_barras": "7891000100110"}
    resposta = client.put(url(cerveja), json={"embalagens": [adicional]}, headers=header_com_token)
    assert resposta.status_code == 200, resposta.text


def test_replace_all_atualiza_mantem_id_e_apaga_o_que_nao_veio(client: TestClient, header_com_token, cerveja):
    criadas = client.put(
        url(cerveja), json={"embalagens": [FARDO, {"sigla": "CX", "fator": 24}]}, headers=header_com_token
    ).json()
    fardo_id = criadas[0]["id"]
    atualizadas = client.put(
        url(cerveja),
        json={"embalagens": [{**FARDO, "id": fardo_id, "preco": 4300}]},
        headers=header_com_token,
    ).json()
    assert [(e["id"], e["preco"]) for e in atualizadas] == [(fardo_id, 4300)]


def test_codigo_unico_no_sistema_inteiro(client: TestClient, header_com_token, cerveja, refri):
    # Código de barras de OUTRO produto.
    r = client.put(url(cerveja), json={"embalagens": [{**FARDO, "codigo_barras": "7894900011517"}]}, headers=header_com_token)
    assert r.status_code == 409 and "Refrigerante 2L" in r.text

    # SKU de outro produto.
    r = client.put(url(cerveja), json={"embalagens": [{**FARDO, "codigo_barras": "REFRI-2L"}]}, headers=header_com_token)
    assert r.status_code == 409

    # O próprio código do produto.
    r = client.put(url(cerveja), json={"embalagens": [{**FARDO, "codigo_barras": "7891000100103"}]}, headers=header_com_token)
    assert r.status_code == 409 and "próprio produto" in r.text

    # Embalagem de outro produto.
    assert client.put(url(refri), json={"embalagens": [FARDO]}, headers=header_com_token).status_code == 200
    r = client.put(url(cerveja), json={"embalagens": [FARDO]}, headers=header_com_token)
    assert r.status_code == 409 and "embalagem FD" in r.text


def test_codigo_repetido_na_mesma_lista_e_preco_com_desconto_sao_422(client: TestClient, header_com_token, cerveja):
    r = client.put(url(cerveja), json={"embalagens": [FARDO, {**FARDO, "sigla": "CX", "fator": 24}]}, headers=header_com_token)
    assert r.status_code == 422
    r = client.put(url(cerveja), json={"embalagens": [{**FARDO, "desconto_bp": 500}]}, headers=header_com_token)
    assert r.status_code == 422
    r = client.put(url(cerveja), json={"embalagens": [{**FARDO, "fator": 0}]}, headers=header_com_token)
    assert r.status_code == 422


def test_gera_codigo_interno_valido_para_fardo_sem_codigo(client: TestClient, header_com_token, cerveja):
    sem_codigo = {"sigla": "FD", "fator": 12, "gerar_codigo_interno": True}
    [fardo] = client.put(url(cerveja), json={"embalagens": [sem_codigo]}, headers=header_com_token).json()
    assert fardo["codigo_barras"] == codigo_interno_embalagem(fardo["id"])
    assert fardo["codigo_barras"].startswith("29") and gtin_valido(fardo["codigo_barras"])


def test_produto_nao_pode_usar_o_codigo_de_uma_embalagem(client: TestClient, header_com_token, cerveja, refri):
    client.put(url(cerveja), json={"embalagens": [FARDO]}, headers=header_com_token)
    r = client.put(f"/api/v1/produtos/{refri.id}", json={"codigo_barras": FARDO["codigo_barras"]}, headers=header_com_token)
    assert r.status_code == 409 and "embalagem FD" in r.text


def test_produto_inexistente_e_404_e_sem_token_401(client: TestClient, header_com_token):
    assert client.get("/api/v1/produtos/9999/embalagens", headers=header_com_token).status_code == 404
    assert client.get("/api/v1/produtos/1/embalagens").status_code == 401


def test_gtin():
    assert gtin_valido("7891000100103") and gtin_valido("17891000100100")
    assert not gtin_valido("7891000100104") and not gtin_valido("ABC")
