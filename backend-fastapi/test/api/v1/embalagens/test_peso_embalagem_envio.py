# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/embalagens/test_peso_embalagem_envio.py
# DESCRIÇÃO: Peso da embalagem na etiqueta de envio (plano de embalagens, A5).
#
# A etiqueta soma `quantidade × peso` dos fardos vendidos. Só se diz "completo"
# quando toda linha é embalagem com peso: latas avulsas sem peso deixariam a
# soma menor que a caixa de verdade.
# ---------------------------------------------------------------------------

from test.api.v1.embalagens.test_venda_por_embalagem import (  # noqa: F401 — `loja` é fixture
    lancar,
    ligar_embalagens,
    loja,
    nova_venda,
)

URL_ENVIO = "/api/v1/etiquetas/envio/venda"


def pesar_fardo(client, headers, loja, gramas):
    r = client.put(f"/api/v1/produtos/{loja['produto_id']}/embalagens", json={"embalagens": [
        {"id": loja["FD"], "sigla": "FD", "fator": 12, "preco": 4800, "codigo_barras": "17891000000008",
         "peso_gramas": gramas},
    ]}, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()[0]


def test_peso_e_opcional_e_volta_no_cadastro(client, header_com_token, loja):
    assert pesar_fardo(client, header_com_token, loja, 4380)["peso_gramas"] == 4380
    assert pesar_fardo(client, header_com_token, loja, None)["peso_gramas"] is None
    r = client.put(f"/api/v1/produtos/{loja['produto_id']}/embalagens", json={"embalagens": [
        {"sigla": "FD", "fator": 12, "peso_gramas": 0},
    ]}, headers=header_com_token)
    assert r.status_code == 422


def test_etiqueta_soma_o_peso_dos_fardos(client, header_com_token, loja):
    ligar_embalagens(client, header_com_token)
    fardo = pesar_fardo(client, header_com_token, loja, 4380)

    v = nova_venda(client, header_com_token, loja)
    assert lancar(client, header_com_token, v, loja["produto_id"], 2, embalagem_id=fardo["id"]).status_code == 201
    dados = client.get(f"{URL_ENVIO}/{v}", headers=header_com_token).json()
    assert (dados["volumes_embalagens"], dados["peso_embalagens_gramas"], dados["peso_completo"]) == (2, 8760, True)

    # Com latas avulsas junto, o peso dos fardos vira só dica.
    lancar(client, header_com_token, v, loja["produto_id"], 3)
    dados = client.get(f"{URL_ENVIO}/{v}", headers=header_com_token).json()
    assert (dados["volumes_embalagens"], dados["peso_embalagens_gramas"], dados["peso_completo"]) == (2, 8760, False)


def test_venda_sem_embalagem_nao_sugere_nada(client, header_com_token, loja):
    v = nova_venda(client, header_com_token, loja)
    lancar(client, header_com_token, v, loja["produto_id"], 3)
    dados = client.get(f"{URL_ENVIO}/{v}", headers=header_com_token).json()
    assert (dados["volumes_embalagens"], dados["peso_embalagens_gramas"], dados["peso_completo"]) == (0, 0, False)
