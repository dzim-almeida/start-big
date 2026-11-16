# ---------------------------------------------------------------------------
# ARQUIVO: app/services/marcenaria/terceirizado_situacao.py
# DESCRICAO: A situacao de um movel TERCEIRIZADO (Spec 11A, D1-D3, D8), numa
#            funcao so. Usada pela tela (11A), pelo bloqueio do "desfazer
#            aprovacao" e pela producao (12A: pronto = CONFERIDO).
#
# Modulo pequeno e sem servicos de proposito: o bloqueio do desfazer vive num
# arquivo que o detalhe do orcamento importa, e ele nao pode puxar o resto.
# ---------------------------------------------------------------------------
"""
Um movel terceirizado passa por: A pedir -> Pedido enviado -> Recebido -> Conferido.

De onde vem a situacao (uma fonte para cada fato):
- COM pedido do Compras (nao cancelado): o pedido manda. O Compras sabe se o
  pedido saiu (ENVIADO/PARCIAL) e se chegou (RECEBIDO). "Conferido" e da
  marcenaria (`terc_conferido_em`) e so vale com o pedido RECEBIDO.
- SEM pedido do Compras (ou com o pedido cancelado): a situacao e a GRAVADA
  no movel pelas acoes manuais (`terc_situacao`; nulo = A pedir).
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional

from app.db.models.marcenaria.ambiente import MarcenariaMovel
from app.db.models.pedido_compra import PedidoCompra, SituacaoPedido

# As quatro situacoes (D1). Gravadas como texto no modo manual.
A_PEDIR = "A_PEDIR"
ENVIADO = "ENVIADO"
RECEBIDO = "RECEBIDO"
CONFERIDO = "CONFERIDO"
ORDEM = (A_PEDIR, ENVIADO, RECEBIDO, CONFERIDO)

# Como a situacao entra numa frase ("o movel Torre Quente esta recebido").
NA_FRASE = {A_PEDIR: "a pedir", ENVIADO: "com o pedido enviado", RECEBIDO: "recebido", CONFERIDO: "conferido"}

TERCEIRIZADA = "TERCEIRIZADA"            # `tipo_producao` do movel comprado pronto (06A)


@dataclass(frozen=True)
class SituacaoTerceirizado:
    """O que a tela, o bloqueio e a producao precisam saber de um movel."""
    situacao: str                        # A_PEDIR, ENVIADO, RECEBIDO ou CONFERIDO
    modo: str                            # "COMPRAS" (o pedido manda) ou "MANUAL"
    previsao: Optional[date]             # do pedido do Compras, ou a anotada
    pedido: Optional[PedidoCompra]       # o pedido do Compras que vale (nao cancelado)


def pedido_ativo(pedido: Optional[PedidoCompra]) -> Optional[PedidoCompra]:
    """O pedido do Compras so vale se existir e nao estiver cancelado (D2, D11)."""
    if pedido is None or pedido.situacao == SituacaoPedido.CANCELADO:
        return None
    return pedido


def situacao_do_movel(movel: MarcenariaMovel, pedido: Optional[PedidoCompra]) -> SituacaoTerceirizado:
    """D2/D3: deriva a situacao de um movel terceirizado.

    `pedido` = o `PedidoCompra` de `movel.pedido_compra_id` (ou None); quem
    chama le do banco, para listas inteiras numa consulta so.
    """
    ativo = pedido_ativo(pedido)
    if ativo is not None:
        if ativo.situacao == SituacaoPedido.RASCUNHO:
            situacao = A_PEDIR                       # o pedido existe, mas ainda nao saiu (selo "rascunho")
        elif ativo.situacao in SituacaoPedido.EM_ABERTO:
            situacao = ENVIADO                       # ENVIADO ou PARCIAL: a central esta fazendo
        else:                                        # RECEBIDO: chegou; conferir e da marcenaria
            situacao = CONFERIDO if movel.terc_conferido_em else RECEBIDO
        return SituacaoTerceirizado(situacao, "COMPRAS", ativo.previsao_entrega, ativo)
    situacao = movel.terc_situacao if movel.terc_situacao in ORDEM else A_PEDIR
    return SituacaoTerceirizado(situacao, "MANUAL", movel.terc_previsao, None)


def atrasado(situacao: SituacaoTerceirizado, hoje: date) -> bool:
    """D8: pedido enviado com a previsao ja vencida (o compromisso da central)."""
    return situacao.situacao == ENVIADO and situacao.previsao is not None and situacao.previsao < hoje
