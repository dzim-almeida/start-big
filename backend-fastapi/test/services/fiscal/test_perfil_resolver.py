# ---------------------------------------------------------------------------
# ARQUIVO: test/services/fiscal/test_perfil_resolver.py
# DESCRIÇÃO: TASK006 CA-3 — `resolver_regra_perfil`: a regra mais específica
#            do perfil para (UF de destino, NCM), em UMA query.
# ---------------------------------------------------------------------------

import pytest
import sqlalchemy as sa

from app.db.models.empresa import Empresa
from app.db.models.perfil_tributario import PerfilTributario
from app.db.models.regra_perfil_tributario import RegraPerfilTributario
from app.services.fiscal.tax_engine.perfil_resolver import resolver_regra_perfil

CELULAR = "85171200"


def _regra(**campos) -> RegraPerfilTributario:
    base = dict(aliquota_interestadual=1200, aliquota_interna_destino=1800)
    base.update(campos)
    return RegraPerfilTributario(**base)


@pytest.fixture
def perfil(db_session) -> PerfilTributario:
    """Fallback + SP genérica + SP/celular + AM genérica. As alíquotas internas identificam cada regra."""
    empresa = Empresa(razao_social="Loja", documento="11111111000191", is_cnpj=True)
    db_session.add(empresa)
    db_session.flush()
    p = PerfilTributario(empresa_id=empresa.id, descricao="Varejo")
    p.regras = [
        _regra(aliquota_interna_destino=1700),                                      # fallback
        _regra(uf_destino="SP", aliquota_interna_destino=1800),                     # SP genérica
        _regra(uf_destino="SP", ncm_excecao=CELULAR, aliquota_interna_destino=2500),  # SP + celular
        _regra(uf_destino="AM", aliquota_interna_destino=2000),                     # AM genérica
    ]
    db_session.add(p)
    db_session.commit()
    return p


def test_uf_e_ncm_exatos_vencem(db_session, perfil):
    regra = resolver_regra_perfil(db_session, perfil.id, "SP", CELULAR)
    assert (regra.uf_destino, regra.ncm_excecao, regra.aliquota_interna_destino) == ("SP", CELULAR, 2500)


def test_sem_excecao_para_o_ncm_cai_na_regra_da_uf(db_session, perfil):
    regra = resolver_regra_perfil(db_session, perfil.id, "SP", "84713012")
    assert (regra.uf_destino, regra.ncm_excecao, regra.aliquota_interna_destino) == ("SP", None, 1800)


def test_sem_regra_para_a_uf_cai_no_fallback(db_session, perfil):
    regra = resolver_regra_perfil(db_session, perfil.id, "RJ", CELULAR)
    assert (regra.uf_destino, regra.ncm_excecao, regra.aliquota_interna_destino) == (None, None, 1700)


def test_ncm_none_no_produto_usa_a_regra_da_uf(db_session, perfil):
    assert resolver_regra_perfil(db_session, perfil.id, "AM", None).aliquota_interna_destino == 2000
    assert resolver_regra_perfil(db_session, perfil.id, "RJ", None).aliquota_interna_destino == 1700


def test_uf_e_normalizada(db_session, perfil):
    assert resolver_regra_perfil(db_session, perfil.id, " sp ", CELULAR).aliquota_interna_destino == 2500


def test_perfil_inexistente_devolve_none(db_session, perfil):
    assert resolver_regra_perfil(db_session, 999, "SP", None) is None


def test_perfil_sem_fallback_nem_regra_da_uf_devolve_none(db_session, perfil):
    db_session.execute(sa.delete(RegraPerfilTributario).where(RegraPerfilTributario.uf_destino.is_(None)))
    db_session.commit()
    assert resolver_regra_perfil(db_session, perfil.id, "RJ", None) is None


def test_ncm_sem_uf_e_ignorado(db_session, perfil):
    """(NULL, NCM) não tem sentido operacional: a alíquota depende sempre do destino."""
    perfil.regras.append(_regra(ncm_excecao=CELULAR, aliquota_interna_destino=9900))
    db_session.commit()
    assert resolver_regra_perfil(db_session, perfil.id, "RJ", CELULAR).aliquota_interna_destino == 1700


def test_faz_uma_unica_query(db_session, perfil):
    perfil_id = perfil.id  # fora da contagem: o commit da fixture expirou o objeto
    executadas: list[str] = []

    def _registrar(conn, cursor, statement, *_):
        executadas.append(statement)

    engine = db_session.get_bind()
    sa.event.listen(engine, "before_cursor_execute", _registrar)
    try:
        resolver_regra_perfil(db_session, perfil_id, "SP", CELULAR)
    finally:
        sa.event.remove(engine, "before_cursor_execute", _registrar)

    assert len([q for q in executadas if q.lstrip().upper().startswith("SELECT")]) == 1
