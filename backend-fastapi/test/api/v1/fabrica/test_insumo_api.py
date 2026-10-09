# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/fabrica/test_insumo_api.py
# DESCRIÇÃO: O produto como insumo da fábrica (docs/marcenaria-fabrica-plano.md, F1).
#
# O que não pode errar: só a marcenaria enxerga; desligar limpa tudo; o
# cadastro do produto (GET/PUT de /produtos) não muda para ninguém (F12).
# ---------------------------------------------------------------------------

import pytest

from app.db.models.produto import Produto

CHAPA_MM2 = 2750 * 1850


def url(produto_id: int) -> str:
    return f"/api/v1/fabrica/produtos/{produto_id}/insumo"


def gravar_chapa(client, headers, produto_id):
    return client.put(
        url(produto_id),
        json={"unidade_consumo": "M2", "consumo_por_unidade": CHAPA_MM2, "sofre_perda": True},
        headers=headers,
    )


# --- trava do segmento ----------------------------------------------------------

@pytest.mark.parametrize("valor", ["oficina_mecanica", "assistencia_tecnica", "serigrafia", "pdv", None])
def test_fora_da_marcenaria_nao_existe(client, header_com_token, segmento, chapa, valor):
    segmento(valor)
    r = client.get(url(chapa), headers=header_com_token)
    assert r.status_code == 403
    assert r.json()["detail"]["codigo"] == "SEGMENTO_SEM_FABRICA"
    assert gravar_chapa(client, header_com_token, chapa).status_code == 403


def test_sem_permissao_de_produto_nao_acessa(client, marcenaria, chapa, como):
    como(venda=True)
    assert client.get(url(chapa)).status_code == 403


# --- ler e gravar ----------------------------------------------------------------

def test_produto_comum_nasce_sem_insumo(client, header_com_token, marcenaria, chapa):
    r = client.get(url(chapa), headers=header_com_token)
    assert r.status_code == 200
    assert r.json() == {
        "produto_id": chapa,
        "unidade_medida": "CH",
        "unidade_consumo": None,
        "consumo_por_unidade": None,
        "sofre_perda": False,
    }


def test_grava_a_chapa_em_m2(client, header_com_token, marcenaria, chapa, db_session):
    r = gravar_chapa(client, header_com_token, chapa)
    assert r.status_code == 200, r.text
    assert r.json()["consumo_por_unidade"] == CHAPA_MM2
    db_session.expire_all()
    produto = db_session.get(Produto, chapa)
    assert (produto.unidade_consumo, produto.consumo_por_unidade, produto.sofre_perda) == ("M2", CHAPA_MM2, True)


def test_desligar_limpa_rendimento_e_perda(client, header_com_token, marcenaria, chapa):
    gravar_chapa(client, header_com_token, chapa)
    r = client.put(
        url(chapa),
        json={"unidade_consumo": None, "consumo_por_unidade": 999, "sofre_perda": True},
        headers=header_com_token,
    )
    assert r.status_code == 200
    assert (r.json()["consumo_por_unidade"], r.json()["sofre_perda"]) == (None, False)


@pytest.mark.parametrize("corpo", [
    {"unidade_consumo": "M2"},                                  # sem rendimento
    {"unidade_consumo": "M2", "consumo_por_unidade": 0},
    {"unidade_consumo": "KG", "consumo_por_unidade": 10},       # unidade que não existe
    {"unidade_consumo": "M", "consumo_por_unidade": 2_147_483_648},
])
def test_dados_invalidos_sao_recusados(client, header_com_token, marcenaria, chapa, corpo):
    assert client.put(url(chapa), json=corpo, headers=header_com_token).status_code == 422


def test_produto_inexistente_e_404(client, header_com_token, marcenaria):
    assert client.get(url(99999), headers=header_com_token).status_code == 404


# --- não-regressão (F12) -----------------------------------------------------------

def test_cadastro_do_produto_nao_muda(client, header_com_token, marcenaria, chapa):
    antes = client.get(f"/api/v1/produtos/{chapa}", headers=header_com_token).json()
    gravar_chapa(client, header_com_token, chapa)
    depois = client.get(f"/api/v1/produtos/{chapa}", headers=header_com_token).json()
    # Desde a Spec 04A da marcenaria, `sofre_perda` FAZ PARTE do cadastro do
    # produto (de propósito), então a resposta mostra o valor que esta rota
    # gravou. O que este teste protege continua: os campos de insumo da fábrica
    # (`unidade_consumo`, `consumo_por_unidade`) não vazam para o cadastro.
    sem_perda = lambda produto: {k: v for k, v in produto.items() if k != "sofre_perda"}  # noqa: E731
    assert sem_perda(antes) == sem_perda(depois)
    assert depois["sofre_perda"] is True
    assert "unidade_consumo" not in depois
    assert "consumo_por_unidade" not in depois

    # e editar o produto pelo cadastro de sempre não apaga o insumo
    r = client.put(f"/api/v1/produtos/{chapa}", json={"nome": "MDF Branco TX 15mm"}, headers=header_com_token)
    assert r.status_code == 200, r.text
    assert client.get(url(chapa), headers=header_com_token).json()["consumo_por_unidade"] == CHAPA_MM2
