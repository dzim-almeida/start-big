# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/fiscal/test_perfis_tributarios_api.py
# DESCRIÇÃO: TASK005 CA-2/CA-3 — o contrato REST de /fiscal/perfis-tributarios.
# ---------------------------------------------------------------------------

import pytest
from fastapi.testclient import TestClient

from app.core.depends import get_current_user
from app.main import app

URL = "/api/v1/fiscal/perfis-tributarios"


def regra(**campos) -> dict:
    base = {"aliquota_interestadual": 1200, "aliquota_interna_destino": 1800}
    base.update(campos)
    return base


def payload(descricao="Varejo - Eletrônicos", *extras) -> dict:
    return {"descricao": descricao, "regras": [regra(), *extras]}


def _criar(client, headers, descricao="Varejo - Eletrônicos") -> dict:
    resposta = client.post(URL, json=payload(descricao), headers=headers)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def test_post_cria_e_devolve_201_com_ids(client: TestClient, header_com_token):
    resposta = client.post(URL, json=payload("Varejo", regra(uf_destino="sp", ncm_excecao="85171200")), headers=header_com_token)
    assert resposta.status_code == 201, resposta.text
    corpo = resposta.json()
    assert corpo["id"] > 0 and corpo["descricao"] == "Varejo"
    assert len(corpo["regras"]) == 2 and all(r["id"] > 0 for r in corpo["regras"])
    assert {r["uf_destino"] for r in corpo["regras"]} == {None, "SP"}
    assert corpo["data_criacao"] and corpo["data_atualizacao"]


def test_post_sem_fallback_e_422(client: TestClient, header_com_token):
    resposta = client.post(URL, json={"descricao": "Varejo", "regras": [regra(uf_destino="SP")]}, headers=header_com_token)
    assert resposta.status_code == 422
    assert "fallback" in resposta.text


def test_get_lista_enxuta_com_contagem(client: TestClient, header_com_token):
    _criar(client, header_com_token)
    client.post(URL, json=payload("Atacado", regra(uf_destino="RJ")), headers=header_com_token)

    resposta = client.get(URL, headers=header_com_token)
    assert resposta.status_code == 200, resposta.text
    lista = resposta.json()
    assert [p["descricao"] for p in lista] == ["Atacado", "Varejo - Eletrônicos"]
    assert [p["quantidade_regras"] for p in lista] == [2, 1]
    assert "regras" not in lista[0]


def test_get_por_id_devolve_perfil_completo(client: TestClient, header_com_token):
    criado = _criar(client, header_com_token)
    resposta = client.get(f"{URL}/{criado['id']}", headers=header_com_token)
    assert resposta.status_code == 200
    assert resposta.json()["regras"][0]["id"] == criado["regras"][0]["id"]


def test_put_substitui_as_regras(client: TestClient, header_com_token):
    criado = _criar(client, header_com_token)
    resposta = client.put(
        f"{URL}/{criado['id']}",
        json=payload("Renomeado", regra(uf_destino="MG", mva_st=4000, reducao_base_calculo=1000)),
        headers=header_com_token,
    )
    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    assert corpo["descricao"] == "Renomeado"
    assert sorted(r["uf_destino"] or "" for r in corpo["regras"]) == ["", "MG"]
    mg = next(r for r in corpo["regras"] if r["uf_destino"] == "MG")
    assert (mg["mva_st"], mg["reducao_base_calculo"]) == (4000, 1000)


def test_delete_devolve_204_e_some_da_lista(client: TestClient, header_com_token):
    criado = _criar(client, header_com_token)
    assert client.delete(f"{URL}/{criado['id']}", headers=header_com_token).status_code == 204
    assert client.get(f"{URL}/{criado['id']}", headers=header_com_token).status_code == 404
    assert client.get(URL, headers=header_com_token).json() == []


@pytest.mark.parametrize("metodo", ["get", "put", "delete"])
def test_id_inexistente_e_404(client: TestClient, header_com_token, metodo):
    chamada = getattr(client, metodo)
    kwargs = {"json": payload()} if metodo == "put" else {}
    assert chamada(f"{URL}/999", headers=header_com_token, **kwargs).status_code == 404


def test_sem_token_e_401(client: TestClient, header_com_token):
    assert client.get(URL).status_code == 401


def test_escrita_exige_master(client: TestClient, header_com_token):
    comum = {"sub": "1", "empresa_id": 1, "is_master": False, "usuario_id": 1}
    app.dependency_overrides[get_current_user] = lambda: comum
    try:
        assert client.post(URL, json=payload(), headers=header_com_token).status_code == 403
        assert client.get(URL, headers=header_com_token).status_code == 200  # leitura é livre
    finally:
        app.dependency_overrides.pop(get_current_user, None)
