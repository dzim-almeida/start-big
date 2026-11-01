# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/test_emissao_troca_cfop.py
# DESCRIÇÃO: CFOP trocado na conferência da NF-e, ponta a ponta
#            (docs/nfe-cfop-e-notas-da-os-plano.md, C1).
# ---------------------------------------------------------------------------
import json

from app.db.models.produto_fiscal import ProdutoFiscal

from test_emissao_ponta_a_ponta import (  # noqa: F401 -- fixtures reutilizadas
    AUTORIZADA,
    REJEITADA_539,
    _doc,
    _licenca_com_nfe,
    _emitir,
    _reemitir,
    header_with_token,
    plataforma,
    venda_pronta,
)


def _preview(client, header, venda_id, trocar_cfop=None):
    corpo = {"venda_id": venda_id}
    if trocar_cfop is not None:
        corpo["trocar_cfop"] = trocar_cfop
    return client.post("/api/v1/fiscal/preview/nfe", json=corpo, headers=header)


def _emitir_com(client, header, venda_id, **extra):
    return client.post("/api/v1/fiscal/emitir/nfe", json={"venda_id": venda_id, **extra}, headers=header)


# --- Sem troca: a nota de sempre ----------------------------------------------

def test_previa_mostra_o_grupo_do_cfop_sugerido(client, header_with_token, venda_pronta):
    venda_id, _ = venda_pronta
    r = _preview(client, header_with_token, venda_id)
    assert r.status_code == 200, r.text
    grupos = r.json()["grupos_cfop"]
    assert len(grupos) == 1
    assert grupos[0]["cfop_sugerido"] == grupos[0]["cfop"] == "5102"
    assert grupos[0]["itens"] == [1]
    assert {o["cfop"] for o in grupos[0]["opcoes"]} == {"5101", "5102", "5103", "5104", "5405"}


def test_sem_troca_o_payload_e_o_de_sempre(client, db_session, header_with_token, venda_pronta, plataforma):
    venda_id, _ = venda_pronta
    falsa = plataforma(AUTORIZADA(11))
    r = _emitir(client, header_with_token, venda_id)
    assert r.status_code == 200, r.text

    payload = falsa.chamadas[0]["payload"]
    assert payload["natureza_operacao"] == "Venda de Mercadoria"
    assert payload["items"][0]["cfop"] == "5102"
    assert payload["items"][0]["icms_situacao_tributaria"] == "102"
    assert _doc(db_session, r.json()["documento_id"]).cfop_trocado is None


# --- Com troca -----------------------------------------------------------------

def test_previa_com_troca_mostra_o_cfop_novo_e_guarda_o_sugerido(client, header_with_token, venda_pronta):
    venda_id, _ = venda_pronta
    r = _preview(client, header_with_token, venda_id, {"5102": "5101"})
    assert r.status_code == 200, r.text
    corpo = r.json()
    assert corpo["itens"][0]["cfop"] == "5101"
    assert corpo["grupos_cfop"][0]["cfop_sugerido"] == "5102"
    assert corpo["grupos_cfop"][0]["cfop"] == "5101"


def test_troca_vai_na_nota_com_a_natureza_e_fica_registrada(
    client, db_session, header_with_token, venda_pronta, plataforma,
):
    venda_id, _ = venda_pronta
    falsa = plataforma(AUTORIZADA(11))
    r = _emitir_com(client, header_with_token, venda_id, trocar_cfop={"5102": "5101"})
    assert r.status_code == 200, r.text

    payload = falsa.chamadas[0]["payload"]
    assert payload["items"][0]["cfop"] == "5101"
    assert payload["items"][0]["icms_situacao_tributaria"] == "102", "dentro da família a situação fica"
    assert payload["natureza_operacao"] == "Venda de producao do estabelecimento"

    doc = _doc(db_session, r.json()["documento_id"])
    assert json.loads(doc.cfop_trocado)["trocas"] == {"5102": "5101"}
    assert doc.itens[0].cfop == "5101"


def test_entrar_no_5405_leva_o_csosn_500(client, header_with_token, venda_pronta, plataforma):
    venda_id, _ = venda_pronta
    falsa = plataforma(AUTORIZADA(11))
    r = _emitir_com(client, header_with_token, venda_id, trocar_cfop={"5102": "5405"})
    assert r.status_code == 200, r.text
    item = falsa.chamadas[0]["payload"]["items"][0]
    assert item["cfop"] == "5405"
    assert item["icms_situacao_tributaria"] == "500"


def test_troca_nao_mexe_no_cadastro(client, db_session, header_with_token, venda_pronta, plataforma):
    venda_id, _ = venda_pronta
    plataforma(AUTORIZADA(11))
    _emitir_com(client, header_with_token, venda_id, trocar_cfop={"5102": "5405"})
    db_session.expire_all()
    fiscal = db_session.query(ProdutoFiscal).first()
    assert (fiscal.cfop_padrao, fiscal.csosn) == ("5102", "102")


def test_cfop_como_padrao_grava_no_cadastro_com_a_situacao(
    client, db_session, header_with_token, venda_pronta, plataforma,
):
    venda_id, _ = venda_pronta
    plataforma(AUTORIZADA(11))
    r = _emitir_com(client, header_with_token, venda_id, trocar_cfop={"5102": "5405"}, cfop_como_padrao=True)
    assert r.status_code == 200, r.text
    db_session.expire_all()
    fiscal = db_session.query(ProdutoFiscal).first()
    assert (fiscal.cfop_padrao, fiscal.csosn) == ("5405", "500")


def test_reemissao_repete_a_troca(client, header_with_token, venda_pronta, plataforma):
    venda_id, _ = venda_pronta
    falsa = plataforma(REJEITADA_539, AUTORIZADA(12))
    rejeitado = _emitir_com(client, header_with_token, venda_id, trocar_cfop={"5102": "5101"}).json()
    r = _reemitir(client, header_with_token, rejeitado["documento_id"])
    assert r.status_code == 200, r.text
    assert falsa.chamadas[1]["payload"]["items"][0]["cfop"] == "5101"


# --- Recusas (antes de reservar número) ----------------------------------------

def test_troca_fora_da_familia_e_recusada(client, db_session, header_with_token, venda_pronta, plataforma):
    venda_id, _ = venda_pronta
    falsa = plataforma(AUTORIZADA(11))
    r = _emitir_com(client, header_with_token, venda_id, trocar_cfop={"5102": "6102"})
    assert r.status_code == 422
    assert "6102" in r.text
    assert falsa.chamadas == [], "nada foi transmitido"


def test_troca_de_cfop_que_nao_esta_na_nota_e_recusada(client, header_with_token, venda_pronta):
    venda_id, _ = venda_pronta
    r = _preview(client, header_with_token, venda_id, {"5405": "5102"})
    assert r.status_code == 422
    assert "não está nesta nota" in r.text


def test_cfop_com_formato_errado_e_recusado(client, header_with_token, venda_pronta):
    venda_id, _ = venda_pronta
    r = _preview(client, header_with_token, venda_id, {"5102": "51O1"})
    assert r.status_code == 422
