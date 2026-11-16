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


# --- Cancelar pela OS (O1 de docs/nfe-cfop-e-notas-da-os-plano.md) ------------

def test_nfse_autorizada_pode_cancelar_sem_prazo_nosso(client, loja, servico, db_session, plataforma):
    numero = _criar_os(client, loja, db_session, [_item_servico(servico)])
    client.post(f"{NFSE}/os/{numero}/emitir", headers=loja)

    [doc] = client.get(f"{OS_URL}/{numero}/notas-fiscais", headers=loja).json()["servico"]["documentos"]

    assert doc["pode_cancelar"] is True
    assert doc["cancelar_ate"] is None                   # o prazo é do município


def _nfe_da_os(db_session, numero, horas_atras):
    from datetime import datetime, timedelta, timezone

    from app.db.models.documento_fiscal import DocumentoFiscal

    os_obj = db_session.query(OrdemServico).filter_by(numero_os=numero).one()
    db_session.add(DocumentoFiscal(
        tipo_documento="NFE", origem_tipo="OS", origem_id=os_obj.id, origem_numero_os=numero,
        status="AUTORIZADA", numero_documento=11, serie=1, ref_api=f"os-{numero}", idempotency_key="k-1",
        ambiente_emissao=2, valor_total=5000,
        data_autorizacao=datetime.now(timezone.utc) - timedelta(hours=horas_atras),
    ))
    db_session.commit()


def test_nfe_dentro_das_24h_pode_cancelar_e_diz_ate_quando(client, loja, servico, db_session, licenca):
    licenca("NFE", "NFSE")
    numero = _criar_os(client, loja, db_session, [_peca()])
    _nfe_da_os(db_session, numero, horas_atras=1)

    doc = client.get(f"{OS_URL}/{numero}/notas-fiscais", headers=loja).json()["pecas"]["documento"]

    assert doc["pode_cancelar"] is True
    assert doc["cancelar_ate"]


def test_nfe_passadas_24h_nao_cancela_mais(client, loja, servico, db_session, licenca):
    licenca("NFE", "NFSE")
    numero = _criar_os(client, loja, db_session, [_peca()])
    _nfe_da_os(db_session, numero, horas_atras=25)

    doc = client.get(f"{OS_URL}/{numero}/notas-fiscais", headers=loja).json()["pecas"]["documento"]

    assert doc["pode_cancelar"] is False


# --- Mandar a nota ao cliente (O2) ---------------------------------------------

def test_whatsapp_da_nfse_leva_numero_link_publico_e_codigo(client, loja, servico, db_session, plataforma):
    from app.db.models.cliente import Cliente

    numero = _criar_os(client, loja, db_session, [_item_servico(servico)])
    db_session.query(Cliente).update({"celular": "88999998888"})
    db_session.commit()
    client.post(f"{NFSE}/os/{numero}/emitir", headers=loja)
    [doc] = client.get(f"{OS_URL}/{numero}/notas-fiscais", headers=loja).json()["servico"]["documentos"]

    r = client.get(f"{OS_URL}/{numero}/notas-fiscais/{doc['id']}/whatsapp", headers=loja)

    assert r.status_code == 200, r.text
    m = r.json()
    assert m["telefone"] == "5588999998888"
    assert m["texto"].startswith("Olá, Maria! Segue a NFS-e nº 74798 da " + numero)
    # A consulta no portal vence o PDF da emissora: abre sem login e não expira.
    assert "Nota no portal: https://www.nfse.gov.br/consultapublica?chave=1" in m["texto"]
    assert "danfse.pdf" not in m["texto"]
    assert "Código de verificação: ABC123" in m["texto"]


def test_whatsapp_da_nfe_leva_a_chave_e_nunca_o_link_da_plataforma(client, loja, servico, db_session, licenca):
    from app.db.models.documento_fiscal import DocumentoFiscal

    licenca("NFE", "NFSE")
    numero = _criar_os(client, loja, db_session, [_peca()])
    _nfe_da_os(db_session, numero, horas_atras=1)
    doc = db_session.query(DocumentoFiscal).one()
    doc.chave_acesso = "2" * 44
    doc.url_pdf = "https://api.startbig.com.br/erp/fiscal/danfe/11.pdf"
    db_session.commit()

    m = client.get(f"{OS_URL}/{numero}/notas-fiscais/{doc.id}/whatsapp", headers=loja).json()

    assert f"Chave de acesso: {'2' * 44}" in m["texto"]
    assert "api.startbig.com.br" not in m["texto"]           # o cliente cairia num login
    assert m["telefone"] is None                             # sem celular: a tela copia o texto


def test_whatsapp_de_nota_nao_autorizada_ou_de_outra_os(client, loja, servico, db_session, licenca):
    from app.db.models.documento_fiscal import DocumentoFiscal

    licenca("NFE", "NFSE")
    numero = _criar_os(client, loja, db_session, [_peca()])
    _nfe_da_os(db_session, numero, horas_atras=1)
    doc = db_session.query(DocumentoFiscal).one()

    assert client.get(f"{OS_URL}/OS-2099-999999/notas-fiscais/{doc.id}/whatsapp", headers=loja).status_code == 404
    doc.status = "REJEITADA"
    db_session.commit()
    assert client.get(f"{OS_URL}/{numero}/notas-fiscais/{doc.id}/whatsapp", headers=loja).status_code == 422
