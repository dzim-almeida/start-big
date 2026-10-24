# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/marcenaria/test_faturamento_nfe_api.py
# DESCRICAO: F3 do faturamento dos moveis (docs/marcenaria-faturamento-
#            plano.md): a NF-e de uma entrega, com a plataforma falsa.
#
#            O que nao pode errar:
#              - so movel pronto (no estoque) entra, e cada um em UMA nota (D1);
#              - a nota leva o movel como o produto acabado, com o nome do movel;
#              - autorizada: o acabado sai do estoque; rejeitada ou cancelada:
#                volta (e o movel pode ir para outra nota);
#              - a OS da marcenaria nao emite mais pelo caminho da OS comum
#                (a nota das chapas a R$ 0).
# ---------------------------------------------------------------------------

import pytest

from app.core.depends import requer_modulo_fiscal
from app.db.models.configuracao_marcenaria import ConfiguracaoMarcenaria
from app.db.models.documento_fiscal import DocumentoFiscal
from app.db.models.empresa import Empresa
from app.db.models.empresa_fiscal_settings import EmpresaFiscalSettings
from app.db.models.marcenaria.faturamento import MarcenariaMovelFaturamento
from app.db.models.produto import Produto
from app.db.models.produto_fiscal import ProdutoFiscal
from app.main import app

from test.api.v1.marcenaria.test_producao_api import Producao, _aprovar_obra, _todas

URL_CONFIG = "/api/v1/configuracoes/marcenaria"
CNPJ_VALIDO = "11222333000181"


class PlataformaFalsa:
    """Responde o que o teste mandar e guarda o payload recebido."""

    ambiente = 2

    def __init__(self):
        self.respostas, self.payloads = [], []

    def emitir_nfe(self, ref, payload, idempotency_key=None):
        self.payloads.append(payload)
        return self.respostas.pop(0)

    def cancelar_nfe(self, ref, justificativa, tipo_documento="NFE"):
        return {"status": "cancelado", "mensagem_sefaz": "Cancelamento homologado"}

    def baixar_xml(self, caminho):
        return None


def AUTORIZADA(numero):
    return {"status": "autorizado", "chave_acesso": f"35261011222333000181550010000000{numero:02d}1000000015",
            "protocolo": f"1352600000{numero:05d}", "numero": numero, "serie": 1,
            "codigo_sefaz": 100, "mensagem_sefaz": "Autorizado o uso da NF-e"}


REJEITADA = {"status": "erro", "codigo_sefaz": 778, "mensagem_sefaz": "Rejeição 778: NCM inexistente"}


@pytest.fixture
def plataforma(monkeypatch):
    from app.services.fiscal.emissoes import nfe_marcenaria
    from app.services.fiscal.eventos import consulta_cancelamento

    falsa = PlataformaFalsa()
    for mod in (nfe_marcenaria, consulta_cancelamento):
        monkeypatch.setattr(mod, "get_fiscal_client", lambda *a, **k: falsa)
    monkeypatch.setattr(nfe_marcenaria.crud, "get_licenca_token", lambda _db: "tok")
    return falsa


@pytest.fixture
def fiscal_liberado(api, db_session):
    """Emitente pronto para emitir (o modulo NFE da licenca fica fora: e a porta, nao a regra)."""
    empresa = db_session.query(Empresa).first()
    empresa.documento, empresa.indicador_ie, empresa.inscricao_estadual = CNPJ_VALIDO, "1", "123456789"
    db_session.add(EmpresaFiscalSettings(empresa_id=empresa.id, serie_nfe=1, ultimo_numero_nfe=10,
                                         ambiente_emissao=2, numeracao_confirmada=True))
    db_session.commit()
    token = {"sub": "1", "nome": "Admin Master", "empresa_id": empresa.id, "is_master": True,
             "permissoes": {"all": True}}
    app.dependency_overrides[requer_modulo_fiscal] = lambda: token
    yield empresa
    app.dependency_overrides.pop(requer_modulo_fiscal, None)


@pytest.fixture
def ligado(api, db_session, fiscal_liberado) -> ConfiguracaoMarcenaria:
    """Produtos acabados com o fiscal preenchido (como o contador faria) e o faturamento ligado."""
    api.client.post(f"{URL_CONFIG}/produtos-acabados", headers=api.header)
    r = api.client.put(URL_CONFIG, json={"faturamento_modo": "NOTA_NA_ENTREGA"}, headers=api.header)
    assert r.status_code == 200, r.text
    db_session.expire_all()
    config = db_session.query(ConfiguracaoMarcenaria).one()
    for produto_id, cfop in ((config.produto_acabado_padrao_id, "5101"), (config.produto_acabado_revenda_id, "5102")):
        fiscal = db_session.query(ProdutoFiscal).filter_by(produto_id=produto_id).first()
        if fiscal is None:
            fiscal = ProdutoFiscal(produto_id=produto_id)
            db_session.add(fiscal)
        fiscal.ncm, fiscal.cfop_padrao, fiscal.origem_mercadoria = "94034000", cfop, 0
        fiscal.csosn, fiscal.unidade_tributavel = "102", "UN"
    db_session.commit()
    return config


@pytest.fixture
def obra(api, fornecedor, cliente_id) -> Producao:
    _d, numero = _aprovar_obra(api, cliente_id, fornecedor("Madeiranit"))
    return Producao(api, numero)


def _url(obra, caminho=""):
    return f"/api/v1/marcenaria/os/{obra.numero_os}/faturamento{caminho}"


def _emitir(api, obra, *nomes):
    ids = [obra.movel(nome)["movel_id"] for nome in nomes]
    return api.client.post(_url(obra, "/emitir"), json={"movel_ids": ids}, headers=api.header)


def _estoque(db, produto_id):
    db.expire_all()
    return db.get(Produto, produto_id).estoque.quantidade


def test_movel_que_nao_esta_pronto_nao_entra(api, obra, ligado, plataforma):
    r = _emitir(api, obra, "Balcão")
    assert r.status_code == 409, r.text
    assert "Balcão" in r.json()["detail"]


def test_nota_autorizada_tira_do_estoque_e_trava_o_movel(api, obra, ligado, plataforma, db_session):
    obra.concluir(*_todas(obra.ler(), "Balcão"))
    plataforma.respostas = [AUTORIZADA(11)]

    r = _emitir(api, obra, "Balcão")

    assert r.status_code == 200, r.text
    assert r.json()["status"] == "AUTORIZADA"
    (payload,) = plataforma.payloads
    (item,) = payload["items"]
    assert item["descricao"] == "Balcão — Cozinha" and item["cfop"] == "5101" and item["ncm"] == "94034000"
    assert _estoque(db_session, ligado.produto_acabado_padrao_id) == 0
    painel = api.client.get(_url(obra), headers=api.header).json()
    balcao = next(m for m in painel["moveis"] if m["nome"] == "Balcão")
    assert balcao["situacao"] == "FATURADO" and balcao["documento"]["numero"] == 11
    # O mesmo movel nao vai para uma segunda nota.
    assert _emitir(api, obra, "Balcão").status_code == 409


def test_rejeitada_devolve_ao_estoque_e_libera_o_movel(api, obra, ligado, plataforma, db_session):
    obra.concluir(*_todas(obra.ler(), "Balcão"))
    plataforma.respostas = [REJEITADA, AUTORIZADA(12)]

    assert _emitir(api, obra, "Balcão").json()["status"] == "REJEITADA"
    assert _estoque(db_session, ligado.produto_acabado_padrao_id) == 1
    assert db_session.query(MarcenariaMovelFaturamento).one().situacao == "NO_ESTOQUE"

    assert _emitir(api, obra, "Balcão").json()["status"] == "AUTORIZADA"   # corrigido o cadastro, emite de novo


def test_uma_nota_por_entrega(api, obra, ligado, plataforma, db_session):
    obra.concluir(*_todas(obra.ler(), "Balcão", "Aéreo"))
    plataforma.respostas = [AUTORIZADA(13), AUTORIZADA(14)]

    assert _emitir(api, obra, "Balcão").json()["status"] == "AUTORIZADA"
    assert _emitir(api, obra, "Aéreo").json()["status"] == "AUTORIZADA"

    assert db_session.query(DocumentoFiscal).count() == 2
    assert len(api.client.get(_url(obra), headers=api.header).json()["notas"]) == 2


def test_cancelar_a_nota_devolve_o_movel(api, obra, ligado, plataforma, db_session):
    from app.services.fiscal.eventos.consulta_cancelamento import cancelar_documento

    obra.concluir(*_todas(obra.ler(), "Balcão"))
    plataforma.respostas = [AUTORIZADA(15)]
    doc_id = _emitir(api, obra, "Balcão").json()["documento_id"]

    cancelar_documento(db_session, doc_id, ligado.empresa_id, "Cliente pediu outra cor de puxador")
    db_session.commit()

    assert _estoque(db_session, ligado.produto_acabado_padrao_id) == 1
    assert db_session.query(MarcenariaMovelFaturamento).one().situacao == "NO_ESTOQUE"


def test_preview_nao_reserva_numero(api, obra, ligado, plataforma, db_session):
    obra.concluir(*_todas(obra.ler(), "Balcão"))
    ids = [obra.movel("Balcão")["movel_id"]]

    r = api.client.post(_url(obra, "/preview"), json={"movel_ids": ids}, headers=api.header)

    assert r.status_code == 200, r.text
    assert [i["descricao"] for i in r.json()["itens"]] == ["Balcão — Cozinha"]
    db_session.expire_all()
    assert db_session.query(EmpresaFiscalSettings).one().ultimo_numero_nfe == 10
    assert db_session.query(DocumentoFiscal).count() == 0


def test_desligado_recusa(api, obra, fiscal_liberado, plataforma):
    obra.concluir(*_todas(obra.ler(), "Balcão"))
    r = _emitir(api, obra, "Balcão")
    assert r.status_code == 409 and "desligado" in r.json()["detail"]


def test_caminho_da_os_comum_recusa_a_os_da_marcenaria(api, obra, fiscal_liberado, db_session):
    """Antes, este caminho emitia a nota so com as chapas a R$ 0 (ver F0)."""
    from app.services.fiscal.emissoes.nfe_os import preview_nfe_os
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as erro:
        preview_nfe_os(db_session, obra.numero_os, fiscal_liberado.id)
    assert erro.value.detail["codigo"] == "OS_DA_MARCENARIA"
