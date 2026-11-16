# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/marcenaria/test_faturamento_nfse_instalacao.py
# DESCRICAO: G5 do docs/nfse-fase2-plano.md: a instalacao dos moveis numa NFS-e
#            (uma por OS), com a plataforma falsa.
#
#            O que nao pode errar:
#              - so com o modo NFSE e o servico da instalacao escolhido;
#              - o valor e o do item "Instalacao e montagem" da OS;
#              - uma por OS (a segunda e recusada);
#              - o painel dos moveis continua so com as NF-e.
# ---------------------------------------------------------------------------

import pytest

from app.db.models.documento_fiscal import DocumentoFiscal
from app.services.fiscal.nfse.marcenaria import cidade_uf_do_endereco

from test.api.v1.marcenaria.test_faturamento_nfe_api import (  # noqa: F401 -- fixtures reutilizadas
    URL_CONFIG, fiscal_liberado, ligado, obra,
)

NFSE = "/api/v1/fiscal/nfse"


class PlataformaNfse:
    def __init__(self):
        self.enviados = []

    def emitir_nfse(self, ref, payload, idempotency_key=None, confirmar_duplicidade=False):
        self.enviados.append((ref, payload))
        return {"status": "autorizado", "numero": 321, "codigo_verificacao": "INST01"}

    def baixar_xml(self, caminho):
        return None


@pytest.fixture
def plataforma_nfse(monkeypatch):
    falsa = PlataformaNfse()
    monkeypatch.setattr("app.services.fiscal.nfse.marcenaria.get_fiscal_client", lambda *a, **k: falsa)
    return falsa


@pytest.fixture
def com_nfse(monkeypatch):
    from app.core import modulos as modulos_mod
    monkeypatch.setattr(modulos_mod.licenca_service, "modulos_da_licenca", lambda db: ["NFE", "NFSE"])


@pytest.fixture
def obra_com_instalacao(api, cliente_id):
    """Como o `_aprovar_obra` da producao, mas com instalacao de R$ 750,00 no orcamento."""
    from test.api.v1.marcenaria.test_producao_api import Producao, _movel
    from test.apoio_orcamento_marcenaria import aprovar

    orc = api.criar(cliente_id=cliente_id, projeto_nome="Apto 802")
    d = api.ok("PATCH", f"/{orc['id']}", rev=orc["revisao"], json={
        "instalacao_custo_centavos": 75000,
        "endereco_obra": "Rua das Flores, 10, Centro, Iguatu/CE, CEP 63500-000",
    })
    d = api.ok("POST", f"/{orc['id']}/ambientes", rev=d["revisao"], esperado=201, json={"nome": "Cozinha"})
    amb = d["ambientes"][0]["id"]
    d = api.ok("POST", f"/{orc['id']}/ambientes/{amb}/moveis", rev=d["revisao"], esperado=201, json=_movel("Balcão"))
    d = aprovar(api, d)
    return Producao(api, d["os"]["numero_os"])


@pytest.fixture
def servico_instalacao(api) -> int:
    r = api.client.post("/api/v1/servicos/", json={"descricao": "Montagem de moveis", "valor": 1000}, headers=api.header)
    sid = r.json()["id"]
    r = api.client.put(f"/api/v1/servicos/{sid}/fiscal", json={
        "codigo_tributacao_nacional": "140601", "codigo_nbs": "120100000",
    }, headers=api.header)
    assert r.status_code == 200, r.text
    return sid


def test_cidade_e_uf_saem_do_endereco_da_obra():
    assert cidade_uf_do_endereco("Rua A, 10 - Casa, Centro, Iguatu/CE, CEP 63500-000") == ("Iguatu", "CE")
    assert cidade_uf_do_endereco("Rua A, Iguatu") is None
    assert cidade_uf_do_endereco(None) is None


def test_modo_nfse_exige_o_servico_da_instalacao(api, ligado, com_nfse):
    r = api.client.put(URL_CONFIG, json={"instalacao_modo": "NFSE"}, headers=api.header)
    assert r.status_code == 422
    assert "serviço da instalação" in r.json()["detail"]


def test_sem_o_modo_nfse_nao_emite_e_o_painel_nao_muda(api, obra, ligado, com_nfse, plataforma_nfse):
    painel = api.client.get(f"/api/v1/marcenaria/os/{obra.numero_os}/faturamento", headers=api.header).json()
    assert painel["nfse_instalacao"] is None
    r = api.client.post(f"{NFSE}/os/{obra.numero_os}/instalacao/emitir", headers=api.header)
    assert r.status_code == 409 and r.json()["detail"]["codigo"] == "INSTALACAO_SEM_NFSE"
    assert plataforma_nfse.enviados == []


def test_emite_a_instalacao_uma_vez_por_os(api, obra_com_instalacao, ligado, com_nfse, servico_instalacao, plataforma_nfse, db_session):
    obra = obra_com_instalacao
    r = api.client.put(URL_CONFIG, json={"instalacao_modo": "NFSE", "servico_instalacao_id": servico_instalacao},
                       headers=api.header)
    assert r.status_code == 200, r.text

    painel = api.client.get(f"/api/v1/marcenaria/os/{obra.numero_os}/faturamento", headers=api.header).json()
    assert painel["instalacao_modo"] == "NFSE"
    assert painel["nfse_instalacao"]["valor"] > 0 and painel["nfse_instalacao"]["documento"] is None

    r = api.client.post(f"{NFSE}/os/{obra.numero_os}/instalacao/emitir", headers=api.header)

    assert r.status_code == 200, r.text
    assert r.json()["status"] == "AUTORIZADA"
    ref, dps = plataforma_nfse.enviados[0]
    assert ref.endswith("-nfse-inst")
    assert dps["codigo_tributacao_nacional_iss"] == "140601"
    assert dps["codigo_municipio_prestacao"] == "2305506"          # a cidade da OBRA (Iguatu/CE), nao a da loja
    assert dps["valor_servico"] * 100 == painel["nfse_instalacao"]["valor"] + round(dps.get("desconto_incondicionado", 0) * 100)
    doc = db_session.query(DocumentoFiscal).filter_by(papel="NFSE:INSTALACAO").one()
    assert (doc.numero_documento, doc.codigo_verificacao) == (321, "INST01")

    segunda = api.client.post(f"{NFSE}/os/{obra.numero_os}/instalacao/emitir", headers=api.header)
    assert segunda.status_code == 409 and segunda.json()["detail"]["codigo"] == "NFSE_INSTALACAO_JA_EMITIDA"

    painel = api.client.get(f"/api/v1/marcenaria/os/{obra.numero_os}/faturamento", headers=api.header).json()
    assert painel["nfse_instalacao"]["documento"]["codigo_verificacao"] == "INST01"
    assert all(n.get("papel") != "NFSE:INSTALACAO" for n in painel["notas"])   # a lista dos moveis nao a mostra
