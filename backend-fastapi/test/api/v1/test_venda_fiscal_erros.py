# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/test_venda_fiscal_erros.py
# DESCRICAO: As recusas das rotas fiscais da VENDA e do SERVICO chegam com o
#            status e a mensagem certos, e nao como erro 500.
#
#            Mesmo bug da OS (d02841d): o endpoint usava `HTTPException` sem
#            importar, e cada `raise` virava NameError -> 500 sem explicacao:
#            "nota ainda nao configurada" (404) e "informe entre 1 e 50 IDs"
#            (400) na verificacao fiscal em lote, e "dados fiscais ainda nao
#            preenchidos" (404) no cadastro de servico.
# ---------------------------------------------------------------------------

import pytest
from fastapi.testclient import TestClient

from app.db.models.empresa import Empresa
from app.db.models.empresa_fiscal_settings import EmpresaFiscalSettings

from test_venda_correcao_fiscal import (  # noqa: F401 -- fixtures reutilizadas
    _funcionario,
    _licenca_com_nfe,
    header_with_token,
)


@pytest.fixture
def loja(db_session, header_with_token) -> dict:
    """Modulo fiscal contratado (fixture _licenca_com_nfe) e configurado."""
    empresa = db_session.query(Empresa).first()
    if not db_session.query(EmpresaFiscalSettings).filter_by(empresa_id=empresa.id).first():
        db_session.add(EmpresaFiscalSettings(
            empresa_id=empresa.id, serie_nfe=1, ultimo_numero_nfe=0, ambiente_emissao=2,
        ))
        db_session.commit()
    return header_with_token


def test_venda_sem_dados_fiscais_responde_404(client: TestClient, loja):
    func_id = _funcionario(client, loja)
    cv = client.post("/api/v1/vendas/", json={"funcionario_id": func_id}, headers=loja)
    assert cv.status_code == 201, cv.text

    r = client.get(f"/api/v1/vendas/{cv.json()['id']}/fiscal", headers=loja)
    assert r.status_code == 404, r.text
    assert r.json()["detail"] == "Nota fiscal ainda não configurada para esta venda"


@pytest.mark.parametrize("ids", ["abc", ",".join(str(i) for i in range(1, 52))])
def test_verificacao_em_lote_fora_do_limite_responde_400(client: TestClient, loja, ids):
    r = client.get("/api/v1/vendas/verificar-fiscal-batch", params={"ids": ids}, headers=loja)
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "Informe entre 1 e 50 IDs de venda."


def test_servico_sem_dados_fiscais_responde_404(client: TestClient, loja):
    cs = client.post("/api/v1/servicos/", json={"descricao": "Formatacao", "valor": 15000}, headers=loja)
    assert cs.status_code == 201, cs.text

    r = client.get(f"/api/v1/servicos/{cs.json()['id']}/fiscal", headers=loja)
    assert r.status_code == 404, r.text
    assert r.json()["detail"] == "Dados fiscais ainda não preenchidos para este serviço"
