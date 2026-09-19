# ---------------------------------------------------------------------------
# ARQUIVO: test/services/fiscal/test_produto_fiscal_perfil.py
# DESCRIÇÃO: TASK006 CA-1/2/4 — o vínculo produto_fiscal.perfil_tributario_id
#            visto pelo serviço de dados fiscais e pelo guard de exclusão.
# ---------------------------------------------------------------------------

import pytest
import sqlalchemy as sa
from fastapi import HTTPException

from app.db.models.empresa import Empresa
from app.db.models.perfil_tributario import PerfilTributario
from app.db.models.produto import Produto
from app.db.models.produto_fiscal import ProdutoFiscal
from app.db.models.regra_perfil_tributario import RegraPerfilTributario
from app.schemas.produto_fiscal import ProdutoFiscalRead, ProdutoFiscalUpdate
from app.services import perfil_tributario as perfil_service
from app.services import produto_fiscal as service


@pytest.fixture
def cenario(db_session):
    """Duas empresas, um perfil em cada, um produto (da empresa A) com NCM."""
    a = Empresa(razao_social="Loja A", documento="11111111000191", is_cnpj=True)
    b = Empresa(razao_social="Loja B", documento="22222222000192", is_cnpj=True)
    db_session.add_all([a, b])
    db_session.flush()
    perfil_a = PerfilTributario(empresa_id=a.id, descricao="Varejo A")
    perfil_b = PerfilTributario(empresa_id=b.id, descricao="Varejo B")
    for p in (perfil_a, perfil_b):
        p.regras = [RegraPerfilTributario(aliquota_interestadual=1200, aliquota_interna_destino=1800)]
    produto = Produto(nome="Celular X", codigo_produto="CEL-1", unidade_medida="UN")
    db_session.add_all([perfil_a, perfil_b, produto])
    db_session.commit()
    service.upsert_dados_fiscais(db_session, produto.id, a.id, ProdutoFiscalUpdate(ncm="85171200"))
    db_session.commit()
    return a, b, perfil_a, perfil_b, produto


def _fiscal(db_session, produto) -> ProdutoFiscal:
    db_session.expire_all()
    return db_session.scalars(sa.select(ProdutoFiscal).where(ProdutoFiscal.produto_id == produto.id)).one()


# --- Model -----------------------------------------------------------------

def test_coluna_e_fk_set_null_com_indice():
    coluna = ProdutoFiscal.__table__.c.perfil_tributario_id
    fk = next(iter(coluna.foreign_keys))
    assert coluna.nullable and coluna.index
    assert fk.target_fullname == "perfil_tributario.id" and fk.ondelete == "SET NULL"


def test_relationship_carrega_o_perfil(db_session, cenario):
    a, _, perfil_a, _, produto = cenario
    service.upsert_dados_fiscais(db_session, produto.id, a.id, ProdutoFiscalUpdate(perfil_tributario_id=perfil_a.id))
    db_session.commit()
    assert _fiscal(db_session, produto).perfil_tributario.descricao == "Varejo A"


# --- Schema / serviço ---------------------------------------------------------

def test_vincular_e_ler_de_volta(db_session, cenario):
    a, _, perfil_a, _, produto = cenario
    service.upsert_dados_fiscais(db_session, produto.id, a.id, ProdutoFiscalUpdate(perfil_tributario_id=perfil_a.id))
    db_session.commit()

    lido = ProdutoFiscalRead.model_validate(_fiscal(db_session, produto))
    assert lido.perfil_tributario_id == perfil_a.id
    assert lido.ncm == "85171200"


def test_null_explicito_desvincula(db_session, cenario):
    a, _, perfil_a, _, produto = cenario
    service.upsert_dados_fiscais(db_session, produto.id, a.id, ProdutoFiscalUpdate(perfil_tributario_id=perfil_a.id))
    db_session.commit()

    service.upsert_dados_fiscais(db_session, produto.id, a.id, ProdutoFiscalUpdate(perfil_tributario_id=None))
    db_session.commit()
    assert _fiscal(db_session, produto).perfil_tributario_id is None


def test_omitir_o_campo_mantem_o_vinculo(db_session, cenario):
    """O formulário atual do produto não conhece o campo: salvar o produto não pode desvincular."""
    a, _, perfil_a, _, produto = cenario
    service.upsert_dados_fiscais(db_session, produto.id, a.id, ProdutoFiscalUpdate(perfil_tributario_id=perfil_a.id))
    db_session.commit()

    service.upsert_dados_fiscais(db_session, produto.id, a.id, ProdutoFiscalUpdate(cfop_padrao="5102"))
    db_session.commit()

    fiscal = _fiscal(db_session, produto)
    assert fiscal.perfil_tributario_id == perfil_a.id and fiscal.cfop_padrao == "5102" and fiscal.ncm == "85171200"


def test_perfil_de_outra_empresa_e_422(db_session, cenario):
    a, _, _, perfil_b, produto = cenario
    with pytest.raises(HTTPException) as exc:
        service.upsert_dados_fiscais(db_session, produto.id, a.id, ProdutoFiscalUpdate(perfil_tributario_id=perfil_b.id))
    assert exc.value.status_code == 422
    assert exc.value.detail["codigo"] == "PERFIL_TRIBUTARIO_INVALIDO"


def test_perfil_inexistente_e_422(db_session, cenario):
    a, _, _, _, produto = cenario
    with pytest.raises(HTTPException) as exc:
        service.upsert_dados_fiscais(db_session, produto.id, a.id, ProdutoFiscalUpdate(perfil_tributario_id=999))
    assert exc.value.status_code == 422


# --- Guard de exclusão (CA-4) -------------------------------------------------

def test_produtos_que_usam_lista_os_nomes(db_session, cenario):
    a, _, perfil_a, _, produto = cenario
    assert perfil_service.crud.produtos_que_usam(db_session, perfil_a.id) == []

    service.upsert_dados_fiscais(db_session, produto.id, a.id, ProdutoFiscalUpdate(perfil_tributario_id=perfil_a.id))
    db_session.commit()
    assert perfil_service.crud.produtos_que_usam(db_session, perfil_a.id) == ["Celular X"]


def test_excluir_perfil_em_uso_e_409(db_session, cenario):
    a, _, perfil_a, _, produto = cenario
    service.upsert_dados_fiscais(db_session, produto.id, a.id, ProdutoFiscalUpdate(perfil_tributario_id=perfil_a.id))
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        perfil_service.deletar_perfil(db_session, a.id, perfil_a.id)
    assert exc.value.status_code == 409 and "Celular X" in exc.value.detail["mensagem"]


def test_apagar_perfil_direto_no_banco_seta_null_no_produto(db_session, cenario):
    """Se o guard for contornado, o produto sobrevive sem perfil (SET NULL)."""
    a, _, perfil_a, _, produto = cenario
    service.upsert_dados_fiscais(db_session, produto.id, a.id, ProdutoFiscalUpdate(perfil_tributario_id=perfil_a.id))
    db_session.commit()

    db_session.execute(sa.delete(PerfilTributario).where(PerfilTributario.id == perfil_a.id))
    db_session.commit()

    assert _fiscal(db_session, produto).perfil_tributario_id is None


# --- Cascata: o perfil é só do produto ---------------------------------------

def test_fiscal_efetivo_carrega_o_perfil_do_produto_sem_cascata():
    """`perfil_tributario_id` desce para o efetivo como campo do produto; NCM e padrão não opinam."""
    from types import SimpleNamespace
    from app.services.fiscal.tributacao import mesclar

    produto = SimpleNamespace(ncm="85171200", perfil_tributario_id=7)
    padrao = SimpleNamespace(csosn="102", perfil_tributario_id=99)  # nunca lido
    efetivo = mesclar(produto_fiscal=produto, padrao=padrao)

    assert efetivo.perfil_tributario_id == 7
    assert efetivo.procedencia["perfil_tributario_id"] == "produto"
    assert mesclar(produto_fiscal=SimpleNamespace(ncm="1"), padrao=padrao).perfil_tributario_id is None
