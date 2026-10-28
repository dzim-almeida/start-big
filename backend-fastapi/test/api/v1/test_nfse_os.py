# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/test_nfse_os.py
# DESCRICAO: NFS-e da mao de obra da OS (F3 do docs/nfse-plano.md), com a
#            plataforma simulada. O caso e o do canario: MEI em Iguatu/CE,
#            suporte em informatica (01.07.01 / NBS 1.1501.30.00).
# ---------------------------------------------------------------------------

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.enum import OrdemServicoStatus
from app.db.crud import fiscal as crud
from app.db.models.documento_fiscal import DocumentoFiscal
from app.db.models.empresa import Empresa
from app.db.models.empresa_fiscal_settings import EmpresaFiscalSettings
from app.db.models.endereco import Endereco
from app.db.models.ordem_servico import OrdemServico
from app.db.models.ordem_servico_nota_fiscal import OrdemServicoNotaFiscal
from app.main import app

from test.apoio_orcamento_marcenaria import _criar_loja

NFSE = "/api/v1/fiscal/nfse"
OS_URL = "/api/v1/ordens-servico"
CNPJ_MEI = "66544279000100"


class PlataformaFalsa:
    """O client fiscal, gravando o que recebeu e respondendo o roteiro."""

    def __init__(self):
        self.enviados = []
        self.resposta = {
            "status": "autorizado", "numero": 74798, "codigo_verificacao": "ABC123",
            "url_pdf": "https://homologacao.focusnfe.com.br/arquivos/danfse.pdf",
            "url_consulta": "https://www.nfse.gov.br/consultapublica?chave=1",
            "mensagem_sefaz": None,
        }
        self.falha = None

    def emitir_nfse(self, ref, payload, idempotency_key=None, confirmar_duplicidade=False):
        self.enviados.append((ref, payload))
        if self.falha:
            raise self.falha
        return dict(self.resposta)

    def baixar_xml(self, caminho):
        return None

    def baixar_pdf(self, caminho):
        return None


@pytest.fixture
def client():
    yield TestClient(app)


@pytest.fixture
def plataforma(monkeypatch):
    falsa = PlataformaFalsa()
    monkeypatch.setattr("app.services.fiscal.nfse.emissao_os.get_fiscal_client", lambda *a, **k: falsa)
    return falsa


@pytest.fixture
def licenca(monkeypatch):
    from app.core import modulos as modulos_mod

    def _com(*modulos):
        monkeypatch.setattr(modulos_mod.licenca_service, "modulos_da_licenca", lambda db: list(modulos))
    _com("NFSE")
    return _com


@pytest.fixture
def loja(client, db_session, licenca) -> dict:
    """MEI de Iguatu/CE, so com a NFS-e."""
    header = _criar_loja(client, "assistencia_tecnica")
    empresa = db_session.query(Empresa).first()
    empresa.documento = CNPJ_MEI
    empresa.crt = 4
    end = db_session.query(Endereco).filter(Endereco.id_entidade == empresa.id).first()
    end.cidade, end.estado = "Iguatu", "CE"
    db_session.add(EmpresaFiscalSettings(empresa_id=empresa.id, serie_nfe=1, ultimo_numero_nfe=0, ambiente_emissao=2))
    db_session.commit()
    return header


@pytest.fixture
def servico(client, loja) -> int:
    r = client.post("/api/v1/servicos/", json={"descricao": "Suporte em informatica", "valor": 15000}, headers=loja)
    assert r.status_code == 201, r.text
    sid = r.json()["id"]
    r = client.put(f"/api/v1/servicos/{sid}/fiscal", json={
        "codigo_servico_lc116": "01.07", "codigo_tributacao_nacional": "01.07.01", "codigo_nbs": "1.1501.30.00",
    }, headers=loja)
    assert r.status_code == 200, r.text
    return sid


def _criar_os(client, loja, db_session, itens, desconto=0, finalizar=True) -> str:
    cliente = client.post("/api/v1/clientes/cliente_pf", json={"nome": "Maria Souza", "cpf": "11144477735", "tipo": "PF"},
                          headers=loja).json()["id"]
    r = client.post(f"{OS_URL}/", json={
        "cliente_id": cliente, "prioridade": "NORMAL", "defeito_relatado": "Notebook lento", "dados_adicionais": {},
        "objeto": {"marca": "Dell", "modelo": "G15", "numero_serie": "SN12345"},
        "itens": itens,
    }, headers=loja)
    assert r.status_code == 201, r.text
    numero = r.json()["numero_os"]
    os_obj = db_session.query(OrdemServico).filter_by(numero_os=numero).first()
    if desconto:
        os_obj.desconto = desconto
    if finalizar:
        os_obj.status = OrdemServicoStatus.FINALIZADA
    db_session.commit()
    return numero


def _item_servico(servico_id=None, valor=15000, nome="Formatacao e backup"):
    item = {"tipo": "SERVICO", "nome": nome, "unidade_medida": "UN", "quantidade": 1, "valor_unitario": valor}
    if servico_id:
        item["item_id"] = servico_id
    return item


# =========================
# Trava e conferencia
# =========================

def test_sem_o_modulo_nfse_nao_emite(client, loja, servico, db_session, licenca, plataforma):
    numero = _criar_os(client, loja, db_session, [_item_servico(servico)])
    licenca("NFE")
    r = client.post(f"{NFSE}/os/{numero}/emitir", headers=loja)
    assert r.status_code == 403
    assert plataforma.enviados == []


def test_servico_avulso_e_sem_codigos_viram_pendencia_nomeada(client, loja, db_session, plataforma):
    sem_codigo = client.post("/api/v1/servicos/", json={"descricao": "Limpeza", "valor": 5000}, headers=loja).json()["id"]
    numero = _criar_os(client, loja, db_session, [_item_servico(), _item_servico(sem_codigo, nome="Limpeza interna")])

    r = client.get(f"{NFSE}/os/{numero}/verificar", headers=loja)

    campos = {p["campo"] for p in r.json()["pendencias"]}
    assert r.json()["completo"] is False
    assert {"avulso_servico", "codigo_tributacao_nacional"} <= campos
    r = client.post(f"{NFSE}/os/{numero}/emitir", headers=loja)
    assert r.status_code == 422 and r.json()["detail"]["codigo"] == "PENDENCIAS_FISCAIS"
    assert plataforma.enviados == []


def test_os_nao_finalizada_nao_emite(client, loja, servico, db_session, plataforma):
    numero = _criar_os(client, loja, db_session, [_item_servico(servico)], finalizar=False)
    assert client.post(f"{NFSE}/os/{numero}/emitir", headers=loja).status_code == 422
    assert plataforma.enviados == []


# =========================
# Emissao
# =========================

def test_emite_a_dps_do_mei_de_iguatu(client, loja, servico, db_session, plataforma):
    numero = _criar_os(client, loja, db_session, [
        _item_servico(servico, 15000),
        {"tipo": "PRODUTO", "nome": "Pente de memoria", "unidade_medida": "UN", "quantidade": 1, "valor_unitario": 25000},
    ], desconto=4000)

    r = client.post(f"{NFSE}/os/{numero}/emitir", headers=loja)

    assert r.status_code == 200, r.text
    assert r.json()["status"] == "AUTORIZADA"
    ref, dps = plataforma.enviados[0]
    assert ref == f"os-{numero}-nfse"
    assert dps["cnpj_prestador"] == CNPJ_MEI
    assert dps["codigo_opcao_simples_nacional"] == "2"            # MEI
    assert dps["codigo_municipio_emissora"] == 2305506            # Iguatu/CE
    assert dps["codigo_municipio_prestacao"] == "2305506"
    assert dps["codigo_tributacao_nacional_iss"] == "010701"
    assert dps["codigo_nbs"] == "115013000"
    assert dps["valor_servico"] == 150.0                          # so o servico, nao a peca
    assert dps["desconto_incondicionado"] == 15.0                 # 40,00 x 150/400
    assert dps["cpf_tomador"] == "11144477735"
    assert "percentual_aliquota_relativa_municipio" not in dps    # MEI: ISS no DAS
    assert "serie_dps" not in dps and "numero_dps" not in dps     # D3: a Focus numera

    doc = db_session.query(DocumentoFiscal).filter_by(tipo_documento="NFSE").one()
    assert (doc.numero_documento, doc.valor_total) == (74798, 13500)
    nota = db_session.query(OrdemServicoNotaFiscal).filter_by(os_id=doc.origem_id).one()
    assert (nota.status_nfse, nota.numero_nfse, nota.codigo_verificacao_nfse) == ("AUTORIZADA", "74798", "ABC123")
    assert nota.url_nfse == "https://www.nfse.gov.br/consultapublica?chave=1"


def test_nfse_nao_trava_a_nfe_das_pecas_e_nao_repete(client, loja, servico, db_session, plataforma):
    numero = _criar_os(client, loja, db_session, [_item_servico(servico)])
    assert client.post(f"{NFSE}/os/{numero}/emitir", headers=loja).status_code == 200

    assert crud.get_documento_ativo_por_os(db_session, numero) is None   # a NF-e continua livre
    assert crud.contar_documentos_por_os(db_session, numero) == 0
    r = client.post(f"{NFSE}/os/{numero}/emitir", headers=loja)
    assert r.status_code == 409 and r.json()["detail"]["codigo"] == "NFSE_JA_AUTORIZADA"
    assert len(plataforma.enviados) == 1


def test_sem_resposta_vira_indeterminada_e_nao_rejeitada(client, loja, servico, db_session, plataforma):
    plataforma.falha = TimeoutError("sem resposta")
    numero = _criar_os(client, loja, db_session, [_item_servico(servico)])

    r = client.post(f"{NFSE}/os/{numero}/emitir", headers=loja)

    assert r.json()["status"] == "INDETERMINADA"
    r = client.post(f"{NFSE}/os/{numero}/emitir", headers=loja)
    assert r.status_code == 409 and r.json()["detail"]["codigo"] == "NFSE_INDETERMINADA"


def test_rejeitada_libera_nova_tentativa_com_outra_ref(client, loja, servico, db_session, plataforma):
    plataforma.resposta = {"status": "erro", "status_focus": "erro_autorizacao", "codigo_erro": "E0312",
                           "mensagem_sefaz": "E0312 - Código de tributação nacional inexistente"}
    numero = _criar_os(client, loja, db_session, [_item_servico(servico)])
    assert client.post(f"{NFSE}/os/{numero}/emitir", headers=loja).json()["status"] == "REJEITADA"

    plataforma.resposta = {"status": "autorizado", "numero": 2}
    r = client.post(f"{NFSE}/os/{numero}/emitir", headers=loja)

    assert r.json()["status"] == "AUTORIZADA"
    assert plataforma.enviados[1][0] == f"os-{numero}-nfse-2"


def test_os_da_marcenaria_ainda_nao_emite_nfse(client, loja, servico, db_session, plataforma):
    numero = _criar_os(client, loja, db_session, [_item_servico(servico)])
    os_obj = db_session.query(OrdemServico).filter_by(numero_os=numero).first()
    os_obj.itens[0].origem = "ORCAMENTO_MARCENARIA"
    db_session.commit()

    r = client.post(f"{NFSE}/os/{numero}/emitir", headers=loja)

    assert r.status_code == 422 and r.json()["detail"]["codigo"] == "OS_DA_MARCENARIA"


# =========================
# Cancelamento: o prazo e do municipio
# =========================

def test_nfse_nao_cai_no_prazo_de_30_minutos_da_nfce():
    from app.services.fiscal.eventos.consulta_cancelamento import _assert_dentro_da_janela_de_cancelamento

    doc = DocumentoFiscal(tipo_documento="NFSE", data_autorizacao=datetime.now(timezone.utc) - timedelta(days=3))
    _assert_dentro_da_janela_de_cancelamento(doc)          # nao levanta: quem decide e o Sistema Nacional


# =========================
# Client: a NFS-e usa a familia /erp/fiscal/nfse da plataforma
# =========================

def test_client_consulta_e_cancela_a_nfse_na_rota_dela():
    from app.services.fiscal.http.client_startbig import FiscalClientStartBig

    assert FiscalClientStartBig._segmento("NFSE") == "nfse"
    assert FiscalClientStartBig._segmento("NFE") == "nfe"       # o resto nao muda
    assert FiscalClientStartBig._segmento("NFCE") == "nfce"


def test_client_le_o_codigo_de_verificacao_e_o_erro_alfanumerico():
    from app.services.fiscal.http.client_startbig import FiscalClientStartBig

    r = FiscalClientStartBig()._parse_response({
        "status": "autorizado", "numero": 74798, "codigo_verificacao": "ABC123", "codigo_erro": None,
        "mensagem_sefaz": "ok",
    })
    assert (r["status"], r["numero"], r["codigo_verificacao"]) == ("autorizado", 74798, "ABC123")


def test_lista_as_nfse_com_o_codigo_de_verificacao(client, loja, servico, db_session, plataforma):
    numero = _criar_os(client, loja, db_session, [_item_servico(servico)])
    client.post(f"{NFSE}/os/{numero}/emitir", headers=loja)

    r = client.get(f"{NFSE}/documentos", headers=loja)

    assert r.status_code == 200, r.text
    [nota] = r.json()
    assert (nota["numero_os"], nota["status"], nota["numero"], nota["codigo_verificacao"]) == (numero, "AUTORIZADA", 74798, "ABC123")
    assert nota["tomador"] == "Maria Souza"


# =========================
# Franquia fiscal da plataforma (28/10/2026): nota repetida e recusas com codigo
# =========================

def test_nota_repetida_pergunta_e_a_confirmacao_reenvia(client, loja, servico, db_session, plataforma):
    numero = _criar_os(client, loja, db_session, [_item_servico(servico)])
    plataforma.resposta = {"status": "nao_transmitido", "codigo": "NOTA_DUPLICADA_SUSPEITA",
                           "mensagem_sefaz": 'Esta nota é igual à ref "os-9-nfse", autorizada há 3 min.'}

    r = client.post(f"{NFSE}/os/{numero}/emitir", headers=loja)

    assert r.status_code == 409
    assert r.json()["detail"]["codigo"] == "NOTA_DUPLICADA_SUSPEITA"
    assert "autorizada há 3 min" in r.json()["detail"]["mensagem"]
    assert db_session.query(DocumentoFiscal).filter_by(tipo_documento="NFSE").count() == 0  # nada ficou

    plataforma.resposta = {"status": "autorizado", "numero": 5}
    confirmados = []
    original = plataforma.emitir_nfse
    plataforma.emitir_nfse = lambda ref, payload, idempotency_key=None, confirmar_duplicidade=False: (
        confirmados.append(confirmar_duplicidade) or original(ref, payload, idempotency_key)
    )
    r = client.post(f"{NFSE}/os/{numero}/emitir", params={"confirmar_duplicidade": True}, headers=loja)

    assert r.json()["status"] == "AUTORIZADA"
    assert confirmados == [True]


def test_client_le_a_recusa_com_codigo_da_plataforma():
    """Antes vinha "Erro desconhecido": o corpo e {codigo, mensagem}, sem mensagem_sefaz."""
    from app.services.fiscal.http.client_startbig import FiscalClientStartBig

    r = FiscalClientStartBig()._parse_response({
        "codigo": "FRANQUIA_ESGOTADA", "mensagem": "As 70 notas do mês acabaram.",
    })
    assert (r["codigo"], r["mensagem_sefaz"]) == ("FRANQUIA_ESGOTADA", "As 70 notas do mês acabaram.")


# =========================
# F4: o ZIP do contador separa a NFS-e
# =========================

def test_pacote_do_contador_poe_a_nfse_na_pasta_dela(db_session, monkeypatch, loja):
    import io
    import zipfile
    from datetime import date

    from app.services.fiscal.documentos import exportacao_xml

    class Cliente:
        def baixar_xml(self, url):
            return "<NFSe/>"

    monkeypatch.setattr(exportacao_xml, "get_fiscal_client", lambda *a, **k: Cliente())
    monkeypatch.setattr(exportacao_xml, "guardar_xml", lambda *a, **k: None)   # nada no disco real
    db_session.add(DocumentoFiscal(
        tipo_documento="NFSE", origem_tipo="OS", origem_numero_os="OS-1", status="AUTORIZADA",
        numero_documento=74798, url_xml="https://x/nfse.xml", valor_total=15000,
        data_emissao=datetime.now(timezone.utc), data_autorizacao=datetime.now(timezone.utc),
    ))
    db_session.commit()
    empresa_id = db_session.query(Empresa).first().id

    conteudo, _resumo = exportacao_xml.montar_pacote_xml(db_session, empresa_id, date.today(), date.today())

    with zipfile.ZipFile(io.BytesIO(conteudo)) as z:
        nomes = z.namelist()
        assert "NFSe/NFSE-74798.xml" in nomes
        relacao = next(n for n in nomes if n.endswith(".csv"))
        linha = [l for l in z.read(relacao).decode("utf-8-sig").splitlines() if "74798" in l][0]
    assert linha.startswith("NFSE;")


def test_aba_nfse_baixa_o_zip_so_de_nfse_sem_o_modulo_nfe(client, loja, servico, db_session, plataforma, monkeypatch):
    from datetime import date

    from app.services.fiscal.documentos import exportacao_xml

    monkeypatch.setattr(exportacao_xml, "get_fiscal_client", lambda *a, **k: type("C", (), {"baixar_xml": lambda s, u: "<x/>"})())
    monkeypatch.setattr(exportacao_xml, "guardar_xml", lambda *a, **k: None)
    plataforma.resposta["url_xml"] = "https://x/nfse.xml"
    numero = _criar_os(client, loja, db_session, [_item_servico(servico)])
    client.post(f"{NFSE}/os/{numero}/emitir", headers=loja)
    hoje = date.today().isoformat()

    r = client.get(f"{NFSE}/exportar-xml", params={"data_inicio": hoje, "data_fim": hoje}, headers=loja)

    assert r.status_code == 200, r.text                     # licença só com NFSE
    assert r.headers["x-fiscal-documentos"] == "1"


# =========================
# G3: configuracao da NFS-e (as decisoes do contador viram opcao)
# =========================

def _segundo_servico(client, loja, codigo="140101", nbs="120100000", nome="Manutencao de impressora"):
    sid = client.post("/api/v1/servicos/", json={"descricao": nome, "valor": 8000}, headers=loja).json()["id"]
    r = client.put(f"/api/v1/servicos/{sid}/fiscal", json={
        "codigo_tributacao_nacional": codigo, "codigo_nbs": nbs,
    }, headers=loja)
    assert r.status_code == 200, r.text
    return sid


def test_configuracao_nasce_no_comportamento_da_fase_1(client, loja):
    r = client.get(f"{NFSE}/configuracao", headers=loja)
    assert r.status_code == 200, r.text
    assert r.json() == {
        "regime_tributacao_iss": None, "nfse_reter_iss_pj": False, "nfse_uma_nota_por_codigo": False,
        "nfse_ibs_cbs_cst": None, "nfse_ibs_cbs_cclass": None,
    }


def test_ibs_cbs_padrao_entra_quando_o_servico_nao_tem(client, loja, servico, db_session, plataforma):
    r = client.put(f"{NFSE}/configuracao", json={"nfse_ibs_cbs_cst": "000", "nfse_ibs_cbs_cclass": "000001"}, headers=loja)
    assert r.status_code == 200, r.text
    numero = _criar_os(client, loja, db_session, [_item_servico(servico)])

    client.post(f"{NFSE}/os/{numero}/emitir", headers=loja)

    dps = plataforma.enviados[0][1]
    assert (dps["ibs_cbs_situacao_tributaria"], dps["ibs_cbs_classificacao_tributaria"]) == ("000", "000001")


def test_retencao_so_para_tomador_pj_com_a_opcao(client, loja, servico, db_session, plataforma):
    client.put(f"{NFSE}/configuracao", json={"nfse_reter_iss_pj": True}, headers=loja)
    numero = _criar_os(client, loja, db_session, [_item_servico(servico)])   # tomador PF

    client.post(f"{NFSE}/os/{numero}/emitir", headers=loja)

    dps = plataforma.enviados[0][1]
    assert dps["tipo_retencao_iss"] == "1"          # pessoa fisica nao retem
    assert dps["consumidor_final"] == "1"


def test_codigos_diferentes_sao_pendencia_sem_a_opcao(client, loja, servico, db_session, plataforma):
    outro = _segundo_servico(client, loja)
    numero = _criar_os(client, loja, db_session, [_item_servico(servico, 15000), _item_servico(outro, 8000, "Impressora")])

    r = client.post(f"{NFSE}/os/{numero}/emitir", headers=loja)

    assert r.status_code == 422
    assert "codigos_diferentes" in {p["campo"] for p in r.json()["detail"]["pendencias"]}
    assert plataforma.enviados == []


def test_uma_nota_por_codigo_emite_cada_codigo_com_a_sua_trava(client, loja, servico, db_session, plataforma):
    client.put(f"{NFSE}/configuracao", json={"nfse_uma_nota_por_codigo": True}, headers=loja)
    outro = _segundo_servico(client, loja)
    numero = _criar_os(client, loja, db_session, [_item_servico(servico, 15000), _item_servico(outro, 5000, "Impressora")],
                       desconto=4000)

    preview = client.post(f"{NFSE}/os/{numero}/preview", headers=loja).json()
    assert [n["codigo"] for n in preview["notas"]] == ["010701", "140101"]

    sem_codigo = client.post(f"{NFSE}/os/{numero}/emitir", headers=loja)
    assert sem_codigo.status_code == 422 and sem_codigo.json()["detail"]["codigo"] == "NFSE_ESCOLHA_O_CODIGO"

    r1 = client.post(f"{NFSE}/os/{numero}/emitir", params={"codigo_nacional": "01.07.01"}, headers=loja)
    r2 = client.post(f"{NFSE}/os/{numero}/emitir", params={"codigo_nacional": "140101"}, headers=loja)
    assert (r1.json()["status"], r2.json()["status"]) == ("AUTORIZADA", "AUTORIZADA")

    (ref1, dps1), (ref2, dps2) = plataforma.enviados
    assert (ref1, ref2) == (f"os-{numero}-nfse-010701", f"os-{numero}-nfse-140101")
    assert (dps1["valor_servico"], dps2["valor_servico"]) == (150.0, 50.0)
    assert (dps1["desconto_incondicionado"], dps2["desconto_incondicionado"]) == (30.0, 10.0)   # 40 rateado
    repetida = client.post(f"{NFSE}/os/{numero}/emitir", params={"codigo_nacional": "140101"}, headers=loja)
    assert repetida.status_code == 409 and repetida.json()["detail"]["codigo"] == "NFSE_JA_AUTORIZADA"
    assert client.post(f"{NFSE}/os/{numero}/preview", headers=loja).json()["notas"][0]["ja_emitida"] is True


def test_codigo_de_verificacao_fica_no_documento(client, loja, servico, db_session, plataforma):
    numero = _criar_os(client, loja, db_session, [_item_servico(servico)])
    client.post(f"{NFSE}/os/{numero}/emitir", headers=loja)
    doc = db_session.query(DocumentoFiscal).filter_by(tipo_documento="NFSE").one()
    db_session.refresh(doc)
    assert doc.codigo_verificacao == "ABC123"


# =========================
# G4: NFS-e avulsa (sem OS)
# =========================

@pytest.fixture
def plataforma_avulsa(monkeypatch, plataforma):
    monkeypatch.setattr("app.services.fiscal.nfse.avulsa.get_fiscal_client", lambda *a, **k: plataforma)
    return plataforma


AVULSA = {
    "codigo_tributacao_nacional": "01.07.01", "codigo_nbs": "1.1501.30.00",
    "descricao": "Consultoria em informatica", "valor": 20000, "desconto": 2000,
    "tomador_documento": "11.222.333/0001-81", "tomador_nome": "Cliente LTDA", "tomador_email": "a@b.com",
}


def test_avulsa_emite_sem_os(client, loja, db_session, plataforma_avulsa):
    r = client.post(f"{NFSE}/avulsa/emitir", json=AVULSA, headers=loja)

    assert r.status_code == 200, r.text
    assert r.json()["status"] == "AUTORIZADA"
    ref, dps = plataforma_avulsa.enviados[0]
    assert ref.startswith("nfse-av-")
    assert dps["codigo_tributacao_nacional_iss"] == "010701"
    assert (dps["valor_servico"], dps["desconto_incondicionado"]) == (200.0, 20.0)
    assert dps["cnpj_tomador"] == "11222333000181"
    assert dps["consumidor_final"] == "0"                 # tomador empresa
    doc = db_session.query(DocumentoFiscal).filter_by(origem_tipo="AVULSA").one()
    assert (doc.valor_total, doc.destinatario_nome_enviado) == (18000, "Cliente LTDA")
    lista = client.get(f"{NFSE}/documentos", headers=loja).json()
    assert lista[0]["numero_os"] is None and lista[0]["tomador"] == "Cliente LTDA"


def test_avulsa_usa_os_codigos_do_servico_do_catalogo(client, loja, servico, plataforma_avulsa):
    corpo = {"servico_id": servico, "descricao": "Suporte remoto", "valor": 5000}
    r = client.post(f"{NFSE}/avulsa/preview", json=corpo, headers=loja)
    assert r.status_code == 200, r.text
    dps = r.json()["dps"]
    assert (dps["codigo_tributacao_nacional_iss"], dps["codigo_nbs"]) == ("010701", "115013000")
    assert "cpf_tomador" not in dps and "cnpj_tomador" not in dps     # sem tomador
    assert plataforma_avulsa.enviados == []                         # preview nao envia


def test_avulsa_sem_codigo_e_pendencia_nomeada(client, loja, plataforma_avulsa):
    r = client.post(f"{NFSE}/avulsa/emitir", json={"descricao": "Aula", "valor": 5000}, headers=loja)
    assert r.status_code == 422
    assert {"codigo_tributacao_nacional", "codigo_nbs"} <= {p["campo"] for p in r.json()["detail"]["pendencias"]}
    assert plataforma_avulsa.enviados == []


def test_avulsa_nota_repetida_nao_grava_documento(client, loja, db_session, plataforma_avulsa):
    plataforma_avulsa.resposta = {"status": "nao_transmitido", "codigo": "NOTA_DUPLICADA_SUSPEITA", "mensagem_sefaz": "igual"}
    r = client.post(f"{NFSE}/avulsa/emitir", json=AVULSA, headers=loja)
    assert r.status_code == 409
    assert db_session.query(DocumentoFiscal).filter_by(origem_tipo="AVULSA").count() == 0


def test_avulsa_sem_o_modulo_nao_emite(client, loja, licenca, plataforma_avulsa):
    licenca("NFE")
    assert client.post(f"{NFSE}/avulsa/emitir", json=AVULSA, headers=loja).status_code == 403
