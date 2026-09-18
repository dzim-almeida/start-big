# ---------------------------------------------------------------------------
# ARQUIVO: test/services/fiscal/test_carta_correcao.py
# DESCRIÇÃO: TASK002 — Carta de Correção Eletrônica (CC-e) na NF-e.
#
# A carta é um EVENTO anexo à nota, como o cancelamento: não consome número,
# não muda a nota, não mexe em estoque. O que se testa aqui é o registro do
# evento, as travas antes de chamar a emissora e o mapeamento da resposta da
# Focus (via plataforma) para o registro local.
# ---------------------------------------------------------------------------

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models.carta_correcao_fiscal import CartaCorrecaoFiscal
from app.db.models.documento_fiscal import DocumentoFiscal
from app.db.models.empresa import Empresa
from app.db.models.empresa_fiscal_settings import EmpresaFiscalSettings
from app.schemas.emissao_fiscal import CartaCorrecaoRequest
from app.services.fiscal.carta_correcao import (
    LIMITE_CARTAS_POR_NOTA,
    emitir_carta_correcao,
    listar_cartas_correcao,
)
from app.services.fiscal.http.client import RESULTADO_NAO_TRANSMITIDO
from app.services.fiscal.http.client_mock import FiscalClientMock

EMPRESA_ID = 1
CORRECAO = "Corrigido o complemento do endereço do destinatário: sala 302."
CHAVE = "35260911222333000181550010000000421000000429"


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    sessao = Session()
    yield sessao
    sessao.close()


@pytest.fixture
def empresa(db):
    db.add(Empresa(
        id=EMPRESA_ID, razao_social="Loja Teste LTDA",
        documento="11222333000181", is_cnpj=True,
        regime_tributario="Simples Nacional",
    ))
    db.flush()
    db.add(EmpresaFiscalSettings(
        empresa_id=EMPRESA_ID, serie_nfe=1, ultimo_numero_nfe=42, ambiente_emissao=2,
    ))
    db.commit()


def _doc(db, tipo="NFE", status_doc="AUTORIZADA", ref="nfe-1", **campos):
    doc = DocumentoFiscal(
        tipo_documento=tipo, origem_tipo="VENDA", origem_id=1,
        numero_documento=42, serie=1, status=status_doc, ref_api=ref,
        chave_acesso=CHAVE, protocolo_autorizacao="135260000000001",
        valor_total=10000, **campos,
    )
    db.add(doc)
    db.commit()
    return doc


class ClientEspiao(FiscalClientMock):
    """Mock que registra as chamadas — para provar que NÃO houve chamada."""

    def __init__(self):
        super().__init__(delay=0)
        self.chamadas = []

    def emitir_carta_correcao(self, ref, correcao):
        self.chamadas.append((ref, correcao))
        return super().emitir_carta_correcao(ref, correcao)


@pytest.fixture
def client(monkeypatch):
    espiao = ClientEspiao()
    monkeypatch.setattr(
        "app.services.fiscal.carta_correcao.get_fiscal_client", lambda *a, **k: espiao,
    )
    monkeypatch.setattr("app.services.fiscal.carta_correcao.crud.get_licenca_token", lambda _db: "tok")
    return espiao


def _snapshot(doc):
    return {
        c: getattr(doc, c) for c in (
            "status", "chave_acesso", "numero_documento", "serie",
            "protocolo_autorizacao", "valor_total", "mensagem_sefaz",
        )
    }


# =========================
# 1. Schema
# =========================

def test_correcao_curta_e_recusada():
    with pytest.raises(ValueError, match="15"):
        CartaCorrecaoRequest(correcao="curta demais")


def test_correcao_longa_e_recusada():
    with pytest.raises(ValueError, match="1000"):
        CartaCorrecaoRequest(correcao="x" * 1001)


def test_correcao_e_normalizada_sem_espacos_nas_bordas():
    assert CartaCorrecaoRequest(correcao=f"  {CORRECAO}  ").correcao == CORRECAO


# =========================
# 2. Travas ANTES da emissora
# =========================

def test_nfce_nao_recebe_carta_e_nao_chama_o_client(db, empresa, client):
    doc = _doc(db, tipo="NFCE")
    with pytest.raises(HTTPException) as exc:
        emitir_carta_correcao(db, doc.id, EMPRESA_ID, CORRECAO, usuario_id=1)
    assert exc.value.status_code == 422
    assert exc.value.detail["codigo"] == "CCE_SOMENTE_NFE"
    assert client.chamadas == []


@pytest.mark.parametrize("status_doc", ["CANCELADA", "REJEITADA", "PROCESSANDO", "NAO_TRANSMITIDA"])
def test_so_nfe_autorizada_recebe_carta(db, empresa, client, status_doc):
    doc = _doc(db, status_doc=status_doc)
    with pytest.raises(HTTPException) as exc:
        emitir_carta_correcao(db, doc.id, EMPRESA_ID, CORRECAO, usuario_id=1)
    assert exc.value.status_code == 422
    assert client.chamadas == []


def test_documento_inexistente_da_404(db, empresa, client):
    with pytest.raises(HTTPException) as exc:
        emitir_carta_correcao(db, 999, EMPRESA_ID, CORRECAO, usuario_id=1)
    assert exc.value.status_code == 404


def test_documento_sem_ref_api_e_recusado(db, empresa, client):
    doc = _doc(db, ref=None)
    with pytest.raises(HTTPException) as exc:
        emitir_carta_correcao(db, doc.id, EMPRESA_ID, CORRECAO, usuario_id=1)
    assert exc.value.status_code == 422
    assert client.chamadas == []


def test_limite_de_20_cartas_e_barrado_localmente(db, empresa, client):
    doc = _doc(db)
    for i in range(LIMITE_CARTAS_POR_NOTA):
        db.add(CartaCorrecaoFiscal(
            empresa_id=EMPRESA_ID, documento_id=doc.id, sequencia=i + 1,
            correcao=CORRECAO, status="AUTORIZADA",
        ))
    db.commit()

    with pytest.raises(HTTPException) as exc:
        emitir_carta_correcao(db, doc.id, EMPRESA_ID, CORRECAO, usuario_id=1)
    assert exc.value.status_code == 422
    assert exc.value.detail["codigo"] == "CCE_LIMITE_ATINGIDO"
    assert client.chamadas == []


def test_cartas_rejeitadas_nao_contam_no_limite(db, empresa, client):
    doc = _doc(db)
    for _ in range(LIMITE_CARTAS_POR_NOTA):
        db.add(CartaCorrecaoFiscal(
            empresa_id=EMPRESA_ID, documento_id=doc.id,
            correcao=CORRECAO, status="REJEITADA",
        ))
    db.commit()

    carta = emitir_carta_correcao(db, doc.id, EMPRESA_ID, CORRECAO, usuario_id=1)
    assert carta.status == "AUTORIZADA"


def test_carta_em_processamento_bloqueia_outra_na_mesma_nota(db, empresa, client):
    doc = _doc(db)
    db.add(CartaCorrecaoFiscal(
        empresa_id=EMPRESA_ID, documento_id=doc.id, correcao=CORRECAO, status="PROCESSANDO",
    ))
    db.commit()

    with pytest.raises(HTTPException) as exc:
        emitir_carta_correcao(db, doc.id, EMPRESA_ID, CORRECAO, usuario_id=1)
    assert exc.value.status_code == 409
    assert client.chamadas == []


# =========================
# 3. Sucesso: registro e imutabilidade da nota
# =========================

def test_carta_autorizada_grava_sequencia_protocolo_e_mensagem(db, empresa, client):
    doc = _doc(db)
    carta = emitir_carta_correcao(db, doc.id, EMPRESA_ID, CORRECAO, usuario_id=7)

    assert client.chamadas == [("nfe-1", CORRECAO)]
    assert carta.status == "AUTORIZADA"
    assert carta.sequencia == 1
    assert carta.codigo_status_sefaz == 135
    assert carta.protocolo
    assert carta.mensagem_sefaz
    assert carta.usuario_id == 7
    assert carta.data_evento is not None
    assert carta.ambiente_emissao == 2


def test_sequencia_vem_da_emissora_e_cresce(db, empresa, client):
    doc = _doc(db)
    primeira = emitir_carta_correcao(db, doc.id, EMPRESA_ID, CORRECAO, usuario_id=1)
    segunda = emitir_carta_correcao(db, doc.id, EMPRESA_ID, CORRECAO + " E o CEP.", usuario_id=1)
    assert (primeira.sequencia, segunda.sequencia) == (1, 2)


def test_carta_nao_altera_a_nota(db, empresa, client):
    doc = _doc(db, mensagem_sefaz="Autorizado o uso da NF-e")
    antes = _snapshot(doc)

    emitir_carta_correcao(db, doc.id, EMPRESA_ID, CORRECAO, usuario_id=1)
    db.refresh(doc)

    assert _snapshot(doc) == antes
    assert doc.status == "AUTORIZADA"


# =========================
# 4. Rejeição da SEFAZ ≠ erro da plataforma
# =========================

def test_rejeicao_da_sefaz_vira_registro_rejeitado_sem_excecao(db, empresa, client, monkeypatch):
    doc = _doc(db)
    monkeypatch.setattr(client, "emitir_carta_correcao", lambda ref, correcao: {
        "status": "erro_autorizacao", "codigo_sefaz": 573,
        "mensagem_sefaz": "Rejeição: Duplicidade de Evento", "numero_carta_correcao": None,
    })

    carta = emitir_carta_correcao(db, doc.id, EMPRESA_ID, CORRECAO, usuario_id=1)

    assert carta.status == "REJEITADA"
    assert carta.codigo_status_sefaz == 573
    assert "Duplicidade" in carta.mensagem_sefaz
    assert carta.sequencia is None


def test_recusa_da_plataforma_vira_erro_e_nao_rejeitada(db, empresa, client, monkeypatch):
    doc = _doc(db)
    monkeypatch.setattr(client, "emitir_carta_correcao", lambda ref, correcao: {
        "status": RESULTADO_NAO_TRANSMITIDO,
        "mensagem_sefaz": "A plataforma recusou (HTTP 400) antes de enviar a SEFAZ.",
    })

    carta = emitir_carta_correcao(db, doc.id, EMPRESA_ID, CORRECAO, usuario_id=1)

    assert carta.status == "ERRO"
    assert carta.codigo_status_sefaz is None


def test_falha_de_rede_vira_502_e_o_pedido_fica_registrado_como_erro(db, empresa, client, monkeypatch):
    doc = _doc(db)

    def explode(ref, correcao):
        raise ConnectionError("timeout")

    monkeypatch.setattr(client, "emitir_carta_correcao", explode)

    with pytest.raises(HTTPException) as exc:
        emitir_carta_correcao(db, doc.id, EMPRESA_ID, CORRECAO, usuario_id=1)
    assert exc.value.status_code == 502

    [carta] = listar_cartas_correcao(db, doc.id, EMPRESA_ID)
    assert carta.status == "ERRO"


# =========================
# 5. Listagem
# =========================

def test_listagem_vem_por_sequencia(db, empresa, client):
    doc = _doc(db)
    for i in (3, 1, 2):
        db.add(CartaCorrecaoFiscal(
            empresa_id=EMPRESA_ID, documento_id=doc.id, sequencia=i,
            correcao=CORRECAO, status="AUTORIZADA",
        ))
    db.commit()

    assert [c.sequencia for c in listar_cartas_correcao(db, doc.id, EMPRESA_ID)] == [1, 2, 3]


def test_listagem_de_documento_inexistente_da_404(db, empresa, client):
    with pytest.raises(HTTPException) as exc:
        listar_cartas_correcao(db, 999, EMPRESA_ID)
    assert exc.value.status_code == 404


# =========================
# 6. Arquivos: a carta não sobrescreve o XML da nota e entra na sincronização
# =========================

@pytest.fixture
def pasta_isolada(tmp_path, monkeypatch):
    from app.services.fiscal import arquivos
    monkeypatch.setattr(arquivos, "PASTA_FISCAL", str(tmp_path / "fiscal"))
    monkeypatch.setattr(arquivos, "PASTA_DANFE", str(tmp_path / "danfe"))
    return tmp_path


def test_xml_da_carta_e_guardado_com_sufixo_e_nao_no_lugar_da_nota(db, empresa, client, pasta_isolada, monkeypatch):
    from app.services.fiscal import arquivos

    doc = _doc(db)
    caminho_da_nota = arquivos.guardar_xml("<nfe/>", chave=CHAVE, fallback="x")
    assert caminho_da_nota and caminho_da_nota.endswith(f"{CHAVE}.xml")

    monkeypatch.setattr(client, "emitir_carta_correcao", lambda ref, correcao: {
        "status": "autorizado", "codigo_sefaz": 135, "protocolo": "135000000000001",
        "mensagem_sefaz": "Evento registrado", "numero_carta_correcao": 1,
        "url_xml": "/arquivos/cce.xml", "url_pdf": None,
    })
    monkeypatch.setattr(client, "baixar_xml", lambda url: "<evento/>")

    carta = emitir_carta_correcao(db, doc.id, EMPRESA_ID, CORRECAO, usuario_id=1)

    assert carta.caminho_xml_local and carta.caminho_xml_local.endswith(f"{CHAVE}_cce_01.xml")
    assert open(caminho_da_nota, encoding="utf-8").read() == "<nfe/>"


def test_sincronizacao_baixa_o_xml_da_carta_que_ficou_sem_arquivo(db, empresa, client, pasta_isolada, monkeypatch):
    from app.services.fiscal.arquivos import sincronizar_pendentes

    doc = _doc(db)
    db.add(CartaCorrecaoFiscal(
        empresa_id=EMPRESA_ID, documento_id=doc.id, sequencia=2, correcao=CORRECAO,
        status="AUTORIZADA", url_xml="/arquivos/cce2.xml",
    ))
    db.commit()
    monkeypatch.setattr(client, "baixar_xml", lambda url: "<evento n='2'/>")

    resumo = sincronizar_pendentes(db, client)

    [carta] = listar_cartas_correcao(db, doc.id, EMPRESA_ID)
    assert carta.caminho_xml_local and carta.caminho_xml_local.endswith(f"{CHAVE}_cce_02.xml")
    assert resumo["guardados"] == 1
