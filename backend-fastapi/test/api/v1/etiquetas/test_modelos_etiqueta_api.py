# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/etiquetas/test_modelos_etiqueta_api.py
# DESCRIÇÃO: O contrato REST de /etiquetas/modelos (docs/etiquetas-plano.md, fase 1).
# ---------------------------------------------------------------------------

from fastapi.testclient import TestClient

URL = "/api/v1/etiquetas/modelos"


def definicao_bobina(largura=50, altura=30, **pagina) -> dict:
    return {
        "pagina": {"tipo": "bobina", "largura_mm": largura, "altura_mm": altura, **pagina},
        "elementos": [
            {"tipo": "texto", "x": 2, "y": 2, "w": 46, "h": 6, "campo": "produto.nome", "fonte_pt": 8},
            {"tipo": "barras", "x": 2, "y": 14, "w": 46, "h": 12, "campo": "produto.codigo_barras", "simbologia": "auto"},
        ],
    }


def definicao_pimaco() -> dict:
    # Pimaco 6180: 3 colunas × 10 linhas de 66,7 × 25,4 mm numa folha CARTA (não A4).
    return {
        "pagina": {
            "tipo": "folha", "largura_mm": 66.7, "altura_mm": 25.4, "colunas": 3,
            "espaco_colunas_mm": 3.2, "espaco_linhas_mm": 0, "margem_esq_mm": 4.8, "margem_topo_mm": 12.7,
            "folha": {"largura_mm": 215.9, "altura_mm": 279.4, "linhas": 10},
        },
        "elementos": [{"tipo": "texto", "x": 2, "y": 2, "w": 60, "h": 6, "campo": "produto.nome"}],
    }


def _criar(client, headers, nome="Gôndola 50x30", definicao=None) -> dict:
    resposta = client.post(URL, json={"nome": nome, "definicao": definicao or definicao_bobina()}, headers=headers)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def test_post_cria_e_devolve_a_definicao_intacta(client: TestClient, header_com_token):
    corpo = _criar(client, header_com_token)
    assert corpo["id"] > 0 and corpo["nome"] == "Gôndola 50x30" and corpo["fonte"] == "produto"
    # Campos do renderizador (campo, fonte_pt, simbologia) passam sem ser descartados.
    barras = corpo["definicao"]["elementos"][1]
    assert barras["simbologia"] == "auto" and barras["campo"] == "produto.codigo_barras"
    assert corpo["definicao"]["elementos"][0]["fonte_pt"] == 8
    assert corpo["definicao"]["layout_auto"] is None


def test_layout_auto_volta_igual(client: TestClient, header_com_token):
    definicao = definicao_bobina() | {"layout_auto": {"campos": ["nome", "barras"]}}
    corpo = _criar(client, header_com_token, definicao=definicao)
    assert corpo["definicao"]["layout_auto"] == {"campos": ["nome", "barras"]}


def test_post_folha_pimaco_valida(client: TestClient, header_com_token):
    corpo = _criar(client, header_com_token, "Pimaco 6180", definicao_pimaco())
    assert corpo["definicao"]["pagina"]["folha"]["linhas"] == 10


def test_colunas_que_nao_cabem_na_folha_sao_422(client: TestClient, header_com_token):
    definicao = definicao_pimaco()
    definicao["pagina"]["colunas"] = 4
    resposta = client.post(URL, json={"nome": "Torta", "definicao": definicao}, headers=header_com_token)
    assert resposta.status_code == 422
    assert "colunas" in resposta.text


def test_folha_sem_medidas_e_422(client: TestClient, header_com_token):
    definicao = definicao_pimaco()
    definicao["pagina"]["folha"] = None
    resposta = client.post(URL, json={"nome": "Sem folha", "definicao": definicao}, headers=header_com_token)
    assert resposta.status_code == 422


def test_elemento_fora_da_etiqueta_e_422(client: TestClient, header_com_token):
    definicao = definicao_bobina()
    definicao["elementos"][0]["x"] = 40  # 40 + 46 > 50
    resposta = client.post(URL, json={"nome": "Vazado", "definicao": definicao}, headers=header_com_token)
    assert resposta.status_code == 422
    assert "sai da etiqueta" in resposta.text


def test_nome_repetido_e_409_sem_diferenciar_maiusculas_nem_espacos(client: TestClient, header_com_token):
    _criar(client, header_com_token, "Gôndola Grande")
    # Espaços nas pontas também não contam. (O lower() do SQLite só cobre ASCII:
    # "Ô" x "ô" não seria pego — por isso o teste varia só letras sem acento.)
    resposta = client.post(URL, json={"nome": "  gôndola GRANDE ", "definicao": definicao_bobina()}, headers=header_com_token)
    assert resposta.status_code == 409, resposta.text


def test_get_lista_em_ordem_de_nome(client: TestClient, header_com_token):
    _criar(client, header_com_token, "Rolo 40x25", definicao_bobina(40, 25) | {"elementos": []})
    _criar(client, header_com_token, "Gôndola")
    resposta = client.get(URL, headers=header_com_token)
    assert resposta.status_code == 200
    assert [m["nome"] for m in resposta.json()] == ["Gôndola", "Rolo 40x25"]


def test_put_substitui_e_pode_manter_o_proprio_nome(client: TestClient, header_com_token):
    criado = _criar(client, header_com_token)
    nova = definicao_bobina(60, 40)
    resposta = client.put(f"{URL}/{criado['id']}", json={"nome": criado["nome"], "definicao": nova}, headers=header_com_token)
    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["definicao"]["pagina"]["largura_mm"] == 60


def test_put_para_nome_de_outro_modelo_e_409(client: TestClient, header_com_token):
    _criar(client, header_com_token, "A")
    b = _criar(client, header_com_token, "B")
    resposta = client.put(f"{URL}/{b['id']}", json={"nome": "A", "definicao": definicao_bobina()}, headers=header_com_token)
    assert resposta.status_code == 409


def test_delete_e_depois_404(client: TestClient, header_com_token):
    criado = _criar(client, header_com_token)
    assert client.delete(f"{URL}/{criado['id']}", headers=header_com_token).status_code == 204
    assert client.get(f"{URL}/{criado['id']}", headers=header_com_token).status_code == 404


def test_sem_token_e_401(client: TestClient):
    assert client.get(URL).status_code == 401
