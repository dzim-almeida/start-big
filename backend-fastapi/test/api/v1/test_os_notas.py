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
