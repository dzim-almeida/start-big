# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/test_franquia_fiscal.py
# DESCRICAO: O saldo da franquia fiscal na tela (docs/nfse-fase2-plano.md, G1).
#            So informa: sem resposta da plataforma, a tela esconde o cartao.
# ---------------------------------------------------------------------------

import pytest
from fastapi.testclient import TestClient

from app.main import app

from test.apoio_orcamento_marcenaria import _criar_loja

FRANQUIA = {
    "competencia": "2026-11", "vigente": True, "franquia": 70, "emitidas": 74,
    "restantesNaFranquia": 0, "excedentes": 4, "precoExcedente": 1, "valorExcedente": 4,
    "formaCobranca": "CARTAO", "limite": 300, "restantes": 226,
}


@pytest.fixture
def client():
    yield TestClient(app)


@pytest.fixture
def loja(client, db_session, monkeypatch) -> dict:
    from app.core import modulos as modulos_mod

    monkeypatch.setattr(modulos_mod.licenca_service, "modulos_da_licenca", lambda db: ["FINANCEIRO"])
    return _criar_loja(client, "assistencia_tecnica")


def _plataforma(monkeypatch, resposta):
    class Falsa:
        def consultar_franquia(self):
            return resposta
    monkeypatch.setattr("app.services.fiscal.http.get_fiscal_client", lambda *a, **k: Falsa())


def test_repassa_a_franquia_sem_exigir_modulo(client, loja, monkeypatch):
    _plataforma(monkeypatch, FRANQUIA)
    r = client.get("/api/v1/fiscal/franquia", headers=loja)
    assert r.status_code == 200, r.text
    assert r.json()["consultou"] is True
    assert (r.json()["emitidas"], r.json()["valorExcedente"]) == (74, 4)


def test_sem_resposta_da_plataforma_nao_e_erro(client, loja, monkeypatch):
    _plataforma(monkeypatch, {})
    r = client.get("/api/v1/fiscal/franquia", headers=loja)
    assert r.status_code == 200
    assert r.json() == {"consultou": False}


def test_client_sem_a_rota_devolve_vazio(monkeypatch):
    """Plataforma antiga (404) ou rede fora: {} -- nunca levanta."""
    import httpx
    from app.services.fiscal.http.client_startbig import FiscalClientStartBig

    def falha(*a, **k):
        raise httpx.ConnectError("sem rede")
    monkeypatch.setattr(httpx.Client, "get", falha)
    assert FiscalClientStartBig().consultar_franquia() == {}
