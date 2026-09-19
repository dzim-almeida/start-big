# ---------------------------------------------------------------------------
# ARQUIVO: test/services/fiscal/test_guardrails_interestadual.py
# DESCRIÇÃO: TASK009 § 5 — o que barra a NF-e interestadual ANTES de reservar
#            número: IE do contribuinte mal formada.
# ---------------------------------------------------------------------------

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.enum import EntityType, State
from app.db.base import Base
from app.db.models.cliente import ClientePF, ClientePJ
from app.db.models.empresa import Empresa
from app.db.models.endereco import Endereco
from app.db.models.funcionario import Funcionario
from app.db.models.venda import Venda
from app.db.models.venda_nota_fiscal import VendaNotaFiscal
from app.services.fiscal.core import verificar_completude_venda
from app.services.fiscal.validators import verificar_ie_destinatario_interestadual


def _pj(ie) -> ClientePJ:
    return ClientePJ(id=2, razao_social="Compradora LTDA", cnpj="12345678000195", ie=ie)


@pytest.mark.parametrize("ie", ["ISENTO", "1", "123456789012345", "ABC123"])
def test_ie_mal_formada_e_pendencia(ie):
    pendencias = verificar_ie_destinatario_interestadual(_pj(ie))
    assert [p.campo for p in pendencias] == ["ie"]
    assert "Rejei" in pendencias[0].mensagem or "232" in pendencias[0].mensagem


@pytest.mark.parametrize("ie", ["110042490114", "110.042.490.114", "12"])
def test_ie_com_digitos_passa_mesmo_com_pontuacao(ie):
    assert verificar_ie_destinatario_interestadual(_pj(ie)) == []


def test_pj_sem_ie_e_pf_nao_tem_o_que_validar():
    assert verificar_ie_destinatario_interestadual(_pj(None)) == []
    assert verificar_ie_destinatario_interestadual(_pj("")) == []
    assert verificar_ie_destinatario_interestadual(ClientePF(id=1, nome="Maria", cpf="52998224725")) == []


# --- Ligado no gate da NF-e, só para operação interestadual -----------------------

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    sessao = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    yield sessao
    sessao.close()


def _venda_persistida(db, uf_cliente, indicador_presenca) -> int:
    db.add(Empresa(id=1, razao_social="Loja", documento="11111111000191", is_cnpj=True))
    db.add(Endereco(id_entidade=1, tipo_entidade=EntityType.EMPRESA, logradouro="Rua A", numero="1",
                    bairro="Centro", cidade="Sao Paulo", estado=State.SAO_PAULO, cep="01001000"))
    cliente = _pj("ISENTO")
    db.add_all([cliente, Funcionario(id=1, empresa_id=1, nome="Vendedor")])
    db.flush()
    db.add(Endereco(id_entidade=cliente.id, tipo_entidade=EntityType.CLIENTE, logradouro="Rua B", numero="2",
                    bairro="Centro", cidade="Cidade", estado=uf_cliente, cep="30130000"))
    venda = Venda(id=1, numero_venda=1001, subtotal=0, total=0, entrega=0, acrescimo=0, cliente_id=cliente.id, funcionario_id=1)
    venda.nota_fiscal = VendaNotaFiscal(venda_id=1, indicador_presenca=indicador_presenca)
    db.add(venda)
    db.commit()
    return venda.id


def _campos(db, venda_id) -> set[str]:
    return {p.campo for p in verificar_completude_venda(db, venda_id, 1, "nfe").pendencias}


def test_gate_barra_ie_invalida_na_interestadual(db):
    assert "ie" in _campos(db, _venda_persistida(db, State.MINAS_GERAIS, indicador_presenca=2))


@pytest.mark.parametrize("uf, indpres", [(State.SAO_PAULO, 2), (State.MINAS_GERAIS, 1)])
def test_gate_ignora_a_ie_em_operacao_interna_ou_balcao(db, uf, indpres):
    assert "ie" not in _campos(db, _venda_persistida(db, uf, indicador_presenca=indpres))
