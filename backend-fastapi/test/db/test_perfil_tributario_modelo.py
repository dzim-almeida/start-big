# ---------------------------------------------------------------------------
# ARQUIVO: test/db/test_perfil_tributario_modelo.py
# DESCRIÇÃO: Os models PerfilTributario e RegraPerfilTributario (TASK004).
#            Banco SQLite em memória com PRAGMA foreign_keys=ON (o listener
#            de app/db/session.py vale para qualquer engine do processo).
# ---------------------------------------------------------------------------

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.db.session  # noqa: F401  -- registra o PRAGMA foreign_keys=ON
from app.db.base import Base
from app.db.models.empresa import Empresa
from app.db.models.perfil_tributario import PerfilTributario
from app.db.models.regra_perfil_tributario import RegraPerfilTributario


@pytest.fixture
def db() -> Session:
    engine = sa.create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    sessao = sessionmaker(bind=engine)()
    yield sessao
    sessao.close()
    engine.dispose()


@pytest.fixture
def empresa(db) -> Empresa:
    emp = Empresa(
        razao_social="Loja Teste LTDA",
        documento="12345678000199",
        is_cnpj=True,
    )
    db.add(emp)
    db.commit()
    return emp


def _regra(**campos) -> RegraPerfilTributario:
    base = dict(aliquota_interestadual=1200, aliquota_interna_destino=1800)
    base.update(campos)
    return RegraPerfilTributario(**base)


# --- Estrutura das tabelas ---------------------------------------------------

def test_tabelas_tem_os_nomes_da_spec():
    assert PerfilTributario.__tablename__ == "perfil_tributario"
    assert RegraPerfilTributario.__tablename__ == "regra_perfil_tributario"


def test_colunas_do_perfil():
    colunas = {c.name: c for c in PerfilTributario.__table__.columns}
    assert set(colunas) == {"id", "empresa_id", "descricao", "data_criacao", "data_atualizacao"}
    assert isinstance(colunas["descricao"].type, sa.String) and colunas["descricao"].type.length == 120
    assert colunas["empresa_id"].nullable is False
    fk = next(iter(colunas["empresa_id"].foreign_keys))
    assert fk.target_fullname == "empresas.id" and fk.ondelete == "CASCADE"


def test_colunas_da_regra():
    colunas = {c.name: c for c in RegraPerfilTributario.__table__.columns}
    assert set(colunas) == {
        "id", "perfil_id", "uf_destino", "ncm_excecao",
        "aliquota_interestadual", "aliquota_interna_destino", "percentual_fcp",
        "calculo_base_dupla", "mva_st", "reducao_base_calculo",
    }
    assert colunas["uf_destino"].type.length == 2 and colunas["uf_destino"].nullable
    assert colunas["ncm_excecao"].type.length == 8 and colunas["ncm_excecao"].nullable
    for obrigatoria in ("aliquota_interestadual", "aliquota_interna_destino", "percentual_fcp", "calculo_base_dupla"):
        assert colunas[obrigatoria].nullable is False, obrigatoria
    for opcional in ("mva_st", "reducao_base_calculo"):
        assert colunas[opcional].nullable is True, opcional
    fk = next(iter(colunas["perfil_id"].foreign_keys))
    assert fk.target_fullname == "perfil_tributario.id" and fk.ondelete == "CASCADE"


def test_regra_tem_unique_perfil_uf_ncm():
    uniques = [c for c in RegraPerfilTributario.__table__.constraints if isinstance(c, sa.UniqueConstraint)]
    assert any(
        c.name == "uq_regra_perfil_uf_ncm" and [col.name for col in c.columns] == ["perfil_id", "uf_destino", "ncm_excecao"]
        for c in uniques
    )


def test_todas_as_colunas_tem_doc():
    for tabela in (PerfilTributario.__table__, RegraPerfilTributario.__table__):
        for coluna in tabela.columns:
            assert coluna.doc, f"{tabela.name}.{coluna.name} sem doc="


# --- Comportamento ------------------------------------------------------------

def test_defaults_da_regra(db, empresa):
    perfil = PerfilTributario(empresa_id=empresa.id, descricao="Varejo - Eletrônicos")
    perfil.regras.append(_regra())
    db.add(perfil)
    db.commit()

    regra = db.scalars(sa.select(RegraPerfilTributario)).one()
    assert regra.percentual_fcp == 0
    assert regra.calculo_base_dupla is False
    assert regra.uf_destino is None and regra.ncm_excecao is None
    assert regra.mva_st is None and regra.reducao_base_calculo is None
    assert perfil.data_criacao is not None and perfil.data_atualizacao is not None


def test_regra_duplicada_para_mesma_uf_e_ncm_e_rejeitada(db, empresa):
    perfil = PerfilTributario(empresa_id=empresa.id, descricao="Varejo")
    perfil.regras.append(_regra(uf_destino="SP", ncm_excecao="85171200"))
    perfil.regras.append(_regra(uf_destino="SP", ncm_excecao="85171200", aliquota_interna_destino=2000))
    db.add(perfil)
    with pytest.raises(IntegrityError):
        db.commit()


def test_remover_regra_da_colecao_apaga_a_linha(db, empresa):
    perfil = PerfilTributario(empresa_id=empresa.id, descricao="Varejo")
    perfil.regras.extend([_regra(uf_destino="SP"), _regra(uf_destino="RJ")])
    db.add(perfil)
    db.commit()

    perfil.regras.pop(0)  # delete-orphan: sair da coleção basta
    db.commit()

    assert db.scalar(sa.select(sa.func.count()).select_from(RegraPerfilTributario)) == 1


def test_apagar_perfil_apaga_as_regras(db, empresa):
    perfil = PerfilTributario(empresa_id=empresa.id, descricao="Varejo")
    perfil.regras.extend([_regra(uf_destino="SP"), _regra()])
    db.add(perfil)
    db.commit()

    db.delete(perfil)
    db.commit()

    assert db.scalar(sa.select(sa.func.count()).select_from(RegraPerfilTributario)) == 0


def test_apagar_empresa_apaga_perfis_e_regras_pelo_banco(db, empresa):
    perfil = PerfilTributario(empresa_id=empresa.id, descricao="Varejo")
    perfil.regras.append(_regra(uf_destino="MG"))
    db.add(perfil)
    db.commit()

    # DELETE direto no banco: nenhum relationship em Empresa -- a cascata é a FK
    db.execute(sa.delete(Empresa).where(Empresa.id == empresa.id))
    db.commit()

    assert db.scalar(sa.select(sa.func.count()).select_from(PerfilTributario)) == 0
    assert db.scalar(sa.select(sa.func.count()).select_from(RegraPerfilTributario)) == 0


def test_repr_e_legivel(db, empresa):
    perfil = PerfilTributario(empresa_id=empresa.id, descricao="Varejo")
    regra = _regra(uf_destino="SP", ncm_excecao="85171200")
    perfil.regras.append(regra)
    db.add(perfil)
    db.commit()

    assert repr(perfil) == f"<PerfilTributario(id={perfil.id}, descricao='Varejo')>"
    assert repr(regra) == f"<RegraPerfilTributario(id={regra.id}, perfil_id={perfil.id}, uf='SP', ncm='85171200')>"
