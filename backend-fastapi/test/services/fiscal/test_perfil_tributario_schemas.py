# ---------------------------------------------------------------------------
# ARQUIVO: test/services/fiscal/test_perfil_tributario_schemas.py
# DESCRIÇÃO: TASK005 CA-1 — o que os schemas do perfil tributário aceitam e
#            recusam. Sem banco.
# ---------------------------------------------------------------------------

import pytest
from pydantic import ValidationError

from app.schemas.perfil_tributario import (
    PerfilTributarioCreate,
    RegraPerfilTributarioBase,
)


def regra(**campos) -> dict:
    base = {"aliquota_interestadual": 1200, "aliquota_interna_destino": 1800}
    base.update(campos)
    return base


FALLBACK = regra()


def perfil(*regras, descricao="Varejo - Eletrônicos") -> dict:
    return {"descricao": descricao, "regras": list(regras)}


# --- Regra ------------------------------------------------------------------

def test_regra_minima_e_valida_com_defaults():
    r = RegraPerfilTributarioBase(**FALLBACK)
    assert r.uf_destino is None and r.ncm_excecao is None
    assert r.percentual_fcp == 0 and r.calculo_base_dupla is False
    assert r.mva_st is None and r.reducao_base_calculo is None


def test_uf_e_normalizada_para_maiusculas():
    assert RegraPerfilTributarioBase(**regra(uf_destino=" sp ")).uf_destino == "SP"


@pytest.mark.parametrize("uf", ["XX", "SPP", "S", "BR"])
def test_uf_invalida_e_recusada(uf):
    with pytest.raises(ValidationError, match="UF"):
        RegraPerfilTributarioBase(**regra(uf_destino=uf))


@pytest.mark.parametrize("ncm", ["8517120", "851712001", "8517120A", "85.17.12.00"])
def test_ncm_fora_de_8_digitos_e_recusado(ncm):
    with pytest.raises(ValidationError, match="8 dígitos"):
        RegraPerfilTributarioBase(**regra(ncm_excecao=ncm))


def test_uf_e_ncm_vazios_viram_none():
    r = RegraPerfilTributarioBase(**regra(uf_destino="", ncm_excecao=""))
    assert r.uf_destino is None and r.ncm_excecao is None


def test_aliquotas_aceitam_zero():
    r = RegraPerfilTributarioBase(**regra(aliquota_interestadual=0, aliquota_interna_destino=0, percentual_fcp=0))
    assert r.aliquota_interestadual == 0


@pytest.mark.parametrize("campo, valor", [
    ("aliquota_interestadual", 2501),
    ("aliquota_interna_destino", 3501),
    ("percentual_fcp", 601),
    ("mva_st", 50001),
    ("reducao_base_calculo", 10001),
    ("aliquota_interestadual", -1),
])
def test_percentuais_fora_da_faixa_sao_recusados(campo, valor):
    with pytest.raises(ValidationError):
        RegraPerfilTributarioBase(**regra(**{campo: valor}))


def test_mva_e_reducao_aceitam_null_explicito():
    r = RegraPerfilTributarioBase(**regra(mva_st=None, reducao_base_calculo=None))
    assert r.mva_st is None and r.reducao_base_calculo is None


# --- Perfil -------------------------------------------------------------------

def test_perfil_valido_com_fallback_e_regras_especificas():
    p = PerfilTributarioCreate(**perfil(
        FALLBACK, regra(uf_destino="SP"), regra(uf_destino="SP", ncm_excecao="85171200"),
    ))
    assert len(p.regras) == 3
    assert p.descricao == "Varejo - Eletrônicos"


def test_descricao_e_aparada_e_curta_e_recusada():
    assert PerfilTributarioCreate(**perfil(FALLBACK, descricao="  Varejo  ")).descricao == "Varejo"
    with pytest.raises(ValidationError):
        PerfilTributarioCreate(**perfil(FALLBACK, descricao="ab"))


def test_perfil_sem_regras_e_recusado():
    with pytest.raises(ValidationError):
        PerfilTributarioCreate(**perfil())


def test_perfil_sem_fallback_e_recusado():
    with pytest.raises(ValidationError, match="fallback"):
        PerfilTributarioCreate(**perfil(regra(uf_destino="SP")))


def test_perfil_com_dois_fallbacks_e_recusado():
    with pytest.raises(ValidationError, match="mais de uma regra de fallback"):
        PerfilTributarioCreate(**perfil(FALLBACK, regra(percentual_fcp=200)))


def test_regras_duplicadas_sao_recusadas():
    with pytest.raises(ValidationError, match="duplicadas"):
        PerfilTributarioCreate(**perfil(FALLBACK, regra(uf_destino="SP"), regra(uf_destino="sp")))


def test_ncm_em_ufs_diferentes_nao_e_duplicata():
    p = PerfilTributarioCreate(**perfil(
        FALLBACK, regra(uf_destino="SP", ncm_excecao="85171200"), regra(uf_destino="RJ", ncm_excecao="85171200"),
    ))
    assert len(p.regras) == 3
