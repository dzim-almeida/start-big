# ---------------------------------------------------------------------------
# ARQUIVO: test/services/fiscal/test_nfe_da_os.py
# DESCRIÇÃO: O adaptador que faz uma OS caber no motor fiscal da venda.
#
# É onde moram as decisões que não são óbvias, e cada uma tem um teste:
#   - só peça aprovada entra (mão de obra é NFS-e, que não existe aqui);
#   - o desconto da OS entra pela fatia que cabe aos produtos;
#   - os pagamentos são reduzidos proporcionalmente, senão a soma não fecha
#     com o total da nota e a SEFAZ rejeita (767).
# ---------------------------------------------------------------------------

import pytest

from app.core.enum import OrdemServicoItemAprovacao, OrdemServicoItemTipo
from app.services.fiscal.emissoes.adaptador_os import adaptar, itens_de_produto


class _Forma:
    def __init__(self, codigo="01"):
        self.codigo_sefaz = codigo
        self.tipo_integracao = None


class _Item:
    def __init__(self, tipo, valor_total, aprovacao=OrdemServicoItemAprovacao.APROVADO,
                 produto=None, quantidade=1.0, nome="item"):
        self.tipo = tipo
        self.valor_total = valor_total
        self.valor_unitario = int(valor_total / quantidade) if quantidade else valor_total
        self.status_aprovacao = aprovacao
        self.produtos = produto
        self.produto_id = getattr(produto, "id", None)
        self.quantidade = quantidade
        self.nome = nome


class _Pagamento:
    def __init__(self, valor, codigo="01"):
        self.valor = valor
        self.forma_pagamento = _Forma(codigo)


class _Objeto:
    def __init__(self, cliente=None):
        self.cliente = cliente


class _OS:
    def __init__(self, itens, pagamentos=(), desconto=0, valor_bruto=None):
        self.itens = list(itens)
        self.pagamentos = list(pagamentos)
        self.desconto = desconto
        self.valor_bruto = (
            valor_bruto if valor_bruto is not None
            else sum(i.valor_total for i in self.itens)
        )
        self.valor_total = self.valor_bruto - desconto
        self.objeto = _Objeto()
        self.nota_fiscal = None
        self.numero_os = "OS-2026-000042"
        self.id = 7


class _Produto:
    def __init__(self, id_=1):
        self.id = id_


PRODUTO = OrdemServicoItemTipo.PRODUTO
SERVICO = OrdemServicoItemTipo.SERVICO


# ---------------------------------------------------------------------------
# O recorte: o que entra na nota
# ---------------------------------------------------------------------------

def test_so_produto_entra_na_nfe():
    """Mão de obra não entra: é NFS-e, e este sistema não a emite.

    Se entrasse, a nota diria que a loja vendeu uma mercadoria chamada
    "troca de tela" — com NCM e CFOP de produto. Documento fiscal errado.
    """
    os_obj = _OS([
        _Item(PRODUTO, 10000, produto=_Produto(1), nome="Tela"),
        _Item(SERVICO, 5000, nome="Mão de obra"),
    ])

    assert len(itens_de_produto(os_obj)) == 1
    assert adaptar(os_obj).total == 10000


def test_item_reprovado_nao_entra():
    """Mesmo filtro do gate (`verificar_itens_os_nfe`).

    Se os dois divergissem, o gate aprovaria uma nota diferente da que sai.
    """
    os_obj = _OS([
        _Item(PRODUTO, 10000, produto=_Produto(1)),
        _Item(PRODUTO, 3000, aprovacao=OrdemServicoItemAprovacao.REPROVADO,
              produto=_Produto(2)),
    ])

    assert len(itens_de_produto(os_obj)) == 1
    assert adaptar(os_obj).total == 10000


# ---------------------------------------------------------------------------
# O desconto da OS
# ---------------------------------------------------------------------------

def test_desconto_da_os_entra_pela_fatia_dos_produtos():
    """A OS desconta no total; a nota cobre só as peças.

    Peças 100,00 + serviço 100,00, com 20,00 de desconto: metade do desconto é
    das peças. Levar os 20,00 inteiros subfaturaria a nota; ignorá-los faria a
    nota valer mais do que o cliente pagou pelas peças.
    """
    os_obj = _OS(
        [
            _Item(PRODUTO, 10000, produto=_Produto(1)),
            _Item(SERVICO, 10000),
        ],
        desconto=2000,
    )

    adaptado = adaptar(os_obj)
    assert adaptado.total == 9000
    assert sum(i.desconto for i in adaptado.itens) == 1000


def test_desconto_rateado_nao_perde_centavo():
    """A soma das partes tem que ser exatamente o total — como no rateio."""
    os_obj = _OS(
        [
            _Item(PRODUTO, 3333, produto=_Produto(1)),
            _Item(PRODUTO, 3333, produto=_Produto(2)),
            _Item(PRODUTO, 3334, produto=_Produto(3)),
        ],
        desconto=1000,
    )

    adaptado = adaptar(os_obj)
    assert sum(i.desconto for i in adaptado.itens) == 1000
    assert adaptado.total == 10000 - 1000


def test_os_sem_desconto_nao_inventa_desconto():
    os_obj = _OS([_Item(PRODUTO, 10000, produto=_Produto(1))])
    adaptado = adaptar(os_obj)
    assert all(i.desconto == 0 for i in adaptado.itens)
    assert adaptado.total == 10000


# ---------------------------------------------------------------------------
# Os pagamentos — Rejeição 767
# ---------------------------------------------------------------------------

def test_pagamentos_sao_reduzidos_a_fatia_dos_produtos():
    """A SEFAZ audita `Σ pagamentos − troco == total da nota` (Rejeição 767).

    Os pagamentos da OS cobrem peças E mão de obra. Mandá-los inteiros numa nota
    que cobre só as peças derruba a emissão.
    """
    os_obj = _OS(
        [
            _Item(PRODUTO, 10000, produto=_Produto(1)),
            _Item(SERVICO, 10000),
        ],
        pagamentos=[_Pagamento(20000)],
    )

    adaptado = adaptar(os_obj)
    assert sum(p.valor for p in adaptado.pagamentos) == adaptado.total == 10000


def test_pagamentos_preservam_as_formas_usadas():
    """Reduzir não pode virar "inventar um pagamento único".

    As formas (dinheiro, cartão, PIX) descrevem como o cliente pagou e vão no
    grupo `pag` da nota. Trocar tudo por uma linha só falsearia isso.
    """
    os_obj = _OS(
        [
            _Item(PRODUTO, 10000, produto=_Produto(1)),
            _Item(SERVICO, 10000),
        ],
        pagamentos=[_Pagamento(12000, "01"), _Pagamento(8000, "03")],
    )

    adaptado = adaptar(os_obj)

    assert len(adaptado.pagamentos) == 2
    assert {p.forma_pagamento.codigo_sefaz for p in adaptado.pagamentos} == {"01", "03"}
    assert sum(p.valor for p in adaptado.pagamentos) == adaptado.total


@pytest.mark.parametrize("valores", [
    (3333, 3333, 3334),
    (1, 1, 99998),
    (7777, 2223),
])
def test_soma_dos_pagamentos_fecha_sempre(valores):
    """O centavo do arredondamento não pode sumir — em nenhuma combinação."""
    os_obj = _OS(
        [
            _Item(PRODUTO, 10000, produto=_Produto(1)),
            _Item(SERVICO, 10000),
        ],
        pagamentos=[_Pagamento(v) for v in valores],
    )

    adaptado = adaptar(os_obj)
    assert sum(p.valor for p in adaptado.pagamentos) == adaptado.total


def test_os_sem_pagamento_nao_quebra():
    os_obj = _OS([_Item(PRODUTO, 10000, produto=_Produto(1))])
    assert adaptar(os_obj).pagamentos == []


# ---------------------------------------------------------------------------
# A forma que o motor espera
# ---------------------------------------------------------------------------

def test_item_adaptado_fala_o_vocabulario_da_venda():
    """O motor lê `produto`, `subtotal` e `desconto` — a OS usa outros nomes."""
    produto = _Produto(9)
    os_obj = _OS([_Item(PRODUTO, 5000, produto=produto, quantidade=2.5)])

    item = adaptar(os_obj).itens[0]

    assert item.produto is produto        # na OS o relacionamento é `produtos`
    assert item.subtotal == 5000          # na OS é `valor_total`
    assert item.produto_id == 9
    assert item.quantidade == 2.5         # fracionária (serigrafia) preservada


def test_frete_e_acrescimo_ficam_fora_da_nota_da_os():
    """São da OS inteira; uma fatia deles mexeria na base de ICMS das peças."""
    adaptado = adaptar(_OS([_Item(PRODUTO, 10000, produto=_Produto(1))]))
    assert adaptado.entrega == 0
    assert adaptado.acrescimo == 0
    assert adaptado.troco == 0


# ---------------------------------------------------------------------------
# A prévia da NF-e da OS (C2 de docs/nfe-cfop-e-notas-da-os-plano.md)
# ---------------------------------------------------------------------------

def test_previa_da_os_tem_o_formato_da_resposta(monkeypatch):
    """Até 01/11/2026 a prévia devolvia os itens do payload e a rota dava 500."""
    from decimal import Decimal

    from app.schemas.fiscal.emissao import EmissaoPreviewResponse
    from app.services.fiscal.emissoes import nfe_os
    from app.services.fiscal.tax_engine.types import ImpostosItem, ResultadoCalculo

    class _ProdutoNomeado(_Produto):
        nome = "Filtro de oleo"

    os_obj = _OS([_Item(PRODUTO, 3000, produto=_ProdutoNomeado(), nome="Filtro de oleo")], [_Pagamento(3000)])
    os_como_venda = adaptar(os_obj)
    zero = Decimal("0")
    imp = ImpostosItem.model_construct(
        numero_item=1, cfop="5101", cfop_sugerido="5102", icms_situacao_tributaria="102",
        icms_valor=zero, pis_valor=zero, cofins_valor=zero,
    )
    resultado = ResultadoCalculo.model_construct(itens=[imp])

    monkeypatch.setattr(nfe_os, "_preparar_dados_emissao_os",
                        lambda *a, **k: (None, None, os_obj, os_como_venda, True, resultado))
    monkeypatch.setattr(nfe_os, "_obter_fiscal_settings", lambda *a: None)
    monkeypatch.setattr(nfe_os, "_fiscais_efetivos", lambda *a: {})
    monkeypatch.setattr(nfe_os, "_avisos", lambda *a: [])
    monkeypatch.setattr(nfe_os, "montar_payload_nfe", lambda *a, **k: {
        "items": [{"descricao": "Filtro de oleo", "ncm": "84212300", "cfop": "5101"}],
        "destinatario": {"nome": "Seu Jorge", "cpf": "11144477735"},
    })

    previa = EmissaoPreviewResponse(**nfe_os.preview_nfe_os(None, "OS-2026-000042", 1))

    item = previa.itens[0]
    assert (item.nome, item.cfop, item.ncm, item.cst_csosn) == ("Filtro de oleo", "5101", "84212300", "102")
    assert item.valor_total == 3000
    assert previa.totais.valor_nota == 3000
    assert previa.destinatario.documento == "11144477735"
    assert previa.formas_pagamento[0].valor == 3000
    assert previa.grupos_cfop[0].cfop_sugerido == "5102"
