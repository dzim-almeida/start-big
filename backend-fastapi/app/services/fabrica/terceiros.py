# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fabrica/terceiros.py
# DESCRIÇÃO: Móvel terceirizado = pedido de SERVIÇO à central de corte
#            (docs/marcenaria-fabrica-plano.md, F5; RC15/RC16, D8).
# ---------------------------------------------------------------------------
"""
O pedido é o pedido de Compras de sempre, com `tipo = SERVICO` (existe desde a
fase 2 de Compras) e um item sem produto: o serviço não entra no estoque. Daí
para frente é o fluxo de Compras — enviar (WhatsApp), receber (gera as contas
a pagar), cancelar. O que a fábrica ganha:

- o pedido fica ligado ao MÓVEL (`fabrica_moveis.pedido_compra_id`);
- a etapa "Separação e compra" só sai com o serviço RECEBIDO (trilho.py);
- o custo real do móvel é o valor recebido (separacao.margem).

Exige o módulo COMPRAS na licença (a rota confere): sem Compras não há pedido.
"""

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.fabrica_orcamento import EventoFase, SituacaoOrcamento
from app.db.models.pedido_compra import PedidoCompra, PedidoCompraItem, SituacaoPedido, TipoPedido
from app.schemas.fabrica import PedidoServicoEscrita, PedidoServicoRead
from app.services.compras import pedidos as pedidos_service
from app.services.fabrica import trilho
from app.services.fabrica.separacao import movel_da_os

UNIDADE_SERVICO = "SV"


def _erro(codigo: int, detalhe: str) -> HTTPException:
    return HTTPException(status_code=codigo, detail=detalhe)


def criar_pedido(db: Session, token: dict[str, Any], movel_id: int, dados: PedidoServicoEscrita) -> PedidoServicoRead:
    movel, os_ = movel_da_os(db, movel_id)
    if os_ is None or os_.fase_fabrica is None:
        raise _erro(status.HTTP_404_NOT_FOUND, "Móvel não encontrado.")
    trilho._os_aberta(db, os_.numero_os)
    if movel.ambiente.orcamento.situacao != SituacaoOrcamento.APROVADO:
        raise _erro(status.HTTP_409_CONFLICT, "Só móvel da versão APROVADA do orçamento vai para a central de corte.")
    if not movel.terceirizado:
        raise _erro(status.HTTP_409_CONFLICT, "Este móvel não está marcado como terceirizado no orçamento.")
    if movel.pedido_compra_id is not None:
        atual = db.get(PedidoCompra, movel.pedido_compra_id)
        if atual is not None and atual.situacao != SituacaoPedido.CANCELADO:
            raise _erro(status.HTTP_409_CONFLICT, f"Este móvel já tem o pedido {atual.codigo}.")

    fornecedor = pedidos_service.validar_fornecedor(db, dados.fornecedor_id)
    pedido = pedidos_service.novo_rascunho(db, token, fornecedor)
    pedido.tipo = TipoPedido.SERVICO
    pedido.previsao_entrega = dados.previsao_entrega
    pedido.condicao_pagamento = (dados.condicao_pagamento or "").strip() or None
    pedido.observacao = (dados.observacao or "").strip() or None
    descricao = f"Serviço: {movel.ambiente.nome} — {movel.nome}"
    if movel.medidas:
        descricao += f" ({movel.medidas})"
    pedido.itens.append(PedidoCompraItem(
        produto_id=None,
        descricao=f"{descricao} · {os_.numero_os}"[:255],
        unidade_compra=UNIDADE_SERVICO,
        fator=1,
        quantidade=1,
        custo_unitario=dados.valor,
    ))
    pedidos_service._recalcular(pedido)
    pedidos_service._definir_parcelas(pedido, None)
    db.flush()
    pedidos_service.registrar_log(db, token, pedido, "CRIADO", None, SituacaoPedido.RASCUNHO,
                                  f"Central de corte da OS {os_.numero_os}")
    movel.pedido_compra_id = pedido.id
    trilho.registrar(db, os_, EventoFase.AVANCO, token.get("nome") or "Sistema",
                     f"Pedido {pedido.codigo} à central de corte: {movel.nome}")
    db.flush()
    return PedidoServicoRead(
        movel_id=movel.id, pedido_compra_id=pedido.id, codigo=pedido.codigo, situacao=pedido.situacao,
        fornecedor_nome=pedido.fornecedor_nome, valor_total=pedido.valor_total,
    )


def pendencias(db: Session, os_) -> list[str]:
    """Móveis terceirizados da versão aprovada cujo serviço ainda não chegou."""
    orc = trilho.orcamento_aprovado(db, os_.id)
    if orc is None:
        return []
    faltando = []
    for amb in orc.ambientes:
        for mov in amb.moveis:
            if not mov.terceirizado:
                continue
            pedido = db.get(PedidoCompra, mov.pedido_compra_id) if mov.pedido_compra_id else None
            if pedido is None or pedido.situacao == SituacaoPedido.CANCELADO:
                faltando.append(f"{mov.nome} (sem pedido à central de corte)")
            elif pedido.situacao != SituacaoPedido.RECEBIDO:
                faltando.append(f"{mov.nome} ({pedido.codigo} {pedido.situacao.lower()})")
    return faltando
