"""
Itens do drawer da nota com quantidade quebrada (venda fracionada, F3).

Até 07/10/2026 o drawer arredondava os milésimos do snapshot para inteiro —
a nota de 3,5 kg aparecia com 4 — e o schema `int` recusava 3,5 da venda.
"""
from types import SimpleNamespace

from app.schemas.documento_fiscal import DocumentoItemResumo
from app.services.documento_fiscal import _itens_do_snapshot


def _item_snapshot(milesimos):
    return SimpleNamespace(
        id=1, produto_id=1, descricao="Sacola Kraft", codigo_barras=None,
        quantidade_milesimos=milesimos, valor_unitario=3001, valor_bruto=10504, valor_desconto=0,
        ncm="48192000", cfop="5102", quantidade_devolvida_acumulada=0,
    )


def test_snapshot_de_tres_e_meio_kg_mostra_tres_e_meio():
    [item] = _itens_do_snapshot(SimpleNamespace(itens=[_item_snapshot(3500)]))
    assert item.quantidade == 3.5


def test_snapshot_inteiro_segue_inteiro():
    [item] = _itens_do_snapshot(SimpleNamespace(itens=[_item_snapshot(3000)]))
    assert item.quantidade == 3 and type(item.quantidade) is int


def test_item_da_venda_com_fracao_nao_derruba_o_schema():
    item = DocumentoItemResumo(nome="Sacola", quantidade=3.5, valor_unitario=3001, subtotal=10504)
    assert item.model_dump()["quantidade"] == 3.5
