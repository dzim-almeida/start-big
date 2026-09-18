# ---------------------------------------------------------------------------
# ARQUIVO: test/services/fiscal/test_emissao_devolucao.py
# DESCRIÇÃO: TASK003 — NF-e de devolução (modelo 55, entrada, finalidade 4).
#
# A devolução é uma EMISSÃO nova que referencia a nota original pela chave:
# consome número da NF-e, tem itens (os devolvidos, na quantidade devolvida),
# CFOP de entrada e pagamento "90 - sem pagamento". Os itens vêm do SNAPSHOT
# da nota original (o que a SEFAZ viu), nunca do cadastro atual.
# ---------------------------------------------------------------------------

from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.enum import EntityType, MovimentacaoOrigem, State
from app.db.base import Base
from app.db.crud import fiscal as crud
from app.db.models.aliquota_uf import AliquotaUF
from app.db.models.cliente import ClientePF
from app.db.models.documento_fiscal import DocumentoFiscal
from app.db.models.documento_fiscal_item import DocumentoFiscalItem
from app.db.models.empresa import Empresa
from app.db.models.empresa_fiscal_settings import EmpresaFiscalSettings
from app.db.models.endereco import Endereco
from app.db.models.estoque import Estoque
from app.db.models.funcionario import Funcionario
from app.db.models.movimentacao_estoque import MovimentacaoEstoque
from app.db.models.produto import Produto
from app.db.models.produto_fiscal import ProdutoFiscal
from app.db.models.venda import Venda
from app.schemas.emissao_fiscal import (
    DestinatarioAvulsoRequest,
    EmissaoDevolucaoRequest,
    ItemDevolucaoRequest,
)
from app.services.fiscal.derivacao.cfop import cfop_devolucao
from app.services.fiscal.devolucao import emitir_devolucao
from app.services.fiscal.http.client_mock import FiscalClientMock

EMPRESA_ID = 1
CHAVE = "35260911222333000181550010000000421000000429"
MOTIVO = "Cliente devolveu a mercadoria com defeito de fabrica."

DESTINATARIO = DestinatarioAvulsoRequest(
    cpf_ou_cnpj="123.456.789-09", nome_razao_social="Maria Silva",
    logradouro="Rua B", numero="20", bairro="Centro", codigo_municipio="3550308",
    municipio="Sao Paulo", uf="SP", cep="01001-000",
)


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
        id=EMPRESA_ID, razao_social="Loja Teste LTDA", documento="11222333000181",
        is_cnpj=True, regime_tributario="Simples Nacional", indicador_ie="1",
        inscricao_estadual="123456789", crt=1,
    ))
    db.flush()
    db.add(Endereco(
        id_entidade=EMPRESA_ID, tipo_entidade=EntityType.EMPRESA, logradouro="Rua A",
        numero="10", bairro="Centro", cidade="Sao Paulo", estado=State.SAO_PAULO, cep="01001000",
    ))
    db.add(EmpresaFiscalSettings(
        empresa_id=EMPRESA_ID, serie_nfe=1, ultimo_numero_nfe=42, ambiente_emissao=2,
        numeracao_confirmada=True,
    ))
    db.add(AliquotaUF(uf="SP", aliquota_icms_interna=1800, aliquota_pis_padrao=165, aliquota_cofins_padrao=760))
    db.commit()


def _produto(db, pid, nome, estoque=10):
    db.add(Produto(id=pid, nome=nome, codigo_produto=f"P{pid}", unidade_medida="UN"))
    db.flush()
    db.add(ProdutoFiscal(produto_id=pid, ncm="84716052", cfop_padrao="5102", origem_mercadoria=0,
                         unidade_tributavel="UN", csosn="102", cst_pis="49", cst_cofins="49"))
    db.add(Estoque(id=pid, quantidade=estoque, valor_varejo=10000))
    db.commit()


def _nota_original(db, tipo="NFE", com_destinatario=True, itens=None):
    """NF-e/NFC-e AUTORIZADA com snapshot de itens (o que a SEFAZ viu)."""
    doc = DocumentoFiscal(
        tipo_documento=tipo, origem_tipo="VENDA", origem_id=1, numero_documento=42,
        serie=1, status="AUTORIZADA", ref_api="venda-1", chave_acesso=CHAVE,
        protocolo_autorizacao="135260000000001", valor_total=30000, ambiente_emissao=2,
        destinatario_documento_enviado="12345678909" if com_destinatario else None,
        destinatario_nome_enviado="Maria Silva" if com_destinatario else None,
    )
    for numero, (pid, qtd_mil, unit, cfop) in enumerate(itens or [(1, 2000, 10000, "5102"), (2, 1000, 10000, "5405")], start=1):
        doc.itens.append(DocumentoFiscalItem(
            numero_item=numero, produto_id=pid, descricao=f"Produto {pid}", codigo_produto=f"P{pid}",
            unidade="UN", ncm="84716052", cfop=cfop, origem_mercadoria="0", situacao_tributaria="102",
            quantidade_milesimos=qtd_mil, valor_unitario=unit, valor_bruto=qtd_mil * unit // 1000,
            base_icms=0, valor_icms=0, aliquota_icms_centesimos=0,
        ))
    db.add(doc)
    db.commit()
    return doc


class ClientEspiao(FiscalClientMock):
    def __init__(self):
        super().__init__(delay=0)
        self.payloads = []

    def emitir_nfe(self, ref, payload, idempotency_key=None):
        self.payloads.append((ref, payload))
        return super().emitir_nfe(ref, payload, idempotency_key=idempotency_key)


@pytest.fixture
def client(monkeypatch):
    espiao = ClientEspiao()
    monkeypatch.setattr("app.services.fiscal.devolucao.get_fiscal_client", lambda *a, **k: espiao)
    monkeypatch.setattr("app.services.fiscal.devolucao.crud.get_licenca_token", lambda _db: "tok")
    return espiao


def _venda_com_cliente(db, numero_venda=1):
    """A venda de origem da NF-e, com cliente cadastrado e endereço completo."""
    cliente = ClientePF(id=1, nome="Maria Silva", cpf="12345678909")
    db.add(cliente)
    db.flush()
    db.add(Endereco(
        id_entidade=cliente.id, tipo_entidade=EntityType.CLIENTE, logradouro="Rua B",
        numero="20", bairro="Centro", cidade="Sao Paulo", estado=State.SAO_PAULO, cep="01001000",
    ))
    db.add(Funcionario(id=1, empresa_id=EMPRESA_ID, nome="Vendedor"))
    db.flush()
    db.add(Venda(id=1, numero_venda=numero_venda, cliente_id=cliente.id, funcionario_id=1,
                 subtotal=30000, total=30000, entrega=0, acrescimo=0))
    db.commit()


@pytest.fixture
def cenario(db, empresa, client):
    _produto(db, 1, "Teclado")
    _produto(db, 2, "Mouse")
    _venda_com_cliente(db)
    return _nota_original(db)


def _pedido(**campos) -> EmissaoDevolucaoRequest:
    base = dict(motivo=MOTIVO, devolver_estoque=True)
    base.update(campos)
    return EmissaoDevolucaoRequest(**base)


# =========================
# 1. CFOP saída -> entrada
# =========================

@pytest.mark.parametrize("saida, interestadual, esperado", [
    ("5102", False, "1202"),
    ("5101", False, "1201"),
    ("5405", False, "1411"),
    ("6102", True, "2202"),
    ("6101", True, "2201"),
    ("6403", True, "2411"),
    ("6404", True, "2411"),
    ("5999", False, "1202"),   # desconhecido: fallback interno
    ("6999", True, "2202"),    # desconhecido: fallback interestadual
    (None, False, "1202"),
])
def test_cfop_de_devolucao(saida, interestadual, esperado):
    assert cfop_devolucao(saida, interestadual) == esperado


# =========================
# 2. Schemas
# =========================

def test_motivo_curto_e_recusado():
    with pytest.raises(ValueError):
        EmissaoDevolucaoRequest(motivo="curto")


def test_destinatario_avulso_sanitiza_documento_e_cep():
    assert DESTINATARIO.cpf_ou_cnpj == "12345678909"
    assert DESTINATARIO.cep == "01001000"


def test_destinatario_contribuinte_exige_ie():
    with pytest.raises(ValueError, match="Inscrição Estadual"):
        DestinatarioAvulsoRequest(**{**DESTINATARIO.model_dump(), "indicador_inscricao_estadual": 1, "inscricao_estadual": None})


# =========================
# 3. Conformidade do payload (os 4 pilares)
# =========================

def test_payload_tem_os_quatro_pilares(db, cenario, client):
    emitir_devolucao(db, cenario.id, EMPRESA_ID, _pedido(), usuario_id=None)

    [(ref, payload)] = client.payloads
    assert ref.startswith(f"devolucao-{cenario.id}-")
    assert payload["modelo"] == 55
    assert payload["tipo_documento"] == 0
    assert payload["finalidade_emissao"] == 4
    assert payload["natureza_operacao"] == "DEVOLUCAO DE VENDA"
    assert payload["notas_referenciadas"] == [{"chave_nfe": CHAVE}]
    assert payload["formas_pagamento"] == [{"forma_pagamento": "90", "valor_pagamento": 0.0}]
    assert MOTIVO in payload["informacoes_adicionais_contribuinte"]


def test_itens_da_devolucao_total_espelham_o_snapshot_com_cfop_de_entrada(db, cenario, client):
    emitir_devolucao(db, cenario.id, EMPRESA_ID, _pedido(), usuario_id=None)

    itens = client.payloads[0][1]["items"]
    assert [(i["codigo_produto"], i["quantidade_comercial"], i["cfop"]) for i in itens] == [
        ("P1", 2.0, "1202"), ("P2", 1.0, "1411"),
    ]
    assert itens[0]["valor_bruto"] == 200.0
    assert itens[0]["icms_situacao_tributaria"] == "102"


def test_devolucao_parcial_recalcula_valores_pela_quantidade(db, cenario, client):
    item1 = cenario.itens[0]
    emitir_devolucao(
        db, cenario.id, EMPRESA_ID,
        _pedido(itens=[ItemDevolucaoRequest(documento_item_id=item1.id, quantidade=500)]),
        usuario_id=None,
    )

    [item] = client.payloads[0][1]["items"]
    assert item["quantidade_comercial"] == 0.5
    assert item["valor_bruto"] == 50.0
    assert client.payloads[0][1]["valor_total"] == 50.0


# =========================
# 4. Documento gerado
# =========================

def test_documento_de_devolucao_referencia_a_origem_e_consome_numero(db, cenario, client):
    doc = emitir_devolucao(db, cenario.id, EMPRESA_ID, _pedido(), usuario_id=None)

    assert doc.tipo_documento == "NFE"
    assert doc.finalidade_emissao == 4
    assert doc.documento_referenciado_id == cenario.id
    assert doc.chave_documento_referenciado == CHAVE
    assert doc.numero_documento == 43
    assert doc.status == "AUTORIZADA"
    assert crud.get_fiscal_settings(db, EMPRESA_ID).ultimo_numero_nfe == 43
    assert len(doc.itens) == 2


def test_origem_continua_intocada(db, cenario, client):
    emitir_devolucao(db, cenario.id, EMPRESA_ID, _pedido(), usuario_id=None)
    db.refresh(cenario)
    assert cenario.status == "AUTORIZADA"
    assert cenario.numero_documento == 42
    assert cenario.finalidade_emissao == 1


# =========================
# 5. Saldos: excedente, parciais consecutivas, esgotado
# =========================

def test_quantidade_acima_do_saldo_e_422(db, cenario, client):
    item1 = cenario.itens[0]
    with pytest.raises(HTTPException) as exc:
        emitir_devolucao(
            db, cenario.id, EMPRESA_ID,
            _pedido(itens=[ItemDevolucaoRequest(documento_item_id=item1.id, quantidade=2001)]),
            usuario_id=None,
        )
    assert exc.value.status_code == 422
    assert client.payloads == []


def test_duas_parciais_de_50_por_cento_e_a_terceira_e_barrada(db, cenario, client):
    item1, item2 = cenario.itens
    metade = lambda: _pedido(itens=[
        ItemDevolucaoRequest(documento_item_id=item1.id, quantidade=1000),
        ItemDevolucaoRequest(documento_item_id=item2.id, quantidade=500),
    ])

    emitir_devolucao(db, cenario.id, EMPRESA_ID, metade(), usuario_id=None)
    emitir_devolucao(db, cenario.id, EMPRESA_ID, metade(), usuario_id=None)
    db.refresh(item1)
    assert item1.quantidade_devolvida_acumulada == 2000

    with pytest.raises(HTTPException) as exc:
        emitir_devolucao(db, cenario.id, EMPRESA_ID, metade(), usuario_id=None)
    assert exc.value.status_code == 422
    assert len(client.payloads) == 2


def test_devolucao_total_de_nota_ja_devolvida_e_422(db, cenario, client):
    emitir_devolucao(db, cenario.id, EMPRESA_ID, _pedido(), usuario_id=None)
    with pytest.raises(HTTPException) as exc:
        emitir_devolucao(db, cenario.id, EMPRESA_ID, _pedido(), usuario_id=None)
    assert exc.value.status_code == 422
    assert "devolvida" in str(exc.value.detail).lower()


def test_item_de_outra_nota_e_422(db, cenario, client):
    with pytest.raises(HTTPException) as exc:
        emitir_devolucao(
            db, cenario.id, EMPRESA_ID,
            _pedido(itens=[ItemDevolucaoRequest(documento_item_id=9999, quantidade=1)]),
            usuario_id=None,
        )
    assert exc.value.status_code == 422


# =========================
# 6. Destinatário: nota anônima exige avulso
# =========================

def test_nfce_anonima_sem_destinatario_avulso_e_422(db, empresa, client):
    _produto(db, 1, "Teclado")
    doc = _nota_original(db, tipo="NFCE", com_destinatario=False, itens=[(1, 1000, 10000, "5102")])

    with pytest.raises(HTTPException) as exc:
        emitir_devolucao(db, doc.id, EMPRESA_ID, _pedido(), usuario_id=None)
    assert exc.value.status_code == 422
    assert "destinat" in str(exc.value.detail).lower()
    assert client.payloads == []


def test_nfce_anonima_com_destinatario_avulso_emite(db, empresa, client):
    _produto(db, 1, "Teclado")
    doc = _nota_original(db, tipo="NFCE", com_destinatario=False, itens=[(1, 1000, 10000, "5102")])

    novo = emitir_devolucao(db, doc.id, EMPRESA_ID, _pedido(destinatario_avulso=DESTINATARIO), usuario_id=None)

    assert novo.status == "AUTORIZADA"
    dest = client.payloads[0][1]["destinatario"]
    assert dest["cpf"] == "12345678909"
    assert dest["nome"] == "Maria Silva"
    assert dest["codigo_municipio"] == "3550308"


def test_nfe_com_cliente_cadastrado_usa_o_cadastro_como_destinatario(db, cenario, client):
    emitir_devolucao(db, cenario.id, EMPRESA_ID, _pedido(), usuario_id=None)
    dest = client.payloads[0][1]["destinatario"]
    assert dest["cpf"] == "12345678909"
    assert dest["endereco"]["logradouro"] == "Rua B"


# =========================
# 7. Pré-requisitos da origem
# =========================

@pytest.mark.parametrize("status_doc", ["CANCELADA", "REJEITADA", "PROCESSANDO"])
def test_so_origem_autorizada(db, empresa, client, status_doc):
    _produto(db, 1, "Teclado")
    doc = _nota_original(db, itens=[(1, 1000, 10000, "5102")])
    doc.status = status_doc
    db.commit()
    with pytest.raises(HTTPException) as exc:
        emitir_devolucao(db, doc.id, EMPRESA_ID, _pedido(), usuario_id=None)
    assert exc.value.status_code == 422


def test_origem_sem_chave_de_44_digitos_e_422(db, empresa, client):
    _produto(db, 1, "Teclado")
    doc = _nota_original(db, itens=[(1, 1000, 10000, "5102")])
    doc.chave_acesso = "123"
    db.commit()
    with pytest.raises(HTTPException) as exc:
        emitir_devolucao(db, doc.id, EMPRESA_ID, _pedido(), usuario_id=None)
    assert exc.value.status_code == 422
    assert client.payloads == []


# =========================
# 8. Estoque
# =========================

def test_autorizada_devolve_os_itens_ao_estoque(db, cenario, client):
    emitir_devolucao(db, cenario.id, EMPRESA_ID, _pedido(), usuario_id=None)

    assert db.get(Estoque, 1).quantidade == 12   # 10 + 2
    assert db.get(Estoque, 2).quantidade == 11   # 10 + 1
    movs = db.query(MovimentacaoEstoque).all()
    assert {m.origem for m in movs} == {MovimentacaoOrigem.DEVOLUCAO.value}


def test_devolver_estoque_false_nao_mexe_no_estoque(db, cenario, client):
    emitir_devolucao(db, cenario.id, EMPRESA_ID, _pedido(devolver_estoque=False), usuario_id=None)
    assert db.get(Estoque, 1).quantidade == 10
    assert db.query(MovimentacaoEstoque).count() == 0


# =========================
# 9. Falha de rede: número consumido, INDETERMINADA, saldos intocados
# =========================

def test_falha_de_rede_consome_o_numero_e_fica_indeterminada(db, cenario, client, monkeypatch):
    def explode(ref, payload, idempotency_key=None):
        raise ConnectionError("timeout")
    monkeypatch.setattr(client, "emitir_nfe", explode)

    doc = emitir_devolucao(db, cenario.id, EMPRESA_ID, _pedido(), usuario_id=None)

    assert doc.status == "INDETERMINADA"
    assert doc.numero_documento == 43
    assert crud.get_fiscal_settings(db, EMPRESA_ID).ultimo_numero_nfe == 43
    # Sem autorização confirmada, nem saldo nem estoque mudam.
    db.refresh(cenario)
    assert cenario.itens[0].quantidade_devolvida_acumulada == 0
    assert db.get(Estoque, 1).quantidade == 10


def test_rejeicao_da_sefaz_nao_consome_saldo(db, cenario, client, monkeypatch):
    monkeypatch.setattr(client, "emitir_nfe", lambda ref, payload, idempotency_key=None: {
        "status": "erro", "codigo_sefaz": 327, "mensagem_sefaz": "Rejeicao: CFOP invalido",
        "chave_acesso": None, "protocolo": None, "numero": None, "serie": None, "url_pdf": None, "url_xml": None,
    })
    doc = emitir_devolucao(db, cenario.id, EMPRESA_ID, _pedido(), usuario_id=None)
    assert doc.status == "REJEITADA"
    db.refresh(cenario)
    assert cenario.itens[0].quantidade_devolvida_acumulada == 0
