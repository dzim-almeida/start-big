# ---------------------------------------------------------------------------
# ARQUIVO: test/services/fiscal/test_st_fabricante_ce.py
# DESCRICAO: Opcao do fabricante do CE com ICMS-ST pago em DAE (Decreto CE
#            32.900/2018). Passa pelo resolver, pelo motor e pelo payload, como
#            a emissao real. A opcao desligada tem que dar a nota de sempre.
# ---------------------------------------------------------------------------

from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.enum import State
from app.db.base import Base
from app.db.models.aliquota_uf import AliquotaUF
from app.db.models.cliente import ClientePF, ClientePJ
from app.db.models.empresa import Empresa
from app.db.models.empresa_fiscal_settings import EmpresaFiscalSettings
from app.db.models.endereco import Endereco
from app.db.models.forma_pagamento import FormaPagamento
from app.db.models.perfil_tributario import PerfilTributario
from app.db.models.produto import Produto
from app.db.models.produto_fiscal import ProdutoFiscal
from app.db.models.regra_perfil_tributario import RegraPerfilTributario
from app.db.models.venda import Venda
from app.db.models.venda_nota_fiscal import VendaNotaFiscal
from app.db.models.venda_pagamento import PagamentoVenda
from app.db.models.venda_produto import ProdutoVenda
from app.services.fiscal.completude.validators import conferir_fiscal_do_produto
from app.services.fiscal.derivacao.st_fabricante_ce import TEXTO_NOTA_OPERACAO_INTERNA
from app.services.fiscal.payload.builder import montar_payload_nfe
from app.services.fiscal.tax_engine.engine import calcular_impostos
from app.services.fiscal.tax_engine.exceptions import OperacaoInterestadualError
from app.services.fiscal.tax_engine.resolver import eh_operacao_interestadual, resolver_aliquotas_venda

BALCAO = 1
INTERNET = 2
SEM_RESPOSTA = None


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    sessao = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    sessao.add(AliquotaUF(uf="CE", aliquota_icms_interna=2000, aliquota_pis_padrao=165, aliquota_cofins_padrao=760))
    sessao.add(Empresa(id=1, razao_social="Marcenaria", documento="11222333000181", is_cnpj=True))
    sessao.commit()
    yield sessao
    sessao.close()


def _empresa() -> Empresa:
    return Empresa(
        id=1, documento="11222333000181", razao_social="Marcenaria Teste", nome_fantasia="Marcenaria",
        inscricao_estadual="110042490114", inscricao_municipal="12345", regime_tributario="Simples Nacional",
    )


def _endereco_empresa() -> Endereco:
    return Endereco(logradouro="Rua A", numero="1", bairro="Centro", cidade="Fortaleza",
                    estado=State.CEARA, cep="60000000")


def _settings(ligada: bool) -> EmpresaFiscalSettings:
    return EmpresaFiscalSettings(empresa_id=1, serie_nfe=2, ultimo_numero_nfe=10, nfe_st_fabricante_ce=ligada)


def _pj(ie="193000000") -> ClientePJ:
    return ClientePJ(id=2, razao_social="Compradora LTDA", cnpj="12345678000195", ie=ie)


def _pf() -> ClientePF:
    return ClientePF(id=1, nome="Maria", cpf="52998224725")


def _venda(cliente, uf=State.PIAUI, presenca=SEM_RESPOSTA, cfop="5401", csosn="500", perfil_id=None) -> Venda:
    venda = Venda(id=1, numero_venda=1001, subtotal=100000, total=100000, entrega=0, acrescimo=0)
    produto = Produto(id=1, nome="Guarda-roupa", codigo_produto="M1", unidade_medida="UN")
    produto.fiscal = ProdutoFiscal(
        produto_id=1, ncm="94036000", cfop_padrao=cfop, origem_mercadoria=0, csosn=csosn,
        unidade_tributavel="UN", perfil_tributario_id=perfil_id,
    )
    item = ProdutoVenda(id=1, produto_id=1, quantidade=1, valor_unitario=100000, subtotal=100000, desconto=0)
    item.produto = produto
    venda.itens = [item]
    cliente.endereco = [Endereco(logradouro="Rua X", numero="1", bairro="Centro", cidade="Cidade",
                                 estado=uf, cep="64000000")]
    venda.cliente = cliente
    venda.nota_fiscal = VendaNotaFiscal(venda_id=1, indicador_presenca=presenca)
    venda.pagamentos = [PagamentoVenda(valor=100000, forma_pagamento=FormaPagamento(id=1, nome="Pix", codigo_sefaz="17"))]
    return venda


def _emitir(db, venda, ligada: bool) -> dict:
    """O caminho da emissao: resolver, motor e payload."""
    itens, dados = resolver_aliquotas_venda(db, venda, "CE", True, st_fabricante_ce=ligada)
    return montar_payload_nfe(
        empresa=_empresa(), endereco_empresa=_endereco_empresa(), fiscal_settings=_settings(ligada),
        venda=venda, nota_fiscal=venda.nota_fiscal, resultado_calculo=calcular_impostos(itens, dados), numero=11,
    )


# --- O que o contador orientou ---------------------------------------------------

def test_empresa_com_ie_de_outro_estado_sai_6401_e_500_sem_st(db):
    payload = _emitir(db, _venda(_pj()), ligada=True)

    item = payload["items"][0]
    assert (item["cfop"], item["icms_situacao_tributaria"]) == ("6401", "500")
    assert payload["local_destino"] == 2
    assert item["icms_valor"] == 0
    assert not any(chave.endswith("_st") or "_st_" in chave for chave in item)
    assert payload["totais"]["valor_total"] == 1000.0


def test_venda_para_fora_sem_resposta_avisa_que_nao_foi_presencial(db):
    assert _emitir(db, _venda(_pj()), ligada=True)["presenca_comprador"] == 9


def test_presenca_respondida_e_mantida(db):
    assert _emitir(db, _venda(_pj(), presenca=INTERNET), ligada=True)["presenca_comprador"] == INTERNET


def test_venda_para_fora_nao_leva_o_texto_do_decreto(db):
    assert "informacoes_adicionais_contribuinte" not in _emitir(db, _venda(_pj()), ligada=True)


def test_dentro_do_ce_sai_5401_e_500_com_o_texto_do_decreto(db):
    payload = _emitir(db, _venda(_pj(), uf=State.CEARA), ligada=True)

    item = payload["items"][0]
    assert (item["cfop"], item["icms_situacao_tributaria"]) == ("5401", "500")
    assert payload["local_destino"] == 1
    assert payload["presenca_comprador"] == BALCAO
    assert payload["informacoes_adicionais_contribuinte"] == TEXTO_NOTA_OPERACAO_INTERNA


def test_cliente_de_fora_que_retirou_no_balcao_sai_interna(db):
    payload = _emitir(db, _venda(_pj(), presenca=BALCAO), ligada=True)

    assert payload["items"][0]["cfop"] == "5401"
    assert payload["local_destino"] == 1
    assert payload["presenca_comprador"] == BALCAO


def test_cpf_de_outro_estado_e_recusado_com_o_caminho_para_resolver(db):
    with pytest.raises(OperacaoInterestadualError, match="marque a venda como presencial"):
        resolver_aliquotas_venda(db, _venda(_pf()), "CE", True, st_fabricante_ce=True)


def test_cpf_de_outro_estado_que_retirou_no_balcao_sai_interna(db):
    assert _emitir(db, _venda(_pf(), presenca=BALCAO), ligada=True)["items"][0]["cfop"] == "5401"


# --- A opcao so alcanca o item da regra ------------------------------------------

def test_ligada_nao_alcanca_produto_que_nao_e_5401_com_500(db):
    with pytest.raises(OperacaoInterestadualError, match="perfil tributário"):
        resolver_aliquotas_venda(db, _venda(_pj(), cfop="5101", csosn="101"), "CE", True, st_fabricante_ce=True)


def test_ligada_nao_alcanca_regime_normal(db):
    venda = _venda(_pj(), presenca=INTERNET)
    venda.itens[0].produto.fiscal.cst_icms = "00"

    with pytest.raises(OperacaoInterestadualError, match="perfil tributário"):
        resolver_aliquotas_venda(db, venda, "CE", False, st_fabricante_ce=True)


# --- Desligada: tudo como antes --------------------------------------------------

def test_desligada_venda_sem_resposta_continua_interna(db):
    payload = _emitir(db, _venda(_pj()), ligada=False)

    assert payload["items"][0]["cfop"] == "5401"
    assert payload["local_destino"] == 1
    assert payload["presenca_comprador"] == BALCAO
    assert not eh_operacao_interestadual(_venda(_pj()), "CE")


def test_desligada_500_para_fora_continua_exigindo_perfil(db):
    with pytest.raises(OperacaoInterestadualError, match="perfil tributário"):
        resolver_aliquotas_venda(db, _venda(_pj(), presenca=INTERNET), "CE", True)


def test_desligada_500_para_fora_com_mva_continua_virando_substituto(db):
    perfil = PerfilTributario(empresa_id=1, descricao="Moveis")
    perfil.regras = [RegraPerfilTributario(aliquota_interestadual=1200, aliquota_interna_destino=1800, mva_st=4000)]
    db.add(perfil)
    db.commit()

    itens, _ = resolver_aliquotas_venda(db, _venda(_pj(), presenca=INTERNET, perfil_id=perfil.id), "CE", True)

    assert itens[0].cfop == "6401"
    assert itens[0].csosn == "202"
    assert itens[0].st_mva is not None


@pytest.mark.parametrize("cfop,csosn,uf,presenca", [
    ("5102", "102", State.CEARA, SEM_RESPOSTA),
    ("5101", "101", State.CEARA, BALCAO),
    ("5405", "500", State.CEARA, SEM_RESPOSTA),
    ("5102", "102", State.PIAUI, SEM_RESPOSTA),
])
def test_quem_nao_ligou_recebe_a_mesma_nota_que_antes(db, cfop, csosn, uf, presenca):
    """Sem o parametro e o caminho antigo; com ele em False, tem que ser igual."""
    def payload(com_parametro: bool) -> dict:
        venda = _venda(_pj(), uf=uf, presenca=presenca, cfop=cfop, csosn=csosn)
        kwargs = {"st_fabricante_ce": False} if com_parametro else {}
        itens, dados = resolver_aliquotas_venda(db, venda, "CE", True, **kwargs)
        return montar_payload_nfe(
            empresa=_empresa(), endereco_empresa=_endereco_empresa(), fiscal_settings=_settings(False),
            venda=venda, nota_fiscal=venda.nota_fiscal, resultado_calculo=calcular_impostos(itens, dados), numero=11,
        )

    antes, depois = payload(False), payload(True)

    assert antes == depois
    assert "informacoes_adicionais_contribuinte" not in depois


# --- CEST ------------------------------------------------------------------------

def _fiscal(cfop="5401", csosn="500", cest=None):
    return SimpleNamespace(
        ncm="94036000", cfop_padrao=cfop, cest=cest, csosn=csosn, cst_icms=None, origem_mercadoria=0,
        reducao_base_icms=None, cst_pis=None, cst_cofins=None, unidade_tributavel="UN",
    )


def _campos_pendentes(fiscal, ligada: bool) -> set[str]:
    return {p.campo for p in conferir_fiscal_do_produto(fiscal, "Movel", simples_nacional=True, st_fabricante_ce=ligada)}


def test_cest_nao_trava_o_item_da_regra_com_a_opcao_ligada():
    assert "cest" not in _campos_pendentes(_fiscal(), ligada=True)


def test_cest_continua_obrigatorio_com_a_opcao_desligada():
    assert "cest" in _campos_pendentes(_fiscal(), ligada=False)


def test_cest_continua_obrigatorio_em_outro_500_com_a_opcao_ligada():
    assert "cest" in _campos_pendentes(_fiscal(cfop="5405"), ligada=True)
