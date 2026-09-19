# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/fiscal/test_produto_perfil_api.py
# DESCRIÇÃO: TASK006 CA-2 pela API — PUT/GET /produtos/{id}/fiscal com
#            perfil_tributario_id (fixtures sem lifespan deste diretório).
# ---------------------------------------------------------------------------

import pytest
from fastapi.testclient import TestClient

PERFIS = "/api/v1/fiscal/perfis-tributarios"


@pytest.fixture
def produto_id(client: TestClient, header_com_token) -> int:
    resposta = client.post(
        "/api/v1/produtos/",
        json={"nome": "Celular X", "codigo_produto": "CEL-1", "unidade_medida": "UN",
              "estoque": {"valor_varejo": 100000, "quantidade": 1, "valor_entrada": 50000}},
        headers=header_com_token,
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()["id"]


@pytest.fixture
def perfil_id(client: TestClient, header_com_token) -> int:
    resposta = client.post(
        PERFIS,
        json={"descricao": "Varejo", "regras": [{"aliquota_interestadual": 1200, "aliquota_interna_destino": 1800}]},
        headers=header_com_token,
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()["id"]


def _fiscal(client, headers, produto_id, corpo) -> dict:
    resposta = client.put(f"/api/v1/produtos/{produto_id}/fiscal", json=corpo, headers=headers)
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def test_vincula_desvincula_e_omitir_mantem(client, header_com_token, fiscal_settings, produto_id, perfil_id):
    assert _fiscal(client, header_com_token, produto_id, {"ncm": "85171200", "perfil_tributario_id": perfil_id})["perfil_tributario_id"] == perfil_id

    lido = client.get(f"/api/v1/produtos/{produto_id}/fiscal", headers=header_com_token).json()
    assert lido["perfil_tributario_id"] == perfil_id

    # omitir não altera
    assert _fiscal(client, header_com_token, produto_id, {"cfop_padrao": "5102"})["perfil_tributario_id"] == perfil_id
    # null desvincula
    assert _fiscal(client, header_com_token, produto_id, {"perfil_tributario_id": None})["perfil_tributario_id"] is None


def test_perfil_inexistente_e_422_com_codigo(client, header_com_token, fiscal_settings, produto_id):
    resposta = client.put(
        f"/api/v1/produtos/{produto_id}/fiscal", json={"perfil_tributario_id": 999}, headers=header_com_token,
    )
    assert resposta.status_code == 422, resposta.text
    assert resposta.json()["detail"]["codigo"] == "PERFIL_TRIBUTARIO_INVALIDO"


def test_excluir_perfil_vinculado_e_409(client, header_com_token, fiscal_settings, produto_id, perfil_id):
    _fiscal(client, header_com_token, produto_id, {"perfil_tributario_id": perfil_id})
    resposta = client.delete(f"{PERFIS}/{perfil_id}", headers=header_com_token)
    assert resposta.status_code == 409, resposta.text
    assert resposta.json()["detail"]["codigo"] == "PERFIL_EM_USO"
    assert "Celular X" in resposta.json()["detail"]["mensagem"]
