# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/etiquetas/test_envio_api.py
# DESCRIÇÃO: Dados das etiquetas de envio (docs/etiquetas-plano.md, fase 5).
# ---------------------------------------------------------------------------

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.enum import EntityType, OrdemServicoStatus, VendaStatus
from app.db.models.cliente import ClientePF, ClientePJ
from app.db.models.documento_fiscal import DocumentoFiscal
from app.db.models.empresa import Empresa
from app.db.models.endereco import Endereco
from app.db.models.funcionario import Funcionario
from app.db.models.objeto_servico import ObjetoServico
from app.db.models.ordem_servico import OrdemServico
from app.db.models.venda import Venda
from app.services.etiqueta_envio import PERMISSOES_OS, PERMISSOES_VENDA, pode

URL = "/api/v1/etiquetas/envio"
CHAVE = "35260912345678000199550010000000111000000110"


def _endereco(entidade_id: int, tipo: EntityType, cidade: str) -> Endereco:
    return Endereco(
        id_entidade=entidade_id, tipo_entidade=tipo, logradouro="Rua das Flores", numero="100",
        bairro="Centro", cidade=cidade, estado="CE", cep="63500-000",
    )


@pytest.fixture
def cenario(db_session: Session, header_com_token) -> dict:
    empresa = db_session.query(Empresa).first()
    func = Funcionario(empresa_id=empresa.id, nome="Vendedor")
    maria = ClientePF(tipo="PF", nome="Maria da Silva", cpf="52998224725", celular="88999990000")
    loja = ClientePJ(tipo="PJ", razao_social="Móveis Norte LTDA", nome_fantasia="Móveis Norte", cnpj="11222333000181", ie="123456")
    db_session.add_all([func, maria, loja])
    db_session.flush()
    db_session.add_all([
        _endereco(maria.id, EntityType.CLIENTE, "Iguatu"),
        _endereco(loja.id, EntityType.CLIENTE, "Juazeiro do Norte"),
    ])

    venda = Venda(funcionario_id=func.id, cliente_id=maria.id, status=VendaStatus.FINALIZADA, numero_venda=41)
    rascunho = Venda(funcionario_id=func.id, cliente_id=maria.id, status=VendaStatus.ATIVA, numero_venda=None)
    objeto = ObjetoServico(cliente_id=loja.id, marca="Cozinha", modelo="Planejada", numero_serie="PRJ-000123")
    db_session.add_all([venda, rascunho, objeto])
    db_session.flush()
    os_ = OrdemServico(
        numero_os="OS-2026-000009", objeto_id=objeto.id, defeito_relatado="Cozinha planejada",
        status=OrdemServicoStatus.EM_ANDAMENTO,
    )
    db_session.add(os_)
    db_session.flush()

    # NF-e autorizada da VENDA — o origem_id é o NÚMERO da venda (41), não o id.
    db_session.add(DocumentoFiscal(
        tipo_documento="NFE", origem_tipo="VENDA", origem_id=41, status="AUTORIZADA",
        numero_documento=11, serie=1, chave_acesso=CHAVE, protocolo_autorizacao="135260000000001",
        data_autorizacao=datetime(2026, 9, 20, 10, 30), valor_total=128000, ambiente_emissao=2, ref_api="v-41",
        destinatario_nome_enviado="MARIA DA SILVA", destinatario_documento_enviado="52998224725",
    ))
    # Uma NF-e REJEITADA da OS não pode aparecer.
    db_session.add(DocumentoFiscal(
        tipo_documento="NFE", origem_tipo="OS", origem_id=os_.id, status="REJEITADA",
        numero_documento=12, serie=1, chave_acesso=CHAVE, ref_api="os-9",
    ))
    db_session.commit()
    return {"venda": venda.id, "rascunho": rascunho.id, "os": os_.id}


def test_origens_traz_os_e_so_vendas_finalizadas(client: TestClient, header_com_token, cenario):
    resposta = client.get(f"{URL}/origens", headers=header_com_token)
    assert resposta.status_code == 200, resposta.text
    itens = {(i["tipo"], i["id"]): i for i in resposta.json()}
    assert ("venda", cenario["venda"]) in itens
    assert ("venda", cenario["rascunho"]) not in itens
    assert itens[("venda", cenario["venda"])]["tem_nfe"] is True
    assert itens[("os", cenario["os"])]["tem_nfe"] is False
    assert itens[("os", cenario["os"])]["cliente_nome"] == "Móveis Norte"


def test_origens_busca_por_cliente_sem_acento_e_por_identificador(client: TestClient, header_com_token, cenario):
    por_cliente = client.get(f"{URL}/origens", params={"busca": "moveis norte"}, headers=header_com_token).json()
    assert [(i["tipo"], i["id"]) for i in por_cliente] == [("os", cenario["os"])]
    por_projeto = client.get(f"{URL}/origens", params={"busca": "prj 000123"}, headers=header_com_token).json()
    assert [(i["tipo"], i["id"]) for i in por_projeto] == [("os", cenario["os"])]


def test_dados_da_venda_com_nfe_autorizada(client: TestClient, header_com_token, cenario):
    resposta = client.get(f"{URL}/venda/{cenario['venda']}", headers=header_com_token)
    assert resposta.status_code == 200, resposta.text
    dados = resposta.json()
    assert dados["numero"] == "41"
    assert dados["destinatario"]["nome"] == "Maria da Silva"
    assert dados["destinatario"]["documento"] == "52998224725"
    assert dados["destinatario"]["endereco"]["cidade"] == "Iguatu"
    assert dados["nfe"]["chave_acesso"] == CHAVE and dados["nfe"]["numero"] == 11
    # O DANFE usa o destinatário como foi para a nota, não o cadastro de hoje.
    assert dados["nfe"]["destinatario_nome"] == "MARIA DA SILVA"
    # O remetente vem do cadastro da empresa, nunca do modelo.
    assert dados["remetente"]["nome"]


def test_dados_da_os_usam_razao_social_e_ignoram_nfe_rejeitada(client: TestClient, header_com_token, cenario):
    dados = client.get(f"{URL}/os/{cenario['os']}", headers=header_com_token).json()
    assert dados["numero"] == "OS-2026-000009"
    assert dados["identificador"] == "PRJ-000123"
    assert dados["destinatario"]["nome"] == "Móveis Norte LTDA"
    assert dados["destinatario"]["inscricao_estadual"] == "123456"
    assert dados["nfe"] is None


def test_origem_inexistente_e_404(client: TestClient, header_com_token, cenario):
    assert client.get(f"{URL}/os/9999", headers=header_com_token).status_code == 404
    assert client.get(f"{URL}/venda/9999", headers=header_com_token).status_code == 404


def test_remetente(client: TestClient, header_com_token):
    resposta = client.get(f"{URL}/remetente", headers=header_com_token)
    assert resposta.status_code == 200
    assert resposta.json()["nome"]


def test_permissao_por_tipo_de_origem():
    so_estoque = {"permissoes": {"produto": True}}
    vendedor = {"permissoes": {"venda": True}}
    assert not pode(so_estoque, PERMISSOES_VENDA) and not pode(so_estoque, PERMISSOES_OS)
    assert pode(vendedor, PERMISSOES_VENDA) and not pode(vendedor, PERMISSOES_OS)
    assert pode({"is_master": True}, PERMISSOES_OS)
    assert pode({"permissoes": {"all": True}}, PERMISSOES_VENDA)
