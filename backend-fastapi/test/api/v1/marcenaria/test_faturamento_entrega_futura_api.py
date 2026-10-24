# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/marcenaria/test_faturamento_entrega_futura_api.py
# DESCRICAO: F4 do faturamento dos moveis (docs/marcenaria-faturamento-
#            plano.md): venda para entrega futura, com a plataforma falsa.
#
#            O que nao pode errar:
#              - a 5922 cobre todos os moveis de uma vez e nao mexe no estoque;
#              - a remessa so sai com a 5922 autorizada e aponta para ela;
#              - a 5922 nao cai com remessa viva, nem a OS com a 5922 valendo;
#              - 5922 rejeitada libera os moveis para outra.
# ---------------------------------------------------------------------------

import pytest

from app.db.models.configuracao_marcenaria import ConfiguracaoMarcenaria
from app.db.models.documento_fiscal import DocumentoFiscal
from app.db.models.marcenaria import MarcenariaMovel
from app.db.models.produto import Produto

from test.api.v1.marcenaria.test_faturamento_nfe_api import (  # noqa: F401 -- fixtures reutilizadas
    AUTORIZADA, REJEITADA, URL_CONFIG, fiscal_liberado, ligado, obra, plataforma,
)
from test.api.v1.marcenaria.test_producao_api import OS_URL, _todas


@pytest.fixture
def futura(api, db_session, ligado) -> ConfiguracaoMarcenaria:
    r = api.client.put(URL_CONFIG, json={"faturamento_modo": "ENTREGA_FUTURA"}, headers=api.header)
    assert r.status_code == 200, r.text
    db_session.expire_all()
    return db_session.query(ConfiguracaoMarcenaria).one()


def _url(obra, caminho=""):
    return f"/api/v1/marcenaria/os/{obra.numero_os}/faturamento{caminho}"


def _simples_faturamento(api, obra):
    return api.client.post(_url(obra, "/simples-faturamento/emitir"), headers=api.header)


def _remessa(api, obra, *nomes):
    ids = [obra.movel(nome)["movel_id"] for nome in nomes]
    return api.client.post(_url(obra, "/emitir"), json={"movel_ids": ids}, headers=api.header)


def _estoque(db, produto_id):
    db.expire_all()
    return db.get(Produto, produto_id).estoque.quantidade


def test_simples_faturamento_cobre_todos_e_nao_mexe_no_estoque(api, obra, futura, plataforma, db_session):
    plataforma.respostas = [AUTORIZADA(20)]

    r = _simples_faturamento(api, obra)

    assert r.status_code == 200, r.text
    (payload,) = plataforma.payloads
    assert {i["cfop"] for i in payload["items"]} == {"5922"}
    assert len(payload["items"]) == 3                                   # Balcão, Aéreo e a Torre
    assert _estoque(db_session, futura.produto_acabado_padrao_id) == 0
    doc = db_session.query(DocumentoFiscal).one()
    assert doc.papel == "SIMPLES_FATURAMENTO"
    assert {m.simples_faturamento_id for m in db_session.query(MarcenariaMovel).filter(MarcenariaMovel.aprovado).all()} == {doc.id}
    # De novo: todos ja estao cobertos.
    assert _simples_faturamento(api, obra).status_code == 409


def test_remessa_so_com_a_5922_autorizada_e_apontando_para_ela(api, obra, futura, plataforma, db_session):
    obra.concluir(*_todas(obra.ler(), "Balcão"))
    assert _remessa(api, obra, "Balcão").status_code == 409             # sem simples faturamento

    plataforma.respostas = [AUTORIZADA(21), AUTORIZADA(22)]
    _simples_faturamento(api, obra)
    chave_sf = db_session.query(DocumentoFiscal).one().chave_acesso
    r = _remessa(api, obra, "Balcão")

    assert r.status_code == 200, r.text
    remessa = plataforma.payloads[1]
    assert [i["cfop"] for i in remessa["items"]] == ["5116"]
    assert remessa["formas_pagamento"] == [{"forma_pagamento": "90", "valor_pagamento": 0.0}]
    assert remessa["notas_referenciadas"] == [{"chave_nfe": chave_sf}]
    assert _estoque(db_session, futura.produto_acabado_padrao_id) == 0       # entrou pronto e saiu na remessa


def test_5922_nao_cai_com_remessa_viva_nem_a_os(api, obra, futura, plataforma, db_session):
    from fastapi import HTTPException
    from app.services.fiscal.eventos.consulta_cancelamento import cancelar_documento

    obra.concluir(*_todas(obra.ler(), "Balcão"))
    plataforma.respostas = [AUTORIZADA(23), AUTORIZADA(24)]
    sf_id = _simples_faturamento(api, obra).json()["documento_id"]
    _remessa(api, obra, "Balcão")

    with pytest.raises(HTTPException) as erro:
        cancelar_documento(db_session, sf_id, futura.empresa_id, "Cliente desistiu da compra toda")
    assert erro.value.status_code == 409
    db_session.rollback()

    r = api.client.put(f"{OS_URL}/{obra.numero_os}/cancelar", json={"motivo": "Desistiu"}, headers=api.header)
    assert r.status_code == 409 and "simples faturamento" in r.json()["detail"]


def test_5922_rejeitada_libera_os_moveis(api, obra, futura, plataforma, db_session):
    plataforma.respostas = [REJEITADA, AUTORIZADA(25)]

    assert _simples_faturamento(api, obra).json()["status"] == "REJEITADA"
    db_session.expire_all()
    assert all(m.simples_faturamento_id is None for m in db_session.query(MarcenariaMovel).all())

    assert _simples_faturamento(api, obra).json()["status"] == "AUTORIZADA"


def test_painel_diz_o_que_falta(api, obra, futura, plataforma, db_session):
    obra.concluir(*_todas(obra.ler(), "Balcão"))
    painel = api.client.get(_url(obra), headers=api.header).json()
    assert painel["falta_simples_faturamento"] is True
    balcao = next(m for m in painel["moveis"] if m["nome"] == "Balcão")
    assert balcao["situacao"] == "NO_ESTOQUE" and balcao["pode_faturar"] is False   # pronto, mas sem a 5922

    plataforma.respostas = [AUTORIZADA(26)]
    _simples_faturamento(api, obra)
    painel = api.client.get(_url(obra), headers=api.header).json()
    assert painel["falta_simples_faturamento"] is False
    assert next(m for m in painel["moveis"] if m["nome"] == "Balcão")["pode_faturar"] is True
