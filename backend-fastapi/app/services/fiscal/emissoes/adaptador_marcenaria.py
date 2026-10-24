# ---------------------------------------------------------------------------
# ARQUIVO: services/fiscal/emissoes/adaptador_marcenaria.py
# DESCRIÇÃO: Uma entrega da marcenaria com a forma de uma Venda, para o motor
#            fiscal (docs/marcenaria-faturamento-plano.md, F3).
# ---------------------------------------------------------------------------
"""
Mesma ideia do `adaptador_os.py` (uma implementação só do motor fiscal), mas
com outro recorte, porque na OS da marcenaria o móvel é SERVICO (decisão C5:
a comissão sai da margem dos itens de serviço) e os insumos são PRODUTO a
R$ 0 (F2b). Pelo recorte da OS comum, a nota sairia só com as chapas a zero.

O QUE ENTRA NESTA NF-e: os MÓVEIS escolhidos (os de uma entrega), cada um como
o seu produto acabado, com o nome do móvel na descrição. Os insumos ficam de
fora (já entraram no móvel). A OS não muda: o móvel continua SERVICO nela.

O RESTO DA OS ENTRA PELA FATIA (D8). A OS pode virar várias notas (uma por
entrega), então desconto, acréscimo, taxa de entrega e a instalação embutida
são divididos pelo valor dos móveis, de forma ACUMULADA:

    fatia = round(T × (antes + nesta) / base) − round(T × antes / base)

`antes` = valor dos móveis já faturados, `nesta` = os desta nota, `base` = todos
os móveis aprovados. Somadas as notas, cada total T fecha ao centavo.

- Instalação EMBUTIDA vai como acréscimo (vira `vOutro` no resolver, como o
  acréscimo da venda): é acessória à venda do móvel (D6). FORA: não entra.
- Pagamentos (Rejeição 767): o que já foi pago na OS entra pela proporção da
  nota; o que falta receber vai como forma "99" -- o mesmo código que o sistema
  já manda para forma sem código SEFAZ. A CONFIRMAR com o contador (D11).
"""

from dataclasses import dataclass
from typing import Optional

from app.services.fiscal.emissoes.adaptador_os import PagamentoOSComoPagamentoVenda, _ratear

INSTALACAO_EMBUTIDA = "EMBUTIDA"
CODIGO_A_RECEBER = "99"

# O papel da nota (`documento_fiscal.papel`), um por modo (D7):
VENDA = "VENDA_MARCENARIA"                     # NOTA_NA_ENTREGA: 5101/5102 a cada entrega
SIMPLES_FATURAMENTO = "SIMPLES_FATURAMENTO"    # ENTREGA_FUTURA, no fechamento: 5922
REMESSA = "REMESSA_ENTREGA_FUTURA"             # ENTREGA_FUTURA, a cada entrega: 5116/5117

NATUREZA = {
    VENDA: "Venda de Mercadoria",
    SIMPLES_FATURAMENTO: "Simples faturamento - venda para entrega futura",
    REMESSA: "Venda para entrega futura - remessa",
}


class _NotaDaEntrega:
    """O cabecalho que o builder le de `nota_fiscal`, com a natureza do papel.

    Finalidade, consumidor final e presenca vem da nota da OS (quando a loja
    preencheu); senao, os padroes do builder.
    """

    def __init__(self, nota_da_os, papel: str):
        self.natureza_operacao = NATUREZA[papel]
        self.finalidade_emissao = getattr(nota_da_os, "finalidade_emissao", None) or 1
        consumidor = getattr(nota_da_os, "consumidor_final", None)
        self.consumidor_final = True if consumidor is None else consumidor
        self.indicador_presenca = getattr(nota_da_os, "indicador_presenca", None) or 1


def fatia_acumulada(total: int, antes: int, nesta: int, base: int) -> int:
    """A parte de `total` que cabe a esta nota (ver o cabeçalho)."""
    if total <= 0 or base <= 0 or nesta <= 0:
        return 0
    return round(total * (antes + nesta) / base) - round(total * antes / base)


@dataclass
class MovelParaNota:
    """Um móvel escolhido para a nota: o item da OS e o produto acabado dele."""
    item_os: object              # OrdemServicoItem do móvel (valor de venda)
    produto: object              # Produto acabado (com o cadastro fiscal)
    quantidade: float
    terceirizado: bool


class ItemMovelComoItemVenda:
    """Um móvel falando o vocabulário de `ProdutoVenda` (o que o motor lê)."""

    __slots__ = (
        "produto", "produto_id", "quantidade", "valor_unitario", "subtotal",
        "desconto", "descricao_avulsa", "descricao_nota", "item_os", "terceirizado",
        "cfop_sufixo_forcado", "icms_sem_destaque",
    )

    def __init__(self, movel: MovelParaNota, desconto: int, papel: str = VENDA):
        self.item_os = movel.item_os
        self.produto = movel.produto
        self.produto_id = movel.produto.id
        self.quantidade = movel.quantidade
        self.valor_unitario = movel.item_os.valor_unitario
        self.subtotal = movel.item_os.valor_total
        self.desconto = desconto
        # A descrição da nota é o nome do móvel ("Torre Quente — Cozinha"), não
        # o do produto genérico ("Móvel planejado"): é o que o cliente comprou.
        self.descricao_avulsa = movel.item_os.nome
        self.descricao_nota = movel.item_os.nome
        self.terceirizado = movel.terceirizado
        # Entrega futura (F4): a operacao manda no CFOP. Venda: o do cadastro.
        if papel == SIMPLES_FATURAMENTO:
            self.cfop_sufixo_forcado = "922"
        elif papel == REMESSA:
            self.cfop_sufixo_forcado = "117" if movel.terceirizado else "116"
        else:
            self.cfop_sufixo_forcado = None
        self.icms_sem_destaque = papel == SIMPLES_FATURAMENTO


class _FormaAReceber:
    """Forma de pagamento do que ainda não foi pago na OS (D11)."""
    codigo_sefaz = CODIGO_A_RECEBER
    tipo_integracao = None
    nome = "A receber"


class _PagamentoAReceber:
    __slots__ = ("forma_pagamento", "valor")

    def __init__(self, valor: int):
        self.forma_pagamento = _FormaAReceber()
        self.valor = valor


class EntregaComoVenda:
    """A entrega (os móveis escolhidos) com a superfície que o motor espera de uma Venda."""

    def __init__(self, os_obj, moveis: list[MovelParaNota], valor_moveis_total: int,
                 valor_moveis_ja_faturados: int, instalacao_valor: int, instalacao_modo: str,
                 papel: str = VENDA, chaves_referenciadas: Optional[list[str]] = None):
        self.os = os_obj
        self.papel = papel
        nesta = sum(m.item_os.valor_total for m in moveis)
        base = valor_moveis_total
        antes = valor_moveis_ja_faturados

        def fatia(total: int) -> int:
            return fatia_acumulada(int(total or 0), antes, nesta, base)

        embutida = instalacao_modo == INSTALACAO_EMBUTIDA
        # O desconto e o acréscimo da OS são do que ela cobra (móveis + instalação):
        # a nota leva a parte do ESCOPO dela (sem a instalação, se ela fica fora).
        bruto = os_obj.valor_bruto or 0
        escopo = base + (instalacao_valor if embutida else 0)
        desconto_escopo = round((os_obj.desconto or 0) * escopo / bruto) if bruto > 0 else 0
        acrescimo_escopo = round((os_obj.acrescimo or 0) * escopo / bruto) if bruto > 0 else 0

        descontos = _ratear(fatia(desconto_escopo), [m.item_os for m in moveis])
        self.itens = [ItemMovelComoItemVenda(m, d, papel) for m, d in zip(moveis, descontos)]

        # Taxa de entrega: é frete da mercadoria, inteira dos móveis.
        self.entrega = fatia(os_obj.taxa_entrega or 0)
        self.acrescimo = fatia(acrescimo_escopo) + (fatia(instalacao_valor) if embutida else 0)
        self.total = nesta - sum(descontos) + self.entrega + self.acrescimo
        self.troco = 0

        # Remessa: o pagamento ja esta na nota de simples faturamento ("90").
        self.sem_pagamento = papel == REMESSA
        self.pagamentos = [] if self.sem_pagamento else _pagamentos_da_nota(os_obj, self.total)
        self.chaves_referenciadas = list(chaves_referenciadas or [])
        self.cliente = getattr(os_obj.objeto, "cliente", None) if os_obj.objeto else None
        self.nota_fiscal = _NotaDaEntrega(os_obj.nota_fiscal, papel)
        self.numero_venda = os_obj.numero_os


def _pagamentos_da_nota(os_obj, total_nota: int) -> list:
    """O que já foi pago na OS, pela proporção desta nota, e o resto "a receber".

    A soma é exatamente o total da nota (Rejeição 767). As formas que o cliente
    usou continuam as dele; a sobra de arredondamento vai para o maior pagamento.
    """
    if total_nota <= 0:
        return []
    pagamentos = [p for p in (os_obj.pagamentos or []) if p.forma_pagamento and (p.valor or 0) > 0]
    pago = sum(p.valor for p in pagamentos)
    valor_os = os_obj.valor_total or 0
    pago_nesta = min(total_nota, round(pago * total_nota / valor_os)) if valor_os > 0 else 0

    resultado = []
    if pago_nesta > 0:
        valores = [round(pago_nesta * p.valor / pago) for p in pagamentos]
        sobra = pago_nesta - sum(valores)
        if sobra:
            maior = max(range(len(pagamentos)), key=lambda k: pagamentos[k].valor)
            valores[maior] += sobra
        resultado = [PagamentoOSComoPagamentoVenda(p, v) for p, v in zip(pagamentos, valores) if v > 0]
    falta = total_nota - sum(p.valor for p in resultado)
    if falta > 0:
        resultado.append(_PagamentoAReceber(falta))
    return resultado


def adaptar_entrega(os_obj, moveis: list[MovelParaNota], *, valor_moveis_total: int,
                    valor_moveis_ja_faturados: int, instalacao_valor: int = 0,
                    instalacao_modo: str = INSTALACAO_EMBUTIDA, papel: str = VENDA,
                    chaves_referenciadas: Optional[list[str]] = None) -> EntregaComoVenda:
    """Ponto de entrada -- a entrega (ou o simples faturamento) vista como venda."""
    return EntregaComoVenda(os_obj, moveis, valor_moveis_total, valor_moveis_ja_faturados,
                            instalacao_valor, instalacao_modo, papel, chaves_referenciadas)
