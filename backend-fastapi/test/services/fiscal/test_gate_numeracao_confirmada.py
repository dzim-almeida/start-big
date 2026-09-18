# ---------------------------------------------------------------------------
# ARQUIVO: test/services/fiscal/test_gate_numeracao_confirmada.py
# DESCRIÇÃO: TASK001 — trava de confirmação da numeração fiscal.
#
# Uma empresa que já emitia em outro ERP e entra aqui com "última nota 0"
# emite a nota 1 de novo e leva Rejeição 204 (duplicidade). A trava obriga
# alguém a CONFIRMAR série e último número antes da primeira emissão.
# ---------------------------------------------------------------------------

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.enum import EntityType, State
from app.db.base import Base
from app.db.crud import fiscal as crud
from app.db.models.empresa import Empresa
from app.db.models.empresa_fiscal_settings import EmpresaFiscalSettings
from app.db.models.endereco import Endereco
from app.schemas.empresa import FiscalSettingsUpdate
from app.services.empresa import update_fiscal_settings
from app.services.fiscal import validators
from app.services.fiscal.emissao import emitir_teste_nfe


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
def empresa_completa(db):
    """Emitente que passa em todas as OUTRAS checagens do gate."""
    empresa = Empresa(
        id=1,
        razao_social="Loja Teste LTDA",
        documento="11222333000181",
        is_cnpj=True,
        regime_tributario="Simples Nacional",
        indicador_ie="9",
        crt=1,
    )
    db.add(empresa)
    db.flush()
    db.add(Endereco(
        id_entidade=empresa.id, tipo_entidade=EntityType.EMPRESA,
        logradouro="Rua A", numero="10", bairro="Centro",
        cidade="Sao Paulo", estado=State.SAO_PAULO, cep="01001000",
    ))
    db.add(EmpresaFiscalSettings(
        empresa_id=empresa.id, serie_nfe=1, ultimo_numero_nfe=0,
        serie_nfce=1, ultimo_numero_nfce=0, ambiente_emissao=2,
    ))
    db.commit()
    return empresa


def _campos(pendencias):
    return {p.campo for p in pendencias}


# =========================
# 1. O gate
# =========================

def test_numeracao_nao_confirmada_gera_pendencia_impeditiva(db, empresa_completa):
    pendencias = validators.verificar_emitente(db, empresa_completa.id)
    assert "numeracao_confirmada" in _campos(pendencias)
    [p] = [p for p in pendencias if p.campo == "numeracao_confirmada"]
    assert p.categoria == "configuracao"
    assert "Emissão Estadual" in p.mensagem


def test_numeracao_confirmada_libera_o_gate(db, empresa_completa):
    fs = crud.get_fiscal_settings(db, empresa_completa.id)
    fs.numeracao_confirmada = True
    db.commit()

    assert "numeracao_confirmada" not in _campos(
        validators.verificar_emitente(db, empresa_completa.id)
    )


def test_sem_configuracao_fiscal_nao_duplica_a_pendencia(db):
    """Sem settings, a pendência é 'fiscal_settings'; não faz sentido acusar numeração."""
    empresa = Empresa(id=2, razao_social="X", documento="11222333000181", is_cnpj=True)
    db.add(empresa)
    db.commit()
    campos = _campos(validators.verificar_emitente(db, empresa.id))
    assert "fiscal_settings" in campos
    assert "numeracao_confirmada" not in campos


# =========================
# 2. Bloqueio efetivo: nada é consumido, nada é transmitido
# =========================

def test_emissao_barrada_nao_consome_numero_nem_chama_a_emissora(
    db, empresa_completa, monkeypatch
):
    from app.services.fiscal import emissao as emissao_mod

    chamadas = []
    monkeypatch.setattr(
        emissao_mod, "get_fiscal_client",
        lambda *a, **k: chamadas.append(("client", a)) or None,
    )
    monkeypatch.setattr(emissao_mod.crud, "get_licenca_token", lambda _db: "tok")

    with pytest.raises(HTTPException) as exc:
        emitir_teste_nfe(db, empresa_completa.id)

    assert exc.value.status_code == 422
    assert exc.value.detail["codigo"] == "EMITENTE_INCOMPLETO"
    assert any("numeração" in m.lower() for m in exc.value.detail["pendencias"])
    assert chamadas == [], "a emissora não pode ser chamada com a trava fechada"
    assert crud.get_fiscal_settings(db, empresa_completa.id).ultimo_numero_nfe == 0


# =========================
# 3. Destravamento pelo serviço de configuração
# =========================

def test_update_explicito_para_true_persiste(db, empresa_completa):
    fs = update_fiscal_settings(
        db, empresa_completa.id, FiscalSettingsUpdate(numeracao_confirmada=True)
    )
    assert fs.numeracao_confirmada is True


@pytest.mark.parametrize("campo", ["serie_nfe", "ultimo_numero_nfe", "serie_nfce", "ultimo_numero_nfce"])
def test_alterar_serie_ou_numero_auto_confirma(db, empresa_completa, campo):
    fs = update_fiscal_settings(
        db, empresa_completa.id, FiscalSettingsUpdate(**{campo: 7})
    )
    assert fs.numeracao_confirmada is True


def test_update_de_outro_campo_nao_confirma(db, empresa_completa):
    fs = update_fiscal_settings(
        db, empresa_completa.id, FiscalSettingsUpdate(ambiente_emissao=1)
    )
    assert fs.numeracao_confirmada is False


def test_update_com_false_explicito_nao_reabre_a_trava_por_engano(db, empresa_completa):
    """`numeracao_confirmada=False` junto com número novo: o número manda (auto-confirma)."""
    fs = update_fiscal_settings(
        db, empresa_completa.id,
        FiscalSettingsUpdate(ultimo_numero_nfe=99, numeracao_confirmada=False),
    )
    assert fs.numeracao_confirmada is True
