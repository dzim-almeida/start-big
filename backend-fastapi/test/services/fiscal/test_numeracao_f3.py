# ---------------------------------------------------------------------------
# ARQUIVO: test_numeracao_f3.py
# DESCRIÇÃO: F3 do plano de refatoração do fiscal — numeração de quem já
#            emitia por outro sistema.
#
# O caso: o primeiro cliente em produção começou do 1 e a SEFAZ devolveu a 539
# no nº 4 da série 2 (emitido em 09/2026 pelo sistema antigo).
# ---------------------------------------------------------------------------

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models.documento_fiscal import DocumentoFiscal
from app.db.models.empresa import Empresa
from app.db.models.empresa_fiscal_settings import EmpresaFiscalSettings
from app.schemas.empresa import FiscalSettingsUpdate
from app.services.empresa import update_fiscal_settings
from app.services.fiscal.inutilizacao import listar_gaps_numeracao, solicitar_inutilizacao
from app.services.fiscal.numeracao import (
    ajustar_numeracao_por_duplicidade,
    ler_chave_da_mensagem,
    validar_novo_ultimo_numero,
)

EMPRESA_ID = 1
MSG_539 = (
    "Rejeição: Duplicidade de NF-e com diferença na Chave de Acesso "
    "[chNFe:35260958348941000109550020000000041750446210][nRec:351025570568140]"
)


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    sessao = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    sessao.add(Empresa(id=EMPRESA_ID, razao_social="Loja", documento="58348941000109", is_cnpj=True, regime_tributario="MEI"))
    sessao.flush()
    yield sessao
    sessao.close()


def _config(db, **campos):
    fs = EmpresaFiscalSettings(empresa_id=EMPRESA_ID, ambiente_emissao=1, numeracao_confirmada=True, **campos)
    db.add(fs)
    db.commit()
    return fs


def _doc(db, numero, status, serie=2, cstat=None, mensagem=None):
    d = DocumentoFiscal(
        tipo_documento="NFE", origem_tipo="VENDA", origem_id=numero, numero_documento=numero,
        serie=serie, status=status, codigo_status_sefaz=cstat, mensagem_sefaz=mensagem,
    )
    db.add(d)
    db.commit()
    return d


def _faixas(db):
    return [(g["numero_inicial"], g["numero_final"]) for g in listar_gaps_numeracao(db, EMPRESA_ID)]


class TestLerChave:
    def test_le_serie_numero_e_modelo_da_539(self):
        assert ler_chave_da_mensagem(MSG_539) == {
            "chave": "35260958348941000109550020000000041750446210",
            "modelo": 55, "serie": 2, "numero": 4, "ano_mes": "2609",
        }

    def test_procura_em_mais_de_um_texto(self):
        assert ler_chave_da_mensagem(None, "sem chave", MSG_539)["numero"] == 4

    def test_sem_chave(self):
        assert ler_chave_da_mensagem("Rejeição: qualquer", None) is None


class TestSugestaoDeInutilizacao:
    def test_quem_veio_de_outro_sistema_nao_ve_os_numeros_antigos(self, db):
        """Informou 'último = 37' à mão: 1..36 são do sistema anterior."""
        _config(db, serie_nfe=2, ultimo_numero_nfe=37, numeracao_piso_nfe=37)
        assert _faixas(db) == []

    def test_acima_do_piso_vale_a_regra_de_sempre(self, db):
        _config(db, serie_nfe=2, ultimo_numero_nfe=40, numeracao_piso_nfe=37)
        _doc(db, 38, "AUTORIZADA")
        # 39 rejeitado, 40 reservado e perdido sem nota: os dois são buraco.
        _doc(db, 39, "REJEITADA", cstat=305)
        assert _faixas(db) == [(39, 40)]

    def test_abaixo_do_piso_numero_usado_pelo_startbig_continua_aparecendo(self, db):
        _config(db, serie_nfe=2, ultimo_numero_nfe=37, numeracao_piso_nfe=37)
        _doc(db, 3, "REJEITADA", cstat=481)
        assert _faixas(db) == [(3, 3)]

    def test_numero_da_539_nunca_e_buraco(self, db):
        """A SEFAZ acabou de dizer que ele existe."""
        _config(db, serie_nfe=2, ultimo_numero_nfe=5)
        for n in (1, 2, 3, 5):
            _doc(db, n, "AUTORIZADA")
        _doc(db, 4, "REJEITADA", cstat=539, mensagem=MSG_539)
        assert _faixas(db) == []

    def test_inutilizar_numero_da_539_e_recusado(self, db):
        _config(db, serie_nfe=2, ultimo_numero_nfe=5)
        _doc(db, 4, "REJEITADA", cstat=539, mensagem=MSG_539)
        with pytest.raises(HTTPException) as exc:
            solicitar_inutilizacao(db, EMPRESA_ID, 2, 4, 4, "Numero recusado pela SEFAZ")
        assert exc.value.status_code == 409
        assert exc.value.detail["codigo"] == "NUMERO_USADO_FORA"


class TestContadorNaoVoltaParaTras:
    def test_abaixo_da_maior_nota_do_startbig_e_recusado(self, db):
        _config(db, serie_nfe=2, ultimo_numero_nfe=5)
        _doc(db, 5, "AUTORIZADA")
        with pytest.raises(HTTPException) as exc:
            validar_novo_ultimo_numero(db, "NFE", 2, 3)
        assert exc.value.status_code == 422 and "nº 5" in exc.value.detail

    @pytest.mark.parametrize("ultimo", [5, 6, 100])
    def test_igual_ou_acima_passa(self, db, ultimo):
        _config(db, serie_nfe=2, ultimo_numero_nfe=5)
        _doc(db, 5, "AUTORIZADA")
        validar_novo_ultimo_numero(db, "NFE", 2, ultimo)

    def test_outra_serie_nao_e_afetada(self, db):
        _config(db, serie_nfe=2, ultimo_numero_nfe=5)
        _doc(db, 5, "AUTORIZADA", serie=2)
        validar_novo_ultimo_numero(db, "NFE", 1, 0)

    def test_tela_de_configuracao_aplica_a_trava(self, db):
        _config(db, serie_nfe=2, ultimo_numero_nfe=5)
        _doc(db, 5, "AUTORIZADA")
        with pytest.raises(HTTPException):
            update_fiscal_settings(db, EMPRESA_ID, FiscalSettingsUpdate(ultimo_numero_nfe=2))


class TestPisoNaConfiguracao:
    def test_mudar_o_ultimo_numero_vira_piso(self, db):
        fs = _config(db, serie_nfe=1, ultimo_numero_nfe=0)
        update_fiscal_settings(db, EMPRESA_ID, FiscalSettingsUpdate(serie_nfe=2, ultimo_numero_nfe=37))
        assert fs.numeracao_piso_nfe == 37

    def test_reenviar_o_mesmo_valor_nao_mexe_no_piso(self, db):
        """A tela manda tudo de novo; isso não pode esconder buraco do StartBig."""
        fs = _config(db, serie_nfe=2, ultimo_numero_nfe=40, numeracao_piso_nfe=37)
        update_fiscal_settings(db, EMPRESA_ID, FiscalSettingsUpdate(serie_nfe=2, ultimo_numero_nfe=40))
        assert fs.numeracao_piso_nfe == 37


class TestAjustePorDuplicidade:
    def test_o_caso_do_celso(self, db):
        fs = _config(db, serie_nfe=2, ultimo_numero_nfe=4)
        doc = _doc(db, 4, "REJEITADA", cstat=539, mensagem=MSG_539)

        r = ajustar_numeracao_por_duplicidade(db, EMPRESA_ID, doc.id, 37)

        assert r["proximo_numero"] == 38
        assert fs.ultimo_numero_nfe == 37
        assert fs.numeracao_piso_nfe == 37
        assert _faixas(db) == []

    def test_nao_aceita_menos_que_o_numero_acusado(self, db):
        _config(db, serie_nfe=2, ultimo_numero_nfe=1)
        doc = _doc(db, 4, "REJEITADA", cstat=539, mensagem=MSG_539)
        with pytest.raises(HTTPException) as exc:
            ajustar_numeracao_por_duplicidade(db, EMPRESA_ID, doc.id, 3)
        assert "pelo menos 4" in exc.value.detail

    def test_nao_aceita_voltar_o_contador(self, db):
        _config(db, serie_nfe=2, ultimo_numero_nfe=10)
        doc = _doc(db, 4, "REJEITADA", cstat=539, mensagem=MSG_539)
        with pytest.raises(HTTPException) as exc:
            ajustar_numeracao_por_duplicidade(db, EMPRESA_ID, doc.id, 5)
        assert "pelo menos 10" in exc.value.detail

    def test_so_para_539(self, db):
        _config(db, serie_nfe=2, ultimo_numero_nfe=4)
        doc = _doc(db, 4, "REJEITADA", cstat=481)
        with pytest.raises(HTTPException) as exc:
            ajustar_numeracao_por_duplicidade(db, EMPRESA_ID, doc.id, 10)
        assert exc.value.status_code == 422

    def test_serie_trocada_depois_da_rejeicao(self, db):
        _config(db, serie_nfe=1, ultimo_numero_nfe=0)
        doc = _doc(db, 4, "REJEITADA", serie=2, cstat=539, mensagem=MSG_539)
        with pytest.raises(HTTPException) as exc:
            ajustar_numeracao_por_duplicidade(db, EMPRESA_ID, doc.id, 10)
        assert "série 2" in exc.value.detail
