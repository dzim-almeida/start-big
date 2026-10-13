# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/test_os_fiscal_erros.py
# DESCRICAO: As recusas das rotas fiscais da OS chegam ao lojista com o status
#            e a mensagem certos, e nao como erro 500.
#
#            `HTTPException` era usada no endpoint da OS sem estar importada:
#            cada `raise` virava NameError. Assim, "nota ainda nao configurada"
#            (404), "NFS-e nao disponivel" (501) e "existem pendencias" (422)
#            chegavam todas como 500, sem a explicacao.
# ---------------------------------------------------------------------------

import pytest
from fastapi.testclient import TestClient

from app.db.models.empresa import Empresa
from app.db.models.empresa_fiscal_settings import EmpresaFiscalSettings
from app.main import app

from test.apoio_orcamento_marcenaria import _criar_loja

OS_URL = "/api/v1/ordens-servico"


@pytest.fixture
def client():
    """SEM `with`: o lifespan nao roda (nada no banco real da maquina)."""
    yield TestClient(app)


@pytest.fixture
def loja(client, db_session, monkeypatch) -> dict:
    """Loja de informatica com o modulo fiscal contratado e configurado."""
    from app.core import modulos as modulos_mod

    monkeypatch.setattr(modulos_mod.licenca_service, "modulos_da_licenca", lambda db: ["NFE"])
    header = _criar_loja(client, "assistencia_tecnica")
    empresa = db_session.query(Empresa).first()
    db_session.add(EmpresaFiscalSettings(
        empresa_id=empresa.id, serie_nfe=1, ultimo_numero_nfe=0, ambiente_emissao=2,
    ))
    db_session.commit()
    return header


@pytest.fixture
def numero_os(client, loja) -> str:
    """OS so com mao de obra (nenhuma peca para a NF-e)."""
    cliente = client.post("/api/v1/clientes/cliente_pf", json={"nome": "Seu Jorge", "cpf": "11144477735", "tipo": "PF"},
                          headers=loja).json()["id"]
    r = client.post(f"{OS_URL}/", json={
        "cliente_id": cliente, "prioridade": "NORMAL", "defeito_relatado": "Tela quebrada", "dados_adicionais": {},
        "objeto": {"marca": "Apple", "modelo": "iPhone 11", "numero_serie": "ABC12345"},
        "itens": [{"tipo": "SERVICO", "nome": "Troca de tela", "unidade_medida": "UN", "quantidade": 1,
                   "valor_unitario": 35000}],
    }, headers=loja)
    assert r.status_code == 201, r.text
    return r.json()["numero_os"]


def test_os_sem_dados_fiscais_responde_404(client, loja, numero_os):
    r = client.get(f"{OS_URL}/{numero_os}/fiscal", headers=loja)
    assert r.status_code == 404, r.text
    assert r.json()["detail"] == "Nota fiscal ainda não configurada para esta OS"


def test_pedir_nfse_responde_501_com_a_explicacao(client, loja, numero_os):
    r = client.post(f"{OS_URL}/{numero_os}/emitir-fiscal", params={"tipo_documento": "nfse"}, headers=loja)
    assert r.status_code == 501, r.text
    assert r.json()["detail"]["codigo"] == "NFSE_NAO_DISPONIVEL"


def test_os_com_pendencias_responde_422_com_a_lista(client, loja, numero_os):
    verificacao = client.get(f"{OS_URL}/{numero_os}/verificar-fiscal", params={"tipo_documento": "nfe"}, headers=loja)
    assert verificacao.status_code == 200, verificacao.text
    assert verificacao.json()["completo"] is False      # premissa: ha pendencia

    r = client.post(f"{OS_URL}/{numero_os}/emitir-fiscal", params={"tipo_documento": "nfe"}, headers=loja)
    assert r.status_code == 422, r.text
    assert r.json()["detail"]["codigo"] == "PENDENCIAS_FISCAIS"
