# ---------------------------------------------------------------------------
# ARQUIVO: test_avisos.py
# DESCRIÇÃO: Avisos que contam mas não travam (F1.3 e F1.4 do plano
#            docs/fiscal-refatoracao-plano.md).
# ---------------------------------------------------------------------------

import pytest

from app.db.models.cliente import ClientePF, ClientePJ
from app.db.models.empresa import Empresa
from app.services.fiscal.avisos import (
    aviso_destinatario_sem_ie,
    aviso_regime_mei,
    avisos_da_emissao,
)


def _empresa(regime=None, natureza=None, crt=None):
    return Empresa(id=1, regime_tributario=regime, natureza_juridica=natureza, crt=crt)


class TestAvisoRegimeMei:
    def test_o_caso_do_primeiro_cliente_natureza_mei_e_regime_simples(self):
        aviso = aviso_regime_mei(_empresa("Simples Nacional", "MEI", crt=1))
        assert aviso and "481" in aviso and "4 - MEI" in aviso

    def test_crt_antigo_vazio_cai_no_rotulo_do_regime(self):
        # Cadastro anterior à coluna `crt`: o CRT sai do rótulo.
        assert aviso_regime_mei(_empresa("Simples Nacional", "MEI")) is not None

    def test_regime_mei_com_natureza_de_outra_empresa(self):
        aviso = aviso_regime_mei(_empresa("MEI", "LTDA", crt=4))
        assert aviso and "LTDA" in aviso

    @pytest.mark.parametrize("regime,natureza,crt", [
        ("MEI", "MEI", 4),                      # coerente
        ("Simples Nacional", "ME", 1),          # Simples comum
        ("Lucro Presumido", "LTDA", 3),         # regime normal
        ("MEI", None, 4),                       # natureza não preenchida: não acusa
        ("Simples Nacional", None, 1),
    ])
    def test_cadastro_coerente_nao_avisa(self, regime, natureza, crt):
        assert aviso_regime_mei(_empresa(regime, natureza, crt)) is None

    def test_sem_empresa(self):
        assert aviso_regime_mei(None) is None


class TestAvisoDestinatarioSemIe:
    def test_pj_sem_ie_avisa(self):
        cliente = ClientePJ(id=1, razao_social="Lojinha Teste LTDA", cnpj="11444777000161")
        aviso = aviso_destinatario_sem_ie(cliente)
        assert aviso and "Lojinha Teste LTDA" in aviso and "NÃO contribuinte" in aviso

    def test_pj_com_ie_nao_avisa(self):
        cliente = ClientePJ(id=1, razao_social="Revenda", cnpj="11444777000161", ie="0623079040081")
        assert aviso_destinatario_sem_ie(cliente) is None

    def test_pessoa_fisica_nao_avisa(self):
        assert aviso_destinatario_sem_ie(ClientePF(id=1, nome="Ana", cpf="52998224725")) is None

    def test_sem_cliente_nao_avisa(self):
        assert aviso_destinatario_sem_ie(None) is None


def test_avisos_da_emissao_junta_os_dois():
    empresa = _empresa("Simples Nacional", "MEI", crt=1)
    cliente = ClientePJ(id=1, razao_social="Lojinha", cnpj="11444777000161")
    assert len(avisos_da_emissao(empresa, cliente)) == 2


def test_avisos_da_emissao_vazio_quando_tudo_certo():
    assert avisos_da_emissao(_empresa("MEI", "MEI", crt=4), None) == []
