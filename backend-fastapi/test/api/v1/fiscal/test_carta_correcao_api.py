# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/fiscal/test_carta_correcao_api.py
# DESCRIÇÃO: TASK002 — a CC-e vista pela API (contrato do drawer).
# ---------------------------------------------------------------------------

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.documento_fiscal import DocumentoFiscal
from app.services.fiscal.http.client_mock import FiscalClientMock

CORRECAO = "Corrigido o complemento do endereço do destinatário: sala 302."


@pytest.fixture(autouse=True)
def _mock_da_emissora(monkeypatch):
    mock = FiscalClientMock(delay=0)
    monkeypatch.setattr(
        "app.services.fiscal.carta_correcao.get_fiscal_client", lambda *a, **k: mock,
    )
    monkeypatch.setattr("app.services.fiscal.carta_correcao.crud.get_licenca_token", lambda _db: "tok")


def _nfe(db: Session, tipo="NFE") -> DocumentoFiscal:
    doc = DocumentoFiscal(
        tipo_documento=tipo, origem_tipo="VENDA", origem_id=1, numero_documento=42,
        serie=1, status="AUTORIZADA", ref_api="nfe-42",
        chave_acesso="35260911222333000181550010000000421000000429",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def test_post_registra_carta_e_devolve_o_registro(
    client: TestClient, header_com_token, fiscal_settings, db_session
):
    doc = _nfe(db_session)
    resposta = client.post(
        f"/api/v1/fiscal/documentos/{doc.id}/carta-correcao",
        json={"correcao": CORRECAO}, headers=header_com_token,
    )
    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    assert corpo["status"] == "AUTORIZADA"
    assert corpo["sequencia"] == 1
    assert corpo["documento_id"] == doc.id
    assert corpo["xml_local"] is False and corpo["pdf_local"] is False


def test_post_com_correcao_curta_e_422_do_schema(
    client: TestClient, header_com_token, fiscal_settings, db_session
):
    doc = _nfe(db_session)
    resposta = client.post(
        f"/api/v1/fiscal/documentos/{doc.id}/carta-correcao",
        json={"correcao": "curta"}, headers=header_com_token,
    )
    assert resposta.status_code == 422


def test_post_em_nfce_e_422_com_codigo(
    client: TestClient, header_com_token, fiscal_settings, db_session
):
    doc = _nfe(db_session, tipo="NFCE")
    resposta = client.post(
        f"/api/v1/fiscal/documentos/{doc.id}/carta-correcao",
        json={"correcao": CORRECAO}, headers=header_com_token,
    )
    assert resposta.status_code == 422
    assert resposta.json()["detail"]["codigo"] == "CCE_SOMENTE_NFE"


def test_get_lista_as_cartas_da_nota_e_o_documento_expoe_o_total(
    client: TestClient, header_com_token, fiscal_settings, db_session
):
    doc = _nfe(db_session)
    for texto in (CORRECAO, CORRECAO + " E o CEP 01001-000."):
        client.post(
            f"/api/v1/fiscal/documentos/{doc.id}/carta-correcao",
            json={"correcao": texto}, headers=header_com_token,
        )

    lista = client.get(
        f"/api/v1/fiscal/documentos/{doc.id}/cartas-correcao", headers=header_com_token,
    )
    assert lista.status_code == 200, lista.text
    assert [c["sequencia"] for c in lista.json()] == [1, 2]

    detalhe = client.get(f"/api/v1/fiscal/documentos/{doc.id}", headers=header_com_token)
    assert detalhe.status_code == 200, detalhe.text
    assert detalhe.json()["total_cartas_correcao"] == 2
    assert detalhe.json()["ultima_carta_correcao"].endswith("CEP 01001-000.")


def test_documento_sem_carta_expoe_zero_e_nulo(
    client: TestClient, header_com_token, fiscal_settings, db_session
):
    doc = _nfe(db_session)
    detalhe = client.get(f"/api/v1/fiscal/documentos/{doc.id}", headers=header_com_token)
    assert detalhe.json()["total_cartas_correcao"] == 0
    assert detalhe.json()["ultima_carta_correcao"] is None


def test_pdf_indisponivel_e_404_e_nao_500(
    client: TestClient, header_com_token, fiscal_settings, db_session
):
    doc = _nfe(db_session)
    carta = client.post(
        f"/api/v1/fiscal/documentos/{doc.id}/carta-correcao",
        json={"correcao": CORRECAO}, headers=header_com_token,
    ).json()
    resposta = client.get(
        f"/api/v1/fiscal/cartas-correcao/{carta['id']}/pdf", headers=header_com_token,
    )
    assert resposta.status_code == 404
