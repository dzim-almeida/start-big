# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/test_nfse_substituicao.py
# DESCRICAO: Substituir a NFS-e autorizada (O4 de docs/nfe-cfop-e-notas-da-os-
#            plano.md): a nova sai com os campos da DPS e a antiga so cai
#            quando a nova e autorizada.
# ---------------------------------------------------------------------------

from app.db.models.documento_fiscal import DocumentoFiscal

from test.api.v1.test_nfse_os import (  # noqa: F401
    NFSE, OS_URL, _criar_os, _item_servico, client, licenca, loja, plataforma, servico,
)

CHAVE_ANTIGA = "2305506" + "1" * 43
MOTIVO = {"motivo": "99", "descricao": "Valor do servico lancado errado na OS"}


def _autorizada(client, loja, db_session, plataforma, servico) -> tuple[str, int]:
    numero = _criar_os(client, loja, db_session, [_item_servico(servico)])
    plataforma.resposta = {**plataforma.resposta, "chave_acesso": CHAVE_ANTIGA}
    doc_id = client.post(f"{NFSE}/os/{numero}/emitir", headers=loja).json()["documento_id"]
    return numero, doc_id


def _status(db_session, doc_id):
    db_session.expire_all()
    return db_session.get(DocumentoFiscal, doc_id).status


def test_substituta_leva_os_campos_e_a_antiga_cai_quando_ela_autoriza(client, loja, servico, db_session, plataforma):
    numero, antiga = _autorizada(client, loja, db_session, plataforma, servico)
    assert client.get(f"{NFSE}/documentos/{antiga}", headers=loja).json()["pode_substituir"] is True

    plataforma.resposta = {**plataforma.resposta, "numero": 74799, "chave_acesso": "2" * 50}
    r = client.post(f"{NFSE}/documentos/{antiga}/substituir", json=MOTIVO, headers=loja)

    assert r.status_code == 200, r.text
    assert r.json()["status"] == "AUTORIZADA"
    ref, dps = plataforma.enviados[-1]
    assert ref.endswith("-2")
    assert dps["chave_nfse_substituida"] == CHAVE_ANTIGA
    assert dps["codigo_justificativa_substituicao"] == "99"
    assert dps["motivo_substituicao"] == MOTIVO["descricao"]

    db_session.expire_all()
    velha = db_session.get(DocumentoFiscal, antiga)
    assert velha.status == "CANCELADA"
    assert "74799" in velha.mensagem_sefaz
    # O cartão da OS mostra a nova.
    [doc] = client.get(f"{OS_URL}/{numero}/notas-fiscais", headers=loja).json()["servico"]["documentos"]
    assert doc["numero"] == 74799


def test_substituta_recusada_mantem_a_antiga_e_deixa_substituir_de_novo(
    client, loja, servico, db_session, plataforma,
):
    numero, antiga = _autorizada(client, loja, db_session, plataforma, servico)
    plataforma.resposta = {"status": "erro_autorizacao", "mensagem_sefaz": "E0312 valor invalido"}

    recusada = client.post(f"{NFSE}/documentos/{antiga}/substituir", json=MOTIVO, headers=loja).json()["documento_id"]

    assert _status(db_session, antiga) == "AUTORIZADA"
    # O cartão continua na nota que vale; a recusada não vira "Tentar de novo".
    [doc] = client.get(f"{OS_URL}/{numero}/notas-fiscais", headers=loja).json()["servico"]["documentos"]
    assert doc["id"] == antiga
    assert client.get(f"{NFSE}/documentos/{recusada}", headers=loja).json()["pode_tentar_de_novo"] is False
    r = client.post(f"{NFSE}/documentos/{recusada}/tentar-de-novo", headers=loja)
    assert r.status_code == 422 and r.json()["detail"]["codigo"] == "NFSE_ERA_SUBSTITUICAO"

    plataforma.resposta = {"status": "autorizado", "numero": 74800, "chave_acesso": "3" * 50}
    assert client.get(f"{NFSE}/documentos/{antiga}", headers=loja).json()["pode_substituir"] is True
    r = client.post(f"{NFSE}/documentos/{antiga}/substituir", json=MOTIVO, headers=loja)
    assert r.status_code == 200, r.text
    assert _status(db_session, antiga) == "CANCELADA"


def test_recusas(client, loja, servico, db_session, plataforma):
    numero, antiga = _autorizada(client, loja, db_session, plataforma, servico)

    r = client.post(f"{NFSE}/documentos/{antiga}/substituir", json={"motivo": "07", "descricao": MOTIVO["descricao"]},
                    headers=loja)
    assert r.status_code == 422 and r.json()["detail"]["codigo"] == "NFSE_MOTIVO_INVALIDO"
    assert client.post(f"{NFSE}/documentos/{antiga}/substituir", json={"motivo": "99", "descricao": "curto"},
                       headers=loja).status_code == 422
    assert client.post(f"{NFSE}/documentos/999999/substituir", json=MOTIVO, headers=loja).status_code == 404

    # Sem a chave gravada não há o que apontar.
    db_session.query(DocumentoFiscal).filter_by(id=antiga).update({"chave_acesso": None})
    db_session.commit()
    r = client.post(f"{NFSE}/documentos/{antiga}/substituir", json=MOTIVO, headers=loja)
    assert r.status_code == 422 and r.json()["detail"]["codigo"] == "NFSE_SEM_CHAVE"
    assert client.get(f"{NFSE}/documentos/{antiga}", headers=loja).json()["pode_substituir"] is False


def test_nota_recusada_nao_se_substitui(client, loja, servico, db_session, plataforma):
    numero = _criar_os(client, loja, db_session, [_item_servico(servico)])
    plataforma.resposta = {"status": "erro_autorizacao", "mensagem_sefaz": "E0312"}
    recusada = client.post(f"{NFSE}/os/{numero}/emitir", headers=loja).json()["documento_id"]

    r = client.post(f"{NFSE}/documentos/{recusada}/substituir", json=MOTIVO, headers=loja)
    assert r.status_code == 422 and r.json()["detail"]["codigo"] == "NFSE_NAO_AUTORIZADA"
