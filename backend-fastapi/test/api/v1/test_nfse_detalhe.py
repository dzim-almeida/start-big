# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/test_nfse_detalhe.py
# DESCRICAO: A gaveta de detalhe da NFS-e (pedido do Alan em 29/10/2026): o
#            motivo inteiro, o que fazer e as tentativas anteriores.
# ---------------------------------------------------------------------------

from test.api.v1.test_nfse_os import (  # noqa: F401
    NFSE, _criar_os, _item_servico, client, licenca, loja, plataforma, servico,
)

MOTIVO = "Empresa não habilitada para emissão de NFSe no ambiente de produção"


def test_recusa_mostra_o_motivo_inteiro_a_dica_e_a_tentativa_anterior(client, loja, servico, db_session, plataforma):
    numero = _criar_os(client, loja, db_session, [_item_servico(servico, valor=8000)])
    plataforma.resposta = {"status": "REJEITADA", "mensagem_sefaz": MOTIVO}
    primeira = client.post(f"{NFSE}/os/{numero}/emitir", headers=loja).json()
    segunda = client.post(f"{NFSE}/os/{numero}/emitir", headers=loja).json()

    r = client.get(f"{NFSE}/documentos/{segunda['documento_id']}", headers=loja)

    assert r.status_code == 200, r.text
    d = r.json()
    assert d["motivo"] == MOTIVO
    assert "suporte StartBig" in d["dica"]
    assert d["numero_os"] == numero and d["valor_total"] == 8000
    assert d["itens"][0]["descricao"] == "Formatacao e backup"
    assert [t["id"] for t in d["tentativas_anteriores"]] == [primeira["documento_id"]]


def test_autorizada_nao_tem_dica(client, loja, servico, db_session, plataforma):
    numero = _criar_os(client, loja, db_session, [_item_servico(servico)])
    doc = client.post(f"{NFSE}/os/{numero}/emitir", headers=loja).json()
    d = client.get(f"{NFSE}/documentos/{doc['documento_id']}", headers=loja).json()
    assert (d["status"], d["dica"], d["codigo_verificacao"]) == ("AUTORIZADA", None, "ABC123")


def test_documento_que_nao_e_nfse_e_404(client, loja):
    assert client.get(f"{NFSE}/documentos/999999", headers=loja).status_code == 404
