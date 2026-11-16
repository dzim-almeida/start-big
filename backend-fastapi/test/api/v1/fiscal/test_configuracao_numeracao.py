# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/fiscal/test_configuracao_numeracao.py
# DESCRIÇÃO: TASK001 — a confirmação da numeração vista pela API.
# ---------------------------------------------------------------------------

from fastapi.testclient import TestClient

URL = "/api/v1/fiscal/configuracao"


def test_get_configuracao_expoe_numeracao_confirmada_false_por_padrao(
    client: TestClient, header_com_token, fiscal_settings
):
    resposta = client.get(URL, headers=header_com_token)
    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["numeracao_confirmada"] is False


def test_put_com_numeracao_confirmada_true_destrava(
    client: TestClient, header_com_token, fiscal_settings
):
    resposta = client.put(URL, json={"numeracao_confirmada": True}, headers=header_com_token)
    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["numeracao_confirmada"] is True

    # Sobrevive à requisição (não fica só na sessão aberta).
    assert client.get(URL, headers=header_com_token).json()["numeracao_confirmada"] is True


def test_put_alterando_ultimo_numero_nfe_auto_confirma(
    client: TestClient, header_com_token, fiscal_settings
):
    resposta = client.put(URL, json={"ultimo_numero_nfe": 1520}, headers=header_com_token)
    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    assert corpo["ultimo_numero_nfe"] == 1520
    assert corpo["numeracao_confirmada"] is True


def test_put_sem_tocar_na_numeracao_nao_confirma(
    client: TestClient, header_com_token, fiscal_settings
):
    resposta = client.put(URL, json={"ambiente_emissao": 1}, headers=header_com_token)
    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["numeracao_confirmada"] is False
