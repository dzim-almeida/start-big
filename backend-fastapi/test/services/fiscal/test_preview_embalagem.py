# ---------------------------------------------------------------------------
# ARQUIVO: test/services/fiscal/test_preview_embalagem.py
# DESCRIÇÃO: A prévia da emissão mostra a embalagem da linha ("2 FD", 24 un).
#
# Antes a conferência dizia "2" para dois fardos — o operador não tinha como
# saber se ia sair 2 latas ou 24. Linha de unidade continua igual.
# ---------------------------------------------------------------------------

from app.db.models.produto import Produto
from app.db.models.produto_fiscal import ProdutoFiscal
from app.db.models.venda import Venda
from app.db.models.venda_produto import ProdutoVenda
from app.schemas.emissao_fiscal import EmissaoPreviewResponse
from app.services.fiscal import emissao


def _venda():
    produto = Produto(id=1, nome="Cerveja Lata", codigo_produto="CERV", unidade_medida="UN")
    produto.fiscal = ProdutoFiscal(produto_id=1, ncm="22030000", cfop_padrao="5405", cst_icms="60", csosn="500")
    venda = Venda(id=1, entrega=0, total=10950)
    venda.itens = [
        ProdutoVenda(id=1, produto_id=1, produto=produto, quantidade=2, valor_unitario=4800, subtotal=9600,
                     desconto=0, desconto_regra=0, fator_embalagem=12, sigla_embalagem="FD"),
        ProdutoVenda(id=2, produto_id=1, produto=produto, quantidade=3, valor_unitario=450, subtotal=1350,
                     desconto=0, desconto_regra=0, fator_embalagem=1, sigla_embalagem=None),
    ]
    return venda


def test_previa_leva_sigla_e_fator_da_embalagem(monkeypatch):
    venda = _venda()
    monkeypatch.setattr(emissao, "_preparar_dados_emissao", lambda db, vid, eid: (None, None, venda, True, None))

    previa = EmissaoPreviewResponse(**emissao.preview_nfe_venda(None, 1, 1))
    fardo, lata = previa.itens
    assert (fardo.quantidade, fardo.sigla_embalagem, fardo.fator_embalagem) == (2, "FD", 12)
    assert (lata.quantidade, lata.sigla_embalagem, lata.fator_embalagem) == (3, None, 1)
