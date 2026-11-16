# ---------------------------------------------------------------------------
# ARQUIVO: test/services/fiscal/test_troca_cfop.py
# DESCRIÇÃO: As regras puras da troca de CFOP na conferência (C1).
# ---------------------------------------------------------------------------
import pytest

from app.services.fiscal.derivacao.troca_cfop import (
    TrocaCfopInvalidaError,
    cfop_para_o_cadastro,
    natureza_da_nota,
    opcoes_de_troca,
    situacao_apos_troca,
    validar_troca,
)


@pytest.mark.parametrize("cfop, esperado", [
    ("5102", ["5101", "5102", "5103", "5104", "5405"]),
    ("5405", ["5101", "5102", "5103", "5104", "5405"]),
    ("6102", ["6101", "6102", "6103", "6104"]),
    ("6108", ["6107", "6108"]),
    ("5117", ["5116", "5117"]),
])
def test_opcoes_sao_da_mesma_familia(cfop, esperado):
    assert opcoes_de_troca(cfop) == esperado


@pytest.mark.parametrize("cfop", ["5922", "6922", "6403", "6404", "6401", "5933", "", None])
def test_cfop_decidido_pela_operacao_fica_travado(cfop):
    assert opcoes_de_troca(cfop) == []


@pytest.mark.parametrize("de, para", [
    ("5102", "6102"),   # destino é decisão do motor, não da conferência
    ("6102", "6108"),   # contribuinte × não contribuinte
    ("5922", "5102"),   # simples faturamento é o papel da nota
    ("6404", "6102"),   # ST como substituto: decide o perfil
])
def test_troca_que_muda_a_operacao_e_recusada(de, para):
    with pytest.raises(TrocaCfopInvalidaError):
        validar_troca(de, para)


def test_trocar_pelo_mesmo_nao_e_troca():
    validar_troca("5922", "5922")


@pytest.mark.parametrize("de, para, simples, csosn, cst, esperado", [
    ("5102", "5405", True, "102", None, ("500", None)),
    ("5405", "5102", True, "500", None, ("102", None)),
    ("5102", "5405", False, None, "00", (None, "60")),
    ("5405", "5101", False, None, "60", (None, "00")),
    ("5102", "5101", True, "101", None, ("101", None)),   # mesma família: situação fica
    ("6102", "6101", False, None, "20", (None, "20")),
])
def test_situacao_acompanha_so_ao_cruzar_o_5405(de, para, simples, csosn, cst, esperado):
    assert situacao_apos_troca(de, para, simples, csosn, cst) == esperado


def test_natureza_so_com_um_cfop_na_nota():
    assert natureza_da_nota({"5101"}) == "Venda de producao do estabelecimento"
    assert natureza_da_nota({"5101", "5405"}) is None


@pytest.mark.parametrize("cfop, esperado", [("5101", "5101"), ("6102", "5102"), ("6107", "5101"), ("6108", "5102")])
def test_cadastro_guarda_o_cfop_interno(cfop, esperado):
    assert cfop_para_o_cadastro(cfop) == esperado


# --- No resolver: nota mista (oficina: peça sem ST + peça com ST) --------------

def _nota_mista():
    from app.db.models.produto import Produto
    from app.db.models.produto_fiscal import ProdutoFiscal
    from app.db.models.venda import Venda
    from app.db.models.venda_nota_fiscal import VendaNotaFiscal
    from app.db.models.venda_produto import ProdutoVenda

    venda = Venda(id=1, numero_venda=1001, subtotal=20000, total=20000, entrega=0, acrescimo=0)
    venda.itens = []
    for n, (cfop, csosn) in enumerate([("5102", "102"), ("5405", "500")], start=1):
        produto = Produto(id=n, nome=f"Peca {n}", codigo_produto=f"P{n}", unidade_medida="UN")
        produto.fiscal = ProdutoFiscal(produto_id=n, ncm="84212300", cfop_padrao=cfop, origem_mercadoria=0, csosn=csosn)
        item = ProdutoVenda(id=n, produto_id=n, quantidade=1, valor_unitario=10000, subtotal=10000, desconto=0)
        item.produto = produto
        venda.itens.append(item)
    venda.cliente = None
    venda.nota_fiscal = VendaNotaFiscal(venda_id=1, indicador_presenca=1)
    return venda


@pytest.fixture
def db():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from app.db.base import Base

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    sessao = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    yield sessao
    sessao.close()


def test_resolver_troca_so_o_grupo_pedido(db):
    from app.services.fiscal.tax_engine.resolver import resolver_aliquotas_venda

    itens, _ = resolver_aliquotas_venda(db, _nota_mista(), "CE", True, trocar_cfop={"5102": "5101"})
    assert [(i.cfop, i.cfop_sugerido, i.csosn) for i in itens] == [
        ("5101", "5102", "102"),
        ("5405", None, "500"),   # a peça com ST não foi tocada
    ]


def test_resolver_sem_troca_nao_marca_sugerido(db):
    from app.services.fiscal.tax_engine.resolver import resolver_aliquotas_venda

    itens, _ = resolver_aliquotas_venda(db, _nota_mista(), "CE", True)
    assert [(i.cfop, i.cfop_sugerido) for i in itens] == [("5102", None), ("5405", None)]
