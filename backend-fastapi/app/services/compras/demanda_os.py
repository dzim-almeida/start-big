# ---------------------------------------------------------------------------
# ARQUIVO: app/services/compras/demanda_os.py
# DESCRIÇÃO: O que as OS abertas já comprometeram do estoque (Compras, fase 6).
# ---------------------------------------------------------------------------
"""
A OS só dá baixa no estoque quando FECHA (services/ordem_servico.py,
`_movimentar_estoque_os`). Até lá, a peça aprovada continua na prateleira —
mas já tem dono. É a "reserva" do resumo da marcenaria (RC03), só que
CALCULADA, sem tabela nem lançamento novo: nada muda no PDV nem no livro.

Regra idêntica à da baixa (`_itens_de_produto`), para as duas nunca
divergirem: item de PRODUTO, com produto do catálogo, APROVADO e com
quantidade, em OS ativa que ainda não fechou (FINALIZADA já baixou; CANCELADA
não vai consumir).

Serve a todo segmento com OS: a peça da oficina, o display da assistência, a
chapa da marcenaria.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enum import OrdemServicoItemAprovacao, OrdemServicoItemTipo, OrdemServicoStatus
from app.db.models.ordem_servico import OrdemServico
from app.db.models.ordem_servico_item import OrdemServicoItem
from app.db.models.pedido_compra import (
    OrigemDemanda,
    PedidoCompra,
    PedidoCompraItem,
    PedidoCompraOrigem,
    SituacaoPedido,
)
from app.db.models.produto import Produto
from app.schemas.compras import CompraDaOSItem, ComprasDaOS, PedidoDaOS
from app.services.fabrica.trilho import pode_comprar

STATUS_QUE_JA_NAO_RESERVAM = (OrdemServicoStatus.FINALIZADA, OrdemServicoStatus.CANCELADA)


@dataclass(frozen=True)
class DemandaOS:
    os_id: int
    numero_os: str
    quantidade: float
    data_previsao: Optional[date]
    aberta_em: datetime
    # Marcenaria-fábrica (F3). Nas outras OS: sem instalação e sempre compra.
    data_instalacao: Optional[date] = None
    # RC04: OS da fábrica sem sinal (nem liberação) RESERVA, mas não vira
    # necessidade de compra.
    pode_comprar: bool = True

    @property
    def na_fila(self) -> datetime:
        """Quem é atendido primeiro: quem INSTALA primeiro; sem data, quem abriu primeiro."""
        if self.data_instalacao is not None:
            return datetime.combine(self.data_instalacao, datetime.min.time())
        return self.aberta_em


def demandas_por_produto(db: Session, produto_ids: Optional[list[int]] = None) -> dict[int, list[DemandaOS]]:
    """Por produto, as OS abertas que o usam — a mais ANTIGA primeiro.

    A ordem importa: o estoque e as compras atendem primeiro quem chegou
    primeiro (a fila do balcão). Na OS da fábrica com data de instalação, é
    ela que conta (RC12): quem instala antes pega primeiro. Sem data nenhuma
    marcada, a ordem é a de sempre.
    """
    consulta = (
        select(
            OrdemServicoItem.produto_id,
            # O que a separação já tirou do estoque não está mais reservado:
            # já saiu (F4). Nulo fora da fábrica = a conta de sempre.
            OrdemServicoItem.quantidade - func.coalesce(OrdemServicoItem.quantidade_separada, 0),
            OrdemServico.id,
            OrdemServico.numero_os,
            OrdemServico.data_previsao,
            OrdemServico.data_criacao,
            OrdemServico.data_instalacao,
            OrdemServico.fase_fabrica,
            OrdemServico.compra_liberada_em,
        )
        .join(OrdemServico, OrdemServico.id == OrdemServicoItem.ordem_servico_id)
        .where(
            OrdemServico.ativo.is_(True),
            OrdemServico.status.not_in(STATUS_QUE_JA_NAO_RESERVAM),
            OrdemServicoItem.tipo == OrdemServicoItemTipo.PRODUTO,
            OrdemServicoItem.produto_id.is_not(None),
            OrdemServicoItem.status_aprovacao == OrdemServicoItemAprovacao.APROVADO,
            OrdemServicoItem.quantidade - func.coalesce(OrdemServicoItem.quantidade_separada, 0) > 0,
        )
        .order_by(OrdemServico.data_criacao, OrdemServico.id)
    )
    if produto_ids is not None:
        consulta = consulta.where(OrdemServicoItem.produto_id.in_(produto_ids or [0]))

    # A mesma peça em duas linhas da mesma OS soma numa demanda só.
    acumulado: dict[tuple[int, int], dict] = {}
    for produto_id, quantidade, os_id, numero, previsao, criada, instalacao, fase, liberada in db.execute(consulta):
        chave = (produto_id, os_id)
        if chave not in acumulado:
            acumulado[chave] = {
                "numero": numero, "qtd": 0.0, "previsao": previsao.date() if previsao else None, "criada": criada,
                "instalacao": instalacao, "pode_comprar": pode_comprar(fase, liberada),
            }
        acumulado[chave]["qtd"] += float(quantidade or 0)

    saida: dict[int, list[DemandaOS]] = defaultdict(list)
    for (produto_id, os_id), d in acumulado.items():
        saida[produto_id].append(DemandaOS(
            os_id, d["numero"], d["qtd"], d["previsao"], d["criada"],
            data_instalacao=d["instalacao"], pode_comprar=d["pode_comprar"],
        ))
    for lista in saida.values():
        lista.sort(key=lambda d: (d.na_fila, d.os_id))
    return dict(saida)


def reservado(demandas: list[DemandaOS]) -> float:
    return round(sum(d.quantidade for d in demandas), 3)


def que_compram(demandas: list[DemandaOS]) -> list[DemandaOS]:
    """Só as OS que já podem gerar compra (RC04: fábrica com sinal ou liberação)."""
    return [d for d in demandas if d.pode_comprar]


# ---------------------------------------------------------------------------
# "Compras desta OS" — o painel da OS (fase 6)
# ---------------------------------------------------------------------------

def compras_da_os(db: Session, os_id: int) -> ComprasDaOS:
    """Para cada peça aprovada da OS: quanto o estoque cobre, quanto está em
    pedido ligado a ela, e quanto ainda falta comprar.

    O ESTOQUE é repartido em FILA: as OS mais antigas que usam a mesma peça
    pegam primeiro. Assim duas OS não contam a mesma chapa da prateleira.
    """
    os_ = db.get(OrdemServico, os_id)
    if os_ is None or not os_.ativo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ordem de serviço não encontrada.")
    previsao_os = os_.data_previsao.date() if os_.data_previsao else None
    # RC08: na fábrica, o pedido atrasa se chega depois da INSTALAÇÃO.
    referencia = os_.data_instalacao or previsao_os
    aberta = os_.status not in STATUS_QUE_JA_NAO_RESERVAM
    compra_bloqueada = not pode_comprar(os_.fase_fabrica, os_.compra_liberada_em)
    if not aberta:
        return ComprasDaOS(os_id=os_.id, numero_os=os_.numero_os, aberta=False, data_previsao=previsao_os, itens=[])

    produto_ids = sorted({
        i.produto_id for i in os_.itens
        if i.tipo == OrdemServicoItemTipo.PRODUTO and i.produto_id is not None
        and i.status_aprovacao == OrdemServicoItemAprovacao.APROVADO and (i.quantidade or 0) > 0
    })
    demandas = demandas_por_produto(db, produto_ids)

    ligados = db.execute(
        select(PedidoCompraOrigem.quantidade, PedidoCompraItem, PedidoCompra)
        .join(PedidoCompraItem, PedidoCompraItem.id == PedidoCompraOrigem.pedido_item_id)
        .join(PedidoCompra, PedidoCompra.id == PedidoCompraItem.pedido_id)
        .where(
            PedidoCompraOrigem.origem == OrigemDemanda.OS,
            PedidoCompraOrigem.origem_id == os_.id,
            PedidoCompra.situacao.in_((SituacaoPedido.RASCUNHO, *SituacaoPedido.EM_ABERTO)),
        )
        .order_by(PedidoCompra.id)
    ).all()

    itens = []
    for produto_id in produto_ids:
        fila = demandas.get(produto_id, [])
        minha = next((d for d in fila if d.os_id == os_.id), None)
        if minha is None:
            continue
        produto = db.get(Produto, produto_id)
        saldo = float(produto.estoque.quantidade or 0) if produto and produto.estoque else 0.0
        antes = sum(d.quantidade for d in fila if (d.na_fila, d.os_id) < (minha.na_fila, minha.os_id))
        no_estoque = round(min(minha.quantidade, max(saldo - antes, 0.0)), 3)

        pedidos = []
        em_pedido = 0.0
        for quantidade, item, pedido in ligados:
            if item.produto_id != produto_id:
                continue
            # Parcial: só a parte que ainda não chegou (o que chegou já está no saldo).
            ainda = float(quantidade) * (item.pendente / item.quantidade) if item.quantidade else 0.0
            if pedido.situacao != SituacaoPedido.RASCUNHO:
                em_pedido += ainda
            pedidos.append(PedidoDaOS(
                pedido_id=pedido.id,
                codigo=pedido.codigo,
                situacao=pedido.situacao,
                previsao_entrega=pedido.previsao_entrega,
                quantidade=round(ainda, 3),
                atrasa_os=bool(
                    referencia and pedido.previsao_entrega and pedido.previsao_entrega > referencia
                ),
            ))
        em_pedido = round(em_pedido, 3)
        falta = round(max(minha.quantidade - no_estoque - em_pedido, 0.0), 3)
        if no_estoque >= minha.quantidade:
            situacao = "NO_ESTOQUE"
        elif falta <= 0:
            situacao = "EM_PEDIDO"
        else:
            situacao = "FALTA"
        itens.append(CompraDaOSItem(
            produto_id=produto_id,
            descricao=produto.nome if produto else f"Produto {produto_id}",
            unidade=(produto.unidade_medida if produto else None) or "UN",
            necessario=minha.quantidade,
            no_estoque=no_estoque,
            em_pedido=em_pedido,
            falta=falta,
            situacao=situacao,
            pedidos=pedidos,
        ))
    return ComprasDaOS(
        os_id=os_.id, numero_os=os_.numero_os, aberta=True, data_previsao=previsao_os, itens=itens,
        data_instalacao=os_.data_instalacao, compra_bloqueada=compra_bloqueada,
    )
