# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/test_os_notas.py
# DESCRICAO: "Notas desta OS" (M5 de docs/nfse-melhorias-plano.md): pecas ->
#            NF-e, servico -> NFS-e, com o valor de cada lado e a situacao.
#            Nota so sai quando o cliente pede: "nao emitida" e normal.
# ---------------------------------------------------------------------------

from app.db.models.ordem_servico import OrdemServico

from test.api.v1.test_nfse_os import (  # noqa: F401
    NFSE, OS_URL, _criar_os, _item_servico, client, licenca, loja, plataforma, servico,
)


def _peca(valor=5000):
    return {"tipo": "PRODUTO", "nome": "Cartucho", "unidade_medida": "UN", "quantidade": 1, "valor_unitario": valor}


def test_os_com_peca_e_servico_divide_os_valores_com_o_desconto(client, loja, servico, db_session, licenca):
    licenca("NFE", "NFSE")
    numero = _criar_os(client, loja, db_session, [_item_servico(servico, valor=15000), _peca(5000)], desconto=2000)

    r = client.get(f"{OS_URL}/{numero}/notas-fiscais", headers=loja)

    assert r.status_code == 200, r.text
    n = r.json()
    assert (n["pecas"]["tem"], n["servico"]["tem"]) == (True, True)
    # 2000 de desconto na proporção 15000/20000: 1500 no serviço, 500 nas peças.
    assert (n["servico"]["valor"], n["pecas"]["valor"]) == (13500, 4500)
    assert n["pecas"]["documento"] is None and n["servico"]["documentos"] == []
    assert (n["pecas"]["modulo"], n["servico"]["modulo"]) == (True, True)


def test_so_servico_e_nfse_emitida_aparece(client, loja, servico, db_session, plataforma):
    numero = _criar_os(client, loja, db_session, [_item_servico(servico)])
    client.post(f"{NFSE}/os/{numero}/emitir", headers=loja)

    n = client.get(f"{OS_URL}/{numero}/notas-fiscais", headers=loja).json()

    assert n["pecas"]["tem"] is False
    assert n["pecas"]["modulo"] is False                 # a loja do teste só tem NFSE
    [doc] = n["servico"]["documentos"]
    assert (doc["status"], doc["numero"]) == ("AUTORIZADA", 74798)


def test_os_inexistente_e_404(client, loja):
    assert client.get(f"{OS_URL}/OS-2099-999999/notas-fiscais", headers=loja).status_code == 404
