# ---------------------------------------------------------------------------
# ARQUIVO: app/services/compras/relatorios.py
# MÓDULO: Service — Relatórios do módulo de Compras (fase 5)
# ---------------------------------------------------------------------------
"""
Duas perguntas que o dono faz ao fornecedor, com número na mão:

1. "Você entrega no prazo?" — por fornecedor: pedidos enviados, quanto foi
   recebido, o PRAZO REAL médio (do envio do pedido à primeira chegada) e
   quantas entregas chegaram até a data prometida.
2. "Você subiu o preço?" — por produto: o custo por unidade na primeira e na
   última chegada do período, e a variação.

A fonte são os RECEBIMENTOS de pedido (manuais e pela XML ligada a pedido):
compra que entrou só pela XML, sem pedido, não tem prazo prometido para medir.
"""

from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.pedido_compra import PedidoCompra
from app.db.models.recebimento_compra import RecebimentoCompra
from app.schemas.compras import RelatorioCompras, RelatorioFornecedor, VariacaoPreco

MAX_VARIACOES = 30


def _limites(inicio: date, fim: date) -> tuple[datetime, datetime]:
    return datetime.combine(inicio, time.min), datetime.combine(fim + timedelta(days=1), time.min)


def gerar(db: Session, token: dict[str, Any], inicio: date, fim: date) -> RelatorioCompras:
    de, ate = _limites(inicio, fim)
    empresa_id = token["empresa_id"]

    enviados = db.scalars(
        select(PedidoCompra).where(
            PedidoCompra.empresa_id == empresa_id,
            PedidoCompra.enviado_em >= de,
            PedidoCompra.enviado_em < ate,
        )
    ).all()
    recebimentos = db.scalars(
        select(RecebimentoCompra)
        .options(selectinload(RecebimentoCompra.itens))
        .where(
            RecebimentoCompra.empresa_id == empresa_id,
            RecebimentoCompra.recebido_em >= de,
            RecebimentoCompra.recebido_em < ate,
        )
        .order_by(RecebimentoCompra.recebido_em, RecebimentoCompra.id)
    ).all()
    pedidos = {p.id: p for p in db.scalars(
        select(PedidoCompra).where(PedidoCompra.id.in_({r.pedido_id for r in recebimentos} or {0}))
    )}

    # --- por fornecedor ---------------------------------------------------------
    linhas: dict[Any, dict] = defaultdict(lambda: {
        "nome": "", "enviados": 0, "recebimentos": 0, "valor": 0,
        "prazos": [], "com_previsao": 0, "no_prazo": 0,
    })
    for p in enviados:
        linha = linhas[p.fornecedor_id]
        linha["nome"] = p.fornecedor_nome
        linha["enviados"] += 1

    primeira_chegada: dict[int, RecebimentoCompra] = {}
    for r in recebimentos:
        pedido = pedidos.get(r.pedido_id)
        if pedido is None:
            continue
        linha = linhas[pedido.fornecedor_id]
        linha["nome"] = pedido.fornecedor_nome
        linha["recebimentos"] += 1
        linha["valor"] += r.valor_total
        primeira_chegada.setdefault(pedido.id, r)

    # Prazo e pontualidade medem a PRIMEIRA chegada de cada pedido: é ela que
    # diz se o fornecedor cumpriu a data; o resto de um parcial é outra história.
    for pedido_id, r in primeira_chegada.items():
        pedido = pedidos[pedido_id]
        linha = linhas[pedido.fornecedor_id]
        if pedido.enviado_em is not None:
            linha["prazos"].append((r.recebido_em.date() - pedido.enviado_em.date()).days)
        if pedido.previsao_entrega is not None:
            linha["com_previsao"] += 1
            if r.recebido_em.date() <= pedido.previsao_entrega:
                linha["no_prazo"] += 1

    por_fornecedor = [
        RelatorioFornecedor(
            fornecedor_id=fornecedor_id,
            fornecedor_nome=dados["nome"] or "Fornecedor removido",
            pedidos_enviados=dados["enviados"],
            recebimentos=dados["recebimentos"],
            valor_recebido=dados["valor"],
            prazo_medio_dias=round(sum(dados["prazos"]) / len(dados["prazos"]), 1) if dados["prazos"] else None,
            entregas_com_previsao=dados["com_previsao"],
            entregas_no_prazo=dados["no_prazo"],
        )
        for fornecedor_id, dados in linhas.items()
    ]
    por_fornecedor.sort(key=lambda f: (-f.valor_recebido, f.fornecedor_nome.lower()))

    # --- variação de preço ----------------------------------------------------------
    historico: dict[int, list[tuple[Decimal, str, str]]] = defaultdict(list)
    for r in recebimentos:
        pedido = pedidos.get(r.pedido_id)
        for item in r.itens:
            if item.produto_id is None or item.custo_unitario <= 0 or item.fator < 1:
                continue
            historico[item.produto_id].append((
                Decimal(item.custo_unitario) / item.fator,
                item.descricao,
                pedido.fornecedor_nome if pedido else "",
            ))

    variacoes = []
    for produto_id, compras in historico.items():
        if len(compras) < 2:
            continue
        primeiro, ultimo = compras[0][0], compras[-1][0]
        if primeiro <= 0:
            continue
        variacoes.append(VariacaoPreco(
            produto_id=produto_id,
            descricao=compras[-1][1],
            fornecedor_nome=compras[-1][2],
            compras=len(compras),
            primeiro_custo_unidade=float(primeiro),
            ultimo_custo_unidade=float(ultimo),
            variacao_bp=int(((ultimo - primeiro) * 10_000 / primeiro).to_integral_value()),
        ))
    variacoes.sort(key=lambda v: -abs(v.variacao_bp))

    return RelatorioCompras(
        inicio=inicio,
        fim=fim,
        pedidos_enviados=len(enviados),
        valor_recebido=sum(r.valor_total for r in recebimentos),
        por_fornecedor=por_fornecedor,
        variacao_precos=variacoes[:MAX_VARIACOES],
    )
