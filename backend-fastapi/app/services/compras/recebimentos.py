# ---------------------------------------------------------------------------
# ARQUIVO: app/services/compras/recebimentos.py
# MÓDULO: Service — Recebimento do pedido de compra (Compras, fase 3)
# ---------------------------------------------------------------------------
"""
A mercadoria chegou. Numa transação só:

1. ESTOQUE: cada item vira uma ENTRADA no livro (origem COMPRA), pelo MESMO
   `registrar_movimentacao` da entrada manual e da XML — com o custo REAL por
   unidade, que recalcula o custo médio. Um caminho só para custo.
2. PEDIDO: soma o recebido em cada item; se não falta nada, RECEBIDO; senão,
   PARCIAL. "Encerrar saldo" cancela o que não chegou (o fornecedor avisou que
   não vem) e fecha o pedido (D5).
3. ÚLTIMO PREÇO do fornecedor (`produto_fornecedores`), como a XML faz.
4. CONTAS A PAGAR (D8), só com o Financeiro: as parcelas COMBINADAS no
   pedido, proporcionais ao que chegou, com vencimento contado de hoje.
5. HISTÓRICO do pedido.

VALOR DE CADA CHEGADA = itens recebidos (custo real) + a parte do frete −
desconto do pedido que cabe a ela, proporcional ao valor PEDIDO desses itens.
A chegada que completa o pedido leva o resto do ajuste: a soma das chegadas
fecha o frete e o desconto ao centavo, sem sobra de arredondamento.

Quem só RECEBE (o almoxarife) confere quantidade: o custo real que ele mandar
é ignorado e vale o do pedido (D14).
"""

from datetime import date, datetime, timedelta
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enum import ContaPagarStatus, MovimentacaoOrigem, MovimentacaoTipo
from app.db.models.conta_pagar import ContaPagar
from app.db.models.pedido_compra import PedidoCompra, SituacaoPedido
from app.db.models.produto import Produto
from app.db.models.recebimento_compra import RecebimentoCompra, RecebimentoCompraItem
from app.schemas.compras import PedidoRead, RecebimentoEscrita
from app.services.compras import fornecedores_produto
from app.services.compras import pedidos as pedidos_service


def _erro(codigo: int, detalhe: str) -> HTTPException:
    return HTTPException(status_code=codigo, detail=detalhe)


def financeiro_disponivel(db: Session) -> bool:
    """Mesma regra da entrada por XML e do `requer_modulo`: não saber libera."""
    from app.services import licenca as licenca_service

    modulos = licenca_service.modulos_da_licenca(db)
    return not modulos or "FINANCEIRO" in modulos


def _custo_por_unidade(custo_compra: int, fator: int) -> int:
    """Centavos por unidade do produto, meio para cima (mesma regra da XML)."""
    return (custo_compra * 2 + fator) // (2 * fator) if fator > 1 else custo_compra


def _proporcional(total: int, pesos: list[int]) -> list[int]:
    """Divide `total` na proporção dos pesos; o resto vai no último (fecha exato).

    Sem peso nenhum (tudo zero), divide em partes iguais.
    """
    if not pesos:
        return []
    soma = sum(pesos)
    if soma <= 0:
        pesos, soma = [1] * len(pesos), len(pesos)
    partes = [total * p // soma for p in pesos]
    partes[-1] += total - sum(partes)
    return partes


def lancar_contas(
    db: Session, token: dict[str, Any], pedido: PedidoCompra, recebimento: RecebimentoCompra
) -> int:
    """As parcelas do pedido, proporcionais a esta chegada (D8)."""
    from app.db.crud import financeiro as financeiro_crud

    parcelas = list(pedido.parcelas) or []
    prazos = [p.dias for p in parcelas] or [0]
    valores = _proporcional(recebimento.valor_total, [p.valor for p in parcelas] or [1])
    total = len(valores)
    hoje = date.today()
    nota = f" — NF {recebimento.numero_nota}" if recebimento.numero_nota else ""
    primeira: Optional[ContaPagar] = None
    lancadas = 0
    for numero, (dias, valor) in enumerate(zip(prazos, valores), start=1):
        if valor <= 0:
            continue
        conta = financeiro_crud.criar_conta_pagar(db, ContaPagar(
            empresa_id=token["empresa_id"],
            descricao=f"Pedido {pedido.codigo} — {pedido.fornecedor_nome}{nota}"[:255],
            valor=valor,
            vencimento=hoje + timedelta(days=dias),
            fornecedor_id=pedido.fornecedor_id,
            recorrente=False,
            status=ContaPagarStatus.PENDENTE.value,
            parcela_numero=numero if total > 1 else None,
            parcela_total=total if total > 1 else None,
            parcelamento_id=(primeira.id if primeira else None) if total > 1 else None,
            recebimento_compra_id=recebimento.id,
            observacao=f"Recebimento do pedido {pedido.codigo}",
        ))
        if primeira is None:
            primeira = conta
            if total > 1:
                conta.parcelamento_id = conta.id
                db.flush()
        lancadas += 1
    return lancadas


def receber(
    db: Session,
    token: dict[str, Any],
    pedido_id: int,
    dados: RecebimentoEscrita,
    ver_custos: bool,
) -> PedidoRead:
    from app.services import movimentacao_estoque as mov_service

    pedido = pedidos_service.carregar(db, token, pedido_id)
    if pedido.situacao not in SituacaoPedido.EM_ABERTO:
        raise _erro(
            status.HTTP_409_CONFLICT,
            f"O pedido {pedido.codigo} está {pedido.situacao.lower()}: só pedido enviado recebe mercadoria.",
        )

    por_id = {i.id: i for i in pedido.itens}
    chegou = [d for d in dados.itens if d.quantidade > 0]
    if not chegou:
        raise _erro(status.HTTP_422_UNPROCESSABLE_ENTITY, "Informe o que chegou (ao menos um item com quantidade).")

    # Valida tudo antes de mexer em qualquer coisa.
    for d in dados.itens:
        item = por_id.get(d.pedido_item_id)
        if item is None:
            raise _erro(status.HTTP_422_UNPROCESSABLE_ENTITY, f"O item {d.pedido_item_id} não é deste pedido.")
        if d.quantidade > item.pendente:
            raise _erro(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"'{item.descricao}': chegaram {d.quantidade} {item.unidade_compra}, mas faltam só "
                f"{item.pendente}. Se o fornecedor mandou a mais, ajuste o pedido antes.",
            )
        if d.quantidade and (item.produto_id is None or db.get(Produto, item.produto_id) is None):
            raise _erro(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"'{item.descricao}': o produto não existe mais no cadastro; não dá para dar entrada.",
            )

    usuario_id, usuario_nome = pedidos_service.usuario_do_token(token)
    numero_nota = (dados.numero_nota or "").strip() or None
    recebimento = RecebimentoCompra(
        empresa_id=token["empresa_id"],
        pedido_id=pedido.id,
        numero_nota=numero_nota,
        observacao=(dados.observacao or "").strip() or None,
        recebido_por_id=usuario_id,
        recebido_por_nome=usuario_nome,
        recebido_em=datetime.now(),
    )
    db.add(recebimento)
    db.flush()

    observacao_mov = f"Pedido {pedido.codigo} — {pedido.fornecedor_nome}"
    if numero_nota:
        observacao_mov += f" (NF {numero_nota})"
    valor_itens = 0
    valor_pedido_desta_chegada = 0
    for d in chegou:
        item = por_id[d.pedido_item_id]
        produto = db.get(Produto, item.produto_id)
        custo_compra = d.custo_unitario if (ver_custos and d.custo_unitario is not None) else item.custo_unitario
        unidades = d.quantidade * item.fator

        movimento = mov_service.registrar_movimentacao(
            db,
            produto=produto,
            tipo=MovimentacaoTipo.ENTRADA,
            quantidade=unidades,
            origem=MovimentacaoOrigem.COMPRA,
            usuario_id=usuario_id,
            usuario_nome=usuario_nome,
            observacao=observacao_mov[:500],
            custo_unitario=_custo_por_unidade(custo_compra, item.fator),
        )
        if movimento is None:
            raise _erro(
                status.HTTP_422_UNPROCESSABLE_ENTITY, f"'{item.descricao}': o produto não controla estoque."
            )
        movimento.recebimento_compra_id = recebimento.id
        if item.embalagem_id is not None:
            movimento.embalagem_id = item.embalagem_id
            movimento.embalagem_sigla = item.unidade_compra[:6]
            movimento.embalagem_fator = item.fator
            movimento.quantidade_embalagem = d.quantidade

        recebimento.itens.append(RecebimentoCompraItem(
            pedido_item_id=item.id,
            produto_id=item.produto_id,
            descricao=item.descricao,
            unidade_compra=item.unidade_compra,
            fator=item.fator,
            quantidade=d.quantidade,
            unidades=float(unidades),
            custo_unitario=custo_compra,
            movimentacao_id=movimento.id,
        ))
        item.quantidade_recebida += d.quantidade
        valor_itens += d.quantidade * custo_compra
        valor_pedido_desta_chegada += d.quantidade * item.custo_unitario

        if pedido.fornecedor_id is not None:
            fornecedores_produto.registrar_compra(
                db,
                produto_id=item.produto_id,
                fornecedor_id=pedido.fornecedor_id,
                custo_total=d.quantidade * custo_compra,
                unidades=unidades,
                fator=item.fator,
                embalagem_id=item.embalagem_id,
                codigo_fornecedor=item.codigo_fornecedor,
                data=date.today(),
            )

    # Frete − desconto: proporcional; a ÚLTIMA chegada leva o resto. Encerrar o
    # saldo também faz desta a última — o frete vem inteiro na nota mesmo
    # quando falta mercadoria, e o desconto combinado não some com o saldo.
    ajuste_total = pedido.frete - pedido.desconto
    completou = all(i.pendente == 0 for i in pedido.itens)
    if completou or dados.encerrar_saldo:
        ja_ajustado = db.scalar(
            select(func.coalesce(func.sum(RecebimentoCompra.valor_ajuste), 0)).where(
                RecebimentoCompra.pedido_id == pedido.id, RecebimentoCompra.id != recebimento.id
            )
        ) or 0
        ajuste = ajuste_total - ja_ajustado
    elif pedido.valor_itens > 0:
        ajuste = ajuste_total * valor_pedido_desta_chegada // pedido.valor_itens
    else:
        ajuste = 0
    recebimento.valor_itens = valor_itens
    recebimento.valor_ajuste = ajuste
    recebimento.valor_total = max(valor_itens + ajuste, 0)

    anterior = pedido.situacao
    if dados.encerrar_saldo and not completou:
        for item in pedido.itens:
            item.quantidade_cancelada += item.pendente
    pedido.situacao = (
        SituacaoPedido.RECEBIDO if all(i.pendente == 0 for i in pedido.itens) else SituacaoPedido.PARCIAL
    )
    db.flush()

    if dados.lancar_contas_pagar and recebimento.valor_total > 0 and financeiro_disponivel(db):
        recebimento.contas_pagar_lancadas = lancar_contas(db, token, pedido, recebimento)

    motivo = f"NF {numero_nota}" if numero_nota else None
    if dados.encerrar_saldo and not completou:
        motivo = ((motivo + " · ") if motivo else "") + "Saldo encerrado: o resto não vem"
    pedidos_service.registrar_log(db, token, pedido, "RECEBIDO", anterior, pedido.situacao, motivo)
    db.flush()
    return pedidos_service.serializar(db, pedido, ver_custos)


def encerrar_saldo(
    db: Session, token: dict[str, Any], pedido_id: int, motivo: str, ver_custos: bool
) -> PedidoRead:
    """O resto de um pedido PARCIAL não vem mais: cancela o saldo e fecha (D5).

    Só PARCIAL: um pedido enviado sem nada recebido se CANCELA (D7), não se
    encerra — o histórico diria "recebido" de algo que nunca chegou.
    """
    pedido = pedidos_service.carregar(db, token, pedido_id)
    if pedido.situacao != SituacaoPedido.PARCIAL:
        raise _erro(
            status.HTTP_409_CONFLICT,
            f"Só pedido recebido em parte tem saldo a encerrar (o {pedido.codigo} está {pedido.situacao.lower()}).",
        )
    for item in pedido.itens:
        item.quantidade_cancelada += item.pendente
    pedido.situacao = SituacaoPedido.RECEBIDO
    pedidos_service.registrar_log(
        db, token, pedido, "SALDO_ENCERRADO", SituacaoPedido.PARCIAL, SituacaoPedido.RECEBIDO, motivo
    )
    db.flush()
    return pedidos_service.serializar(db, pedido, ver_custos)
