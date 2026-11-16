# ---------------------------------------------------------------------------
# ARQUIVO: test_payload_fotografias_os.py
# DESCRIÇÃO: Fotografias do payload da NF-e de ORDEM DE SERVIÇO (F0 do plano
#            docs/marcenaria-faturamento-plano.md).
#
# POR QUE ISTO EXISTE
# -------------------
# O faturamento da marcenaria mexe no caminho da NF-e da OS: o adaptador
# (`adaptador_os.py`), a emissão (`nfe_os.py`) e a descrição do item
# (`payload/itens.py`). A regra R1 do plano diz que a nota da informática, da
# oficina e da serigrafia NÃO pode mudar um byte. Estas fotografias travam a
# saída de HOJE, montada pelo mesmo caminho da emissão: OS -> adaptar() ->
# tax engine -> montar_payload_nfe().
#
# Mudou o payload DE PROPÓSITO? Regere e revise o diff dos .json no commit:
#     REGERAR_PAYLOAD=1 pytest test/services/fiscal/test_payload_fotografias_os.py
# ---------------------------------------------------------------------------

from app.core.enum import OrdemServicoItemAprovacao, OrdemServicoItemTipo
from app.db.models.cliente import ClientePF
from app.services.fiscal.emissoes.adaptador_os import adaptar
from app.services.fiscal.payload.builder import montar_payload_nfe

from test.services.fiscal.test_payload_builder import (
    _calcular,
    _empresa,
    _endereco_empresa,
    _fiscal_settings,
    _pagamento,
    _produto,
)
from test.services.fiscal.test_payload_fotografias import _fotografar

PRODUTO = OrdemServicoItemTipo.PRODUTO
SERVICO = OrdemServicoItemTipo.SERVICO


class _ItemOS:
    """Item da OS com os atributos que o adaptador lê."""

    def __init__(self, tipo, nome, quantidade, valor_unitario, produto=None,
                 visivel_cliente=True, origem=None):
        self.tipo = tipo
        self.nome = nome
        self.quantidade = quantidade
        self.valor_unitario = valor_unitario
        self.valor_total = round(quantidade * valor_unitario)
        self.status_aprovacao = OrdemServicoItemAprovacao.APROVADO
        self.produtos = produto
        self.produto_id = getattr(produto, "id", None)
        self.visivel_cliente = visivel_cliente
        self.origem = origem


class _Objeto:
    def __init__(self, cliente):
        self.cliente = cliente


class _OS:
    def __init__(self, itens, pagamentos, desconto=0, cliente=None):
        self.id = 42
        self.numero_os = "OS-2026-000042"
        self.itens = itens
        self.pagamentos = pagamentos
        self.desconto = desconto
        self.taxa_entrega = 0
        self.acrescimo = 0
        self.valor_bruto = sum(i.valor_total for i in itens)
        self.valor_total = self.valor_bruto - desconto
        self.objeto = _Objeto(cliente)
        self.nota_fiscal = None


def _cliente():
    return ClientePF(id=10, nome="Cliente Teste", cpf="52998224725")


def _payload_da_os(os_obj, simples=False):
    """O mesmo caminho da emissão real: adaptar -> calcular -> montar."""
    os_como_venda = adaptar(os_obj)
    return montar_payload_nfe(
        empresa=_empresa("Simples Nacional" if simples else "Lucro Presumido"),
        endereco_empresa=_endereco_empresa(),
        fiscal_settings=_fiscal_settings(),
        venda=os_como_venda,
        nota_fiscal=None,
        resultado_calculo=_calcular(os_como_venda, simples),
    )


def test_fotografia_os_informatica_peca_mao_de_obra_e_desconto():
    """Informática: 2 telas + mão de obra, desconto na OS, pago em PIX e dinheiro.

    A mão de obra fica fora da nota; o desconto entra pela fatia das peças e os
    pagamentos são reduzidos à mesma fatia (Rejeição 767).
    """
    os_obj = _OS(
        [
            _ItemOS(PRODUTO, "Tela 15,6", 2, 15000, produto=_produto(1, "Tela 15,6 LED")),
            _ItemOS(SERVICO, "Mão de obra", 1, 8000),
        ],
        [_pagamento(20000, codigo_sefaz="17", nome="PIX"), _pagamento(15000)],
        desconto=3000,
        cliente=_cliente(),
    )

    payload = _payload_da_os(os_obj)

    assert [i["descricao"] for i in payload["items"]] == ["Tela 15,6 LED"]
    _fotografar("nfe-os-informatica.json", payload)


def test_fotografia_os_serigrafia_fracionada_no_simples():
    """Serigrafia: 2,5 kg de tinta (quantidade fracionada) no Simples Nacional."""
    tinta = _produto(2, "Tinta Plastisol Branca", codigo_barras=None)
    tinta.unidade_medida = "KG"
    tinta.fiscal.csosn = "102"
    os_obj = _OS(
        [
            _ItemOS(PRODUTO, "Tinta", 2.5, 4000, produto=tinta),
            _ItemOS(SERVICO, "Estampa", 1, 12000),
        ],
        [_pagamento(22000)],
        cliente=_cliente(),
    )

    payload = _payload_da_os(os_obj, simples=True)

    assert payload["items"][0]["quantidade_comercial"] == 2.5
    _fotografar("nfe-os-serigrafia-fracionada.json", payload)


def test_marcenaria_hoje_a_nota_sai_so_com_os_insumos_a_zero():
    """O defeito que o plano corrige (docs/marcenaria-faturamento-plano.md §0).

    Na OS da marcenaria o móvel e a instalação são SERVICO (C5) e os insumos
    embutidos são PRODUTO a R$ 0 (F2b). Pelo caminho de hoje, a NF-e não leva
    nenhum móvel: só as chapas, a zero. Este teste registra o comportamento
    ANTIGO; quando o faturamento da marcenaria entrar (F3), ele passa a afirmar
    que essa nota não sai mais.
    """
    chapa = _produto(3, "Chapa MDF 18mm Branco", codigo_barras=None)
    os_obj = _OS(
        [
            _ItemOS(SERVICO, "Armário aéreo — Cozinha", 1, 800000, origem="ORCAMENTO_MARCENARIA"),
            _ItemOS(SERVICO, "Instalação", 1, 50000, origem="ORCAMENTO_MARCENARIA"),
            _ItemOS(PRODUTO, "Chapa MDF 18mm Branco", 3, 0, produto=chapa,
                    visivel_cliente=False, origem="ORCAMENTO_MARCENARIA"),
        ],
        [_pagamento(850000)],
        cliente=_cliente(),
    )

    payload = _payload_da_os(os_obj)

    assert [i["descricao"] for i in payload["items"]] == ["Chapa MDF 18mm Branco"]
    assert payload["totais"]["valor_total"] == 0
