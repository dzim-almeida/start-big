# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/fiscal/test_devolucao_api.py
# DESCRIÇÃO: TASK003 — a devolução vista pela API (contrato do modal).
# ---------------------------------------------------------------------------

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.aliquota_uf import AliquotaUF
from app.db.models.documento_fiscal import DocumentoFiscal
from app.db.models.documento_fiscal_item import DocumentoFiscalItem
from app.db.models.empresa import Empresa
from app.db.models.estoque import Estoque
from app.db.models.produto import Produto
from app.db.models.produto_fiscal import ProdutoFiscal
from app.services.fiscal.http.client_mock import FiscalClientMock

CHAVE = "35260911222333000181550010000000421000000429"
MOTIVO = "Cliente devolveu a mercadoria com defeito de fabrica."
DESTINATARIO = {
    "cpf_ou_cnpj": "12345678909", "nome_razao_social": "Maria Silva",
    "logradouro": "Rua B", "numero": "20", "bairro": "Centro", "codigo_municipio": "3550308",
    "municipio": "Sao Paulo", "uf": "SP", "cep": "01001000",
}


@pytest.fixture(autouse=True)
def _mock_da_emissora(monkeypatch):
    mock = FiscalClientMock(delay=0)
    monkeypatch.setattr("app.services.fiscal.devolucao.get_fiscal_client", lambda *a, **k: mock)
    monkeypatch.setattr("app.services.fiscal.devolucao.crud.get_licenca_token", lambda _db: "tok")


@pytest.fixture
def nota_anonima(db_session: Session, fiscal_settings) -> DocumentoFiscal:
    """NFC-e sem CPF, com um item de 2 UN, empresa completa para emitir."""
    empresa = db_session.query(Empresa).first()
    empresa.documento = "11222333000181"
    empresa.indicador_ie = "9"
    empresa.crt = 1
    db_session.add(AliquotaUF(uf="SP", aliquota_icms_interna=1800, aliquota_pis_padrao=165, aliquota_cofins_padrao=760))
    db_session.add(Produto(id=1, nome="Teclado", codigo_produto="P1", unidade_medida="UN"))
    db_session.flush()
    db_session.add(ProdutoFiscal(produto_id=1, ncm="84716052", cfop_padrao="5102", origem_mercadoria=0, csosn="102"))
    db_session.add(Estoque(id=1, quantidade=5, valor_varejo=10000))

    doc = DocumentoFiscal(
        tipo_documento="NFCE", origem_tipo="VENDA", origem_id=1, numero_documento=7, serie=1,
        status="AUTORIZADA", ref_api="venda-1", chave_acesso=CHAVE, ambiente_emissao=2,
    )
    doc.itens.append(DocumentoFiscalItem(
        numero_item=1, produto_id=1, descricao="Teclado", codigo_produto="P1", unidade="UN",
        ncm="84716052", cfop="5102", origem_mercadoria="0", situacao_tributaria="102",
        quantidade_milesimos=2000, valor_unitario=10000, valor_bruto=20000,
    ))
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    return doc


def _url(doc_id: int) -> str:
    return f"/api/v1/fiscal/documentos/{doc_id}/devolucao"


def test_nfce_anonima_sem_destinatario_e_422_com_codigo(client: TestClient, header_com_token, nota_anonima):
    resposta = client.post(_url(nota_anonima.id), json={"motivo": MOTIVO}, headers=header_com_token)
    assert resposta.status_code == 422, resposta.text
    assert resposta.json()["detail"]["codigo"] == "DESTINATARIO_OBRIGATORIO"


def test_devolucao_parcial_devolve_o_documento_novo_e_atualiza_o_saldo_da_origem(
    client: TestClient, header_com_token, nota_anonima, db_session
):
    item_id = nota_anonima.itens[0].id
    resposta = client.post(
        _url(nota_anonima.id),
        json={
            "motivo": MOTIVO, "devolver_estoque": True,
            "itens": [{"documento_item_id": item_id, "quantidade": 1000}],
            "destinatario_avulso": DESTINATARIO,
        },
        headers=header_com_token,
    )
    assert resposta.status_code == 200, resposta.text
    novo = resposta.json()
    assert novo["tipo_documento"] == "NFE"
    assert novo["status"] == "AUTORIZADA"
    assert novo["finalidade_emissao"] == 4
    assert novo["documento_referenciado_id"] == nota_anonima.id
    assert novo["chave_documento_referenciado"] == CHAVE
    assert novo["itens_resumo"][0]["cfop"] == "1202"

    origem = client.get(f"/api/v1/fiscal/documentos/{nota_anonima.id}", headers=header_com_token).json()
    assert origem["totalmente_devolvida"] is False
    [item] = origem["itens_resumo"]
    assert item["quantidade_milesimos"] == 2000
    assert item["quantidade_devolvida_acumulada"] == 1000

    db_session.expire_all()
    assert db_session.get(Estoque, 1).quantidade == 6


def test_devolucao_total_marca_a_origem_como_totalmente_devolvida(
    client: TestClient, header_com_token, nota_anonima
):
    resposta = client.post(
        _url(nota_anonima.id),
        json={"motivo": MOTIVO, "destinatario_avulso": DESTINATARIO},
        headers=header_com_token,
    )
    assert resposta.status_code == 200, resposta.text
    origem = client.get(f"/api/v1/fiscal/documentos/{nota_anonima.id}", headers=header_com_token).json()
    assert origem["totalmente_devolvida"] is True
