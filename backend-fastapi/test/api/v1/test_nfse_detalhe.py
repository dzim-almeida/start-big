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


class _Emissora:
    def baixar_pdf(self, caminho):
        return b"%PDF-1.4 danfse"

    def baixar_xml(self, caminho):
        return "<NFSe/>"


def test_danfse_e_xml_saem_pela_rota_da_nfse_so_com_o_modulo_nfse(client, loja, servico, db_session, plataforma, monkeypatch):
    """Pedido do Alan (30/10): baixar PDF e XML como na NF-e. O MEI só tem a
    NFSE, e as rotas da NF-e exigem o módulo NFE -- daí as rotas próprias."""
    from app.api.v1.endpoints import fiscal_documentos
    from app.services.fiscal.documentos import arquivos

    monkeypatch.setattr(fiscal_documentos, "_cliente_fiscal", lambda *a, **k: _Emissora())
    monkeypatch.setattr(arquivos, "guardar_pdf", lambda *a, **k: None)   # nada no disco real
    monkeypatch.setattr(arquivos, "guardar_xml", lambda *a, **k: None)
    plataforma.resposta = {**plataforma.resposta, "url_xml": "https://homologacao.focusnfe.com.br/arquivos/nfse.xml"}

    numero = _criar_os(client, loja, db_session, [_item_servico(servico)])
    doc_id = client.post(f"{NFSE}/os/{numero}/emitir", headers=loja).json()["documento_id"]

    pdf = client.get(f"{NFSE}/documentos/{doc_id}/pdf", headers=loja)
    xml = client.get(f"{NFSE}/documentos/{doc_id}/xml", headers=loja)
    assert (pdf.status_code, pdf.content) == (200, b"%PDF-1.4 danfse")
    assert (xml.status_code, xml.text) == (200, "<NFSe/>")

    # A rota da NF-e segue barrada para quem só tem a NFSE.
    assert client.get(f"/api/v1/fiscal/documentos/{doc_id}/pdf", headers=loja).status_code == 403

    d = client.get(f"{NFSE}/documentos/{doc_id}", headers=loja).json()
    assert (d["pdf_local"], d["xml_local"]) == (False, False)


def test_arquivo_de_nfse_inexistente_e_404(client, loja):
    assert client.get(f"{NFSE}/documentos/999999/xml", headers=loja).status_code == 404


def test_tentar_de_novo_reenvia_a_ultima_recusada_e_aponta_a_anterior(client, loja, servico, db_session, plataforma):
    """Pedido do Alan (30/10): "Tentar de novo" no detalhe, como o "Reemitir" da NF-e."""
    numero = _criar_os(client, loja, db_session, [_item_servico(servico, valor=8000)])
    plataforma.resposta = {"status": "REJEITADA", "mensagem_sefaz": MOTIVO}
    recusada = client.post(f"{NFSE}/os/{numero}/emitir", headers=loja).json()["documento_id"]
    assert client.get(f"{NFSE}/documentos/{recusada}", headers=loja).json()["pode_tentar_de_novo"] is True

    plataforma.resposta = {"status": "autorizado", "numero": 24}
    r = client.post(f"{NFSE}/documentos/{recusada}/tentar-de-novo", headers=loja)

    assert r.status_code == 200, r.text
    nova = r.json()
    assert nova["documento_id"] != recusada and nova["status"] == "AUTORIZADA"
    assert nova["ref_api"].endswith("-2")
    d = client.get(f"{NFSE}/documentos/{nova['documento_id']}", headers=loja).json()
    assert [t["id"] for t in d["tentativas_anteriores"]] == [recusada]
    assert d["pode_tentar_de_novo"] is False

    # A recusada antiga já foi substituída: não tenta de novo por cima.
    assert client.get(f"{NFSE}/documentos/{recusada}", headers=loja).json()["pode_tentar_de_novo"] is False
    r = client.post(f"{NFSE}/documentos/{recusada}/tentar-de-novo", headers=loja)
    assert r.status_code == 409 and r.json()["detail"]["codigo"] == "NFSE_JA_TEM_TENTATIVA_NOVA"


def test_tentar_de_novo_so_vale_para_recusada(client, loja, servico, db_session, plataforma):
    numero = _criar_os(client, loja, db_session, [_item_servico(servico)])
    autorizada = client.post(f"{NFSE}/os/{numero}/emitir", headers=loja).json()["documento_id"]
    r = client.post(f"{NFSE}/documentos/{autorizada}/tentar-de-novo", headers=loja)
    assert r.status_code == 422 and r.json()["detail"]["codigo"] == "NFSE_NAO_RECUSADA"
    assert client.post(f"{NFSE}/documentos/999999/tentar-de-novo", headers=loja).status_code == 404
