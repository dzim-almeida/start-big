# ---------------------------------------------------------------------------
# ARQUIVO: app/services/compras/previsoes.py
# DESCRIÇÃO: O que os pedidos em aberto vão custar, e quando (Compras, fase 5).
# ---------------------------------------------------------------------------
"""
Um pedido ENVIADO ainda não é conta a pagar (a conta nasce no recebimento,
D8), mas já é dinheiro comprometido. O Fluxo de Caixa (Financeiro PRO) mostra
estas previsões na régua, marcadas como "previsto · pedido", para o dono não
ler sobra onde já há compromisso (D8d).

A conta, por pedido ENVIADO/PARCIAL:
- valor previsto = o que FALTA chegar (pendente × custo combinado) + a parte
  proporcional do frete − desconto;
- dividido nas parcelas combinadas (sem parcelas: à vista);
- cada parcela vence `dias` depois da previsão de entrega — ou de hoje, se a
  previsão já passou ou não foi dada (atrasado continua sendo compromisso).

Só com o módulo COMPRAS: sem ele, nenhum pedido existe para prever, e a
função devolve vazio sem nem consultar.
"""

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.pedido_compra import PedidoCompra, SituacaoPedido
from app.services.compras.recebimentos import proporcional


@dataclass(frozen=True)
class PrevisaoPagamento:
    data: date
    valor: int
    descricao: str
    pedido_id: int


def previsoes_de_pagamento(db: Session, empresa_id: int, inicio: date, fim: date) -> list[PrevisaoPagamento]:
    from app.services.compras.nota_pedido import modulo_compras_ativo

    if not modulo_compras_ativo(db):
        return []

    pedidos = db.scalars(
        select(PedidoCompra)
        .options(selectinload(PedidoCompra.itens), selectinload(PedidoCompra.parcelas))
        .where(PedidoCompra.empresa_id == empresa_id, PedidoCompra.situacao.in_(SituacaoPedido.EM_ABERTO))
    ).all()

    saida: list[PrevisaoPagamento] = []
    for pedido in pedidos:
        falta = sum(i.pendente * i.custo_unitario for i in pedido.itens)
        if falta <= 0:
            continue
        ajuste = (pedido.frete - pedido.desconto) * falta // pedido.valor_itens if pedido.valor_itens else 0
        total = max(falta + ajuste, 0)
        parcelas = list(pedido.parcelas)
        prazos = [p.dias for p in parcelas] or [0]
        valores = proporcional(total, [p.valor for p in parcelas] or [1])
        base = max(pedido.previsao_entrega or inicio, inicio)
        n = len(valores)
        for numero, (dias, valor) in enumerate(zip(prazos, valores), start=1):
            vence = base + timedelta(days=dias)
            if valor <= 0 or not (inicio <= vence <= fim):
                continue
            parte = f" ({numero}/{n})" if n > 1 else ""
            saida.append(PrevisaoPagamento(
                data=vence,
                valor=valor,
                descricao=f"Pedido {pedido.codigo} — {pedido.fornecedor_nome}{parte}",
                pedido_id=pedido.id,
            ))
    return saida
