# ---------------------------------------------------------------------------
# ARQUIVO: test/services/fiscal/test_payload_regra_preco.py
# DESCRIÇÃO: Regra de preço por quantidade na NF-e/NFC-e (§6.1, fase 5).
#
# R1/R3 saem como desconto do item (vDesc) — operador + regra somados. R2 sai
# como preço praticado (vUnCom), sem desconto. Linha sem regra: como antes.
# ---------------------------------------------------------------------------

from app.db.models.produto import Produto
from app.db.models.produto_fiscal import ProdutoFiscal
from app.db.models.venda import Venda
from app.db.models.venda_produto import ProdutoVenda
from app.services.fiscal.payload_builder import _montar_itens


def _produto():
    produto = Produto(id=1, nome="Cerveja Lata", codigo_produto="CERV", unidade_medida="UN",
                      codigo_barras="7891234567895")
    produto.fiscal = ProdutoFiscal(produto_id=1, ncm="22030000", cfop_padrao="5405", origem_mercadoria=0,
                                   unidade_tributavel="UN", cst_icms="60", csosn="500")
    return produto


def _item(quantidade, valor_unitario, desconto=0, desconto_regra=0):
    venda = Venda(id=1)
    venda.itens = [ProdutoVenda(id=1, produto_id=1, produto=_produto(), quantidade=quantidade,
                                valor_unitario=valor_unitario, subtotal=quantidade * valor_unitario,
                                desconto=desconto, desconto_regra=desconto_regra)]
    [item] = _montar_itens(venda, simples_nacional=False)
    return item


def test_r1_e_r3_vao_no_vdesc_somados_ao_do_operador():
    item = _item(17, 450, desconto=100, desconto_regra=1750)
    assert (item["quantidade_comercial"], item["valor_unitario_comercial"], item["valor_bruto"]) == (17.0, 4.5, 76.5)
    assert item["valor_desconto"] == 18.5


def test_r2_vai_como_preco_praticado_sem_desconto():
    item = _item(6, 380)
    assert (item["valor_unitario_comercial"], item["valor_bruto"]) == (3.8, 22.8)
    assert "valor_desconto" not in item


def test_linha_sem_regra_sai_como_antes():
    item = _item(3, 450, desconto=50)
    assert item["valor_desconto"] == 0.5
