# ---------------------------------------------------------------------------
# ARQUIVO: test/services/marcenaria/test_leitor.py
# DESCRICAO: Leitor de codigo de barras da separacao (Spec 10A, D20, caso 15).
#
#            O que nao pode errar:
#              - so acha entre os itens DESTA OS;
#              - codigo de barras antes do codigo do produto, e os dois antes
#                da embalagem; embalagem inativa nao conta;
#              - a embalagem devolve o fator (caixa de 10 = 10).
# ---------------------------------------------------------------------------

from types import SimpleNamespace

from app.db.models.produto import Produto
from app.db.models.produto_embalagem import ProdutoEmbalagem
from app.services.marcenaria import leitor


def _item(item_id: int, produto_id: int):
    """Um item de OS de mentira: o leitor so olha `id` e `produto_id`."""
    return SimpleNamespace(id=item_id, produto_id=produto_id)


def test_codigo_de_barras_antes_do_codigo_do_produto(db_session, produto):
    # O SKU de A e igual ao codigo de barras de B: o codigo de barras ganha.
    a = produto("Chapa A", codigo="789100")
    b = produto("Chapa B", codigo="CH-B")
    db_session.get(Produto, b).codigo_barras = "789100"
    db_session.commit()
    itens = [_item(1, a), _item(2, b)]
    assert leitor.achar(db_session, itens, "789100") == (itens[1], 1)
    assert leitor.achar(db_session, itens, " CH-B ") == (itens[1], 1)     # espacos do leitor nao atrapalham


def test_embalagem_ativa_com_fator(db_session, produto):
    corredica = produto("Corrediça", codigo="COR-1")
    db_session.add_all([
        ProdutoEmbalagem(produto_id=corredica, sigla="CX", fator=10, codigo_barras="CX10"),
        ProdutoEmbalagem(produto_id=corredica, sigla="FD", fator=50, codigo_barras="FD50", ativo=False),
    ])
    db_session.commit()
    itens = [_item(7, corredica)]
    assert leitor.achar(db_session, itens, "CX10") == (itens[0], 10)
    assert leitor.achar(db_session, itens, "FD50") is None               # inativa


def test_so_entre_os_itens_desta_os(db_session, produto):
    de_fora = produto("Dobradiça", codigo="DOB-35")
    dentro = produto("Chapa", codigo="CH-1")
    db_session.add(ProdutoEmbalagem(produto_id=de_fora, sigla="CX", fator=10, codigo_barras="CXDOB"))
    db_session.commit()
    itens = [_item(1, dentro)]
    assert leitor.achar(db_session, itens, "DOB-35") is None
    assert leitor.achar(db_session, itens, "CXDOB") is None
    assert leitor.achar(db_session, itens, "") is None
    assert leitor.achar(db_session, [], "CH-1") is None
