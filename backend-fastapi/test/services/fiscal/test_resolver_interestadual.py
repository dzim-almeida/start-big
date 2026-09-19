# ---------------------------------------------------------------------------
# ARQUIVO: test/services/fiscal/test_resolver_interestadual.py
# DESCRIÇÃO: TASK007 CA-3 — o resolver diante de uma operação interestadual:
#            quem é não contribuinte, quando o perfil libera a venda e o que
#            chega ao ItemEntrada.
# ---------------------------------------------------------------------------

from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.enum import State
from app.db.base import Base
from app.db.models.aliquota_uf import AliquotaUF
from app.db.models.cliente import ClientePF, ClientePJ
from app.db.models.empresa import Empresa
from app.db.models.endereco import Endereco
from app.db.models.perfil_tributario import PerfilTributario
from app.db.models.produto import Produto
from app.db.models.produto_fiscal import ProdutoFiscal
from app.db.models.regra_perfil_tributario import RegraPerfilTributario
from app.db.models.venda import Venda
from app.db.models.venda_nota_fiscal import VendaNotaFiscal
from app.db.models.venda_produto import ProdutoVenda
from app.services.fiscal.tax_engine.exceptions import OperacaoInterestadualError
from app.services.fiscal.tax_engine.resolver import _cliente_nao_contribuinte, resolver_aliquotas_venda

INTERNET = 2
BALCAO = 1


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    sessao = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    sessao.add(AliquotaUF(uf="SP", aliquota_icms_interna=1800, aliquota_pis_padrao=165, aliquota_cofins_padrao=760))
    sessao.add(Empresa(id=1, razao_social="Loja", documento="11111111000191", is_cnpj=True))
    sessao.commit()
    yield sessao
    sessao.close()


@pytest.fixture
def perfil(db) -> PerfilTributario:
    """Fallback 12%/17% e MG 12%/18% + FCP 2% (base dupla)."""
    p = PerfilTributario(empresa_id=1, descricao="Varejo")
    p.regras = [
        RegraPerfilTributario(aliquota_interestadual=1200, aliquota_interna_destino=1700),
        RegraPerfilTributario(uf_destino="MG", aliquota_interestadual=1200, aliquota_interna_destino=1800,
                              percentual_fcp=200, calculo_base_dupla=True),
    ]
    db.add(p)
    db.commit()
    return p


def _pf() -> ClientePF:
    return ClientePF(id=1, nome="Maria", cpf="52998224725")


def _pj(ie=None) -> ClientePJ:
    return ClientePJ(id=2, razao_social="Compradora LTDA", cnpj="12345678000195", ie=ie)


def _venda(cliente, uf_cliente=State.MINAS_GERAIS, indicador_presenca=INTERNET, perfil_id=None, itens=1) -> Venda:
    venda = Venda(id=1, numero_venda=1001, subtotal=10000 * itens, total=10000 * itens, entrega=0, acrescimo=0)
    venda.itens = []
    for n in range(1, itens + 1):
        produto = Produto(id=n, nome=f"Teclado {n}", codigo_produto=f"P{n}", unidade_medida="UN")
        produto.fiscal = ProdutoFiscal(
            produto_id=n, ncm="84716052", cfop_padrao="5102", origem_mercadoria=0,
            cst_icms="00", csosn="102", aliquota_icms=1800, perfil_tributario_id=perfil_id,
        )
        item = ProdutoVenda(id=n, produto_id=n, quantidade=1, valor_unitario=10000, subtotal=10000, desconto=0)
        item.produto = produto
        venda.itens.append(item)
    if cliente is not None:
        cliente.endereco = [Endereco(logradouro="Rua X", numero="1", bairro="Centro", cidade="Cidade",
                                     estado=uf_cliente, cep="01001000")]
    venda.cliente = cliente
    venda.nota_fiscal = VendaNotaFiscal(venda_id=1, indicador_presenca=indicador_presenca)
    return venda


# --- Quem é não contribuinte ---------------------------------------------------

def test_pf_pj_sem_ie_e_sem_cliente_sao_nao_contribuintes():
    assert _cliente_nao_contribuinte(_venda(_pf())) is True
    assert _cliente_nao_contribuinte(_venda(_pj(ie=None))) is True
    assert _cliente_nao_contribuinte(_venda(_pj(ie=""))) is True
    assert _cliente_nao_contribuinte(_venda(None)) is True


def test_pj_com_ie_e_contribuinte():
    assert _cliente_nao_contribuinte(_venda(_pj(ie="1234567890"))) is False


# --- Regime normal: DIFAL pelo perfil -------------------------------------------

def test_nao_contribuinte_com_perfil_recebe_difal_e_icms_pela_interestadual(db, perfil):
    itens, _ = resolver_aliquotas_venda(db, _venda(_pf(), perfil_id=perfil.id), "SP", simples_nacional=False)
    i = itens[0]
    assert i.aliquota_icms == Decimal("12")               # não mais os 18% internos de SP
    assert i.difal_aliquota_interestadual == Decimal("12")
    assert i.difal_aliquota_interna_destino == Decimal("18")
    assert i.difal_percentual_fcp == Decimal("2") and i.difal_base_dupla is True


def test_uf_sem_regra_especifica_usa_o_fallback(db, perfil):
    itens, _ = resolver_aliquotas_venda(
        db, _venda(_pf(), uf_cliente=State.RIO_DE_JANEIRO, perfil_id=perfil.id), "SP", simples_nacional=False,
    )
    assert itens[0].difal_aliquota_interna_destino == Decimal("17") and itens[0].difal_base_dupla is False


def test_pj_sem_ie_e_tratada_como_nao_contribuinte(db, perfil):
    itens, _ = resolver_aliquotas_venda(db, _venda(_pj(), perfil_id=perfil.id), "SP", simples_nacional=False)
    assert itens[0].difal_aliquota_interna_destino == Decimal("18")


def test_produto_sem_perfil_e_barrado_com_orientacao(db, perfil):
    venda = _venda(_pf(), perfil_id=perfil.id, itens=2)
    venda.itens[1].produto.fiscal.perfil_tributario_id = None

    with pytest.raises(OperacaoInterestadualError) as exc:
        resolver_aliquotas_venda(db, venda, "SP", simples_nacional=False)
    assert exc.value.campo == "perfil_tributario_id" and exc.value.item == 2
    assert "Teclado 2" in exc.value.mensagem and "perfil" in exc.value.mensagem.lower()


def test_perfil_sem_regra_para_a_uf_e_barrado(db, perfil):
    db.query(RegraPerfilTributario).filter(RegraPerfilTributario.uf_destino.is_(None)).delete()
    db.commit()
    with pytest.raises(OperacaoInterestadualError) as exc:
        resolver_aliquotas_venda(db, _venda(_pf(), uf_cliente=State.RIO_DE_JANEIRO, perfil_id=perfil.id), "SP", simples_nacional=False)
    assert exc.value.campo == "perfil_tributario_id" and "RJ" in exc.value.mensagem


def test_contribuinte_com_perfil_sem_mva_nao_recebe_difal(db, perfil):
    """A trava do contribuinte caiu na TASK008: sem MVA na regra é revenda interestadual comum."""
    itens, _ = resolver_aliquotas_venda(db, _venda(_pj(ie="1234567890"), perfil_id=perfil.id), "SP", simples_nacional=False)
    assert itens[0].difal_aliquota_interestadual is None and itens[0].st_mva is None
    assert itens[0].aliquota_icms == Decimal("12") and itens[0].cfop == "6102"


# --- O que não muda -----------------------------------------------------------

@pytest.mark.parametrize("uf, indpres", [(State.SAO_PAULO, INTERNET), (State.MINAS_GERAIS, BALCAO)])
def test_operacao_interna_e_balcao_nao_tem_difal(db, perfil, uf, indpres):
    itens, _ = resolver_aliquotas_venda(
        db, _venda(_pf(), uf_cliente=uf, indicador_presenca=indpres, perfil_id=perfil.id), "SP", simples_nacional=False,
    )
    assert itens[0].aliquota_icms == Decimal("18") and itens[0].difal_aliquota_interestadual is None


def test_simples_nacional_libera_sem_difal_e_sem_exigir_perfil(db):
    """ADI 5464: remetente do Simples não recolhe o DIFAL de partilha — sem ICMSUFDest, sem perfil."""
    itens, _ = resolver_aliquotas_venda(db, _venda(_pf(), perfil_id=None), "SP", simples_nacional=True)
    assert itens[0].difal_aliquota_interestadual is None and itens[0].csosn == "102"


# --- TASK008: contribuinte (ICMS-ST) e CFOP/CST da operação ---------------------

@pytest.fixture
def perfil_st(db) -> PerfilTributario:
    """MG com ST (MVA 40%, redução 20%); RJ sem ST; fallback sem ST."""
    p = PerfilTributario(empresa_id=1, descricao="Peças - ST")
    p.regras = [
        RegraPerfilTributario(aliquota_interestadual=1200, aliquota_interna_destino=1700),
        RegraPerfilTributario(uf_destino="MG", aliquota_interestadual=1200, aliquota_interna_destino=1800,
                              mva_st=4000, reducao_base_calculo=2000),
        RegraPerfilTributario(uf_destino="RJ", aliquota_interestadual=1200, aliquota_interna_destino=2000, mva_st=0),
    ]
    db.add(p)
    db.commit()
    return p


def test_contribuinte_com_st_recebe_mva_cfop_6404_e_cst_10(db, perfil_st):
    itens, _ = resolver_aliquotas_venda(db, _venda(_pj(ie="1234567890"), perfil_id=perfil_st.id), "SP", simples_nacional=False)
    i = itens[0]
    assert i.aliquota_icms == Decimal("12")
    assert (i.st_aliquota_interestadual, i.st_aliquota_interna_destino) == (Decimal("12"), Decimal("18"))
    assert (i.st_mva, i.st_reducao_base) == (Decimal("40"), Decimal("20"))
    assert i.cfop == "6404" and i.cst_icms == "10"
    assert i.difal_aliquota_interestadual is None


def test_contribuinte_com_st_e_produto_com_reducao_vira_cst_70(db, perfil_st):
    venda = _venda(_pj(ie="1234567890"), perfil_id=perfil_st.id)
    venda.itens[0].produto.fiscal.cst_icms = "20"
    venda.itens[0].produto.fiscal.reducao_base_icms = 5000
    itens, _ = resolver_aliquotas_venda(db, venda, "SP", simples_nacional=False)
    assert itens[0].cst_icms == "70"


def test_contribuinte_sem_st_na_regra_e_b2b_normal(db, perfil_st):
    itens, _ = resolver_aliquotas_venda(
        db, _venda(_pj(ie="1234567890"), uf_cliente=State.RIO_DE_JANEIRO, perfil_id=perfil_st.id), "SP", simples_nacional=False,
    )
    i = itens[0]
    assert i.aliquota_icms == Decimal("12") and i.st_mva is None
    assert i.cfop == "6102" and i.cst_icms == "00"


def test_contribuinte_sem_perfil_e_barrado(db, perfil_st):
    with pytest.raises(OperacaoInterestadualError) as exc:
        resolver_aliquotas_venda(db, _venda(_pj(ie="1234567890"), perfil_id=None), "SP", simples_nacional=False)
    assert exc.value.campo == "perfil_tributario_id"


def test_simples_contribuinte_com_st_recebe_csosn_202_e_st(db, perfil_st):
    itens, _ = resolver_aliquotas_venda(db, _venda(_pj(ie="1234567890"), perfil_id=perfil_st.id), "SP", simples_nacional=True)
    i = itens[0]
    assert i.csosn == "202" and i.cfop == "6404" and i.st_mva == Decimal("40")
    assert i.aliquota_icms == Decimal("18")   # no Simples o ICMS próprio não é destacado; a alíquota fica como está


def test_simples_contribuinte_exige_perfil(db):
    with pytest.raises(OperacaoInterestadualError):
        resolver_aliquotas_venda(db, _venda(_pj(ie="1234567890"), perfil_id=None), "SP", simples_nacional=True)


def test_cfop_interestadual_no_b2c(db, perfil):
    itens, _ = resolver_aliquotas_venda(db, _venda(_pf(), perfil_id=perfil.id), "SP", simples_nacional=False)
    assert itens[0].cfop == "6108" and itens[0].cst_icms == "00"


def test_producao_propria_vai_para_6107(db, perfil):
    venda = _venda(_pf(), perfil_id=perfil.id)
    venda.itens[0].produto.fiscal.cfop_padrao = "5101"
    itens, _ = resolver_aliquotas_venda(db, venda, "SP", simples_nacional=False)
    assert itens[0].cfop == "6107"


def test_simples_b2c_tambem_sai_com_cfop_6108(db):
    itens, _ = resolver_aliquotas_venda(db, _venda(_pf(), perfil_id=None), "SP", simples_nacional=True)
    assert itens[0].cfop == "6108" and itens[0].csosn == "102"


def test_operacao_interna_mantem_o_cfop_do_produto(db, perfil_st):
    itens, _ = resolver_aliquotas_venda(
        db, _venda(_pj(ie="1234567890"), uf_cliente=State.SAO_PAULO, perfil_id=perfil_st.id), "SP", simples_nacional=False,
    )
    assert itens[0].cfop == "5102" and itens[0].st_mva is None and itens[0].cst_icms == "00"
