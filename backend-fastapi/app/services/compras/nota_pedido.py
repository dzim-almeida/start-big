# ---------------------------------------------------------------------------
# ARQUIVO: app/services/compras/nota_pedido.py
# MÓDULO: Service — A NF-e do fornecedor casada com o pedido (Compras, fase 4)
# ---------------------------------------------------------------------------
"""
A mercadoria chega com a XML. A ENTRADA continua sendo a da XML (services/
nfe_entrada.py, em produção): ela dá entrada no estoque com o custo da nota,
lembra o De-Para e o último preço. Este arquivo só faz o que é do pedido:

1. `pedidos_abertos` — na prévia, os pedidos enviados/parciais do fornecedor
   da nota (só com o módulo COMPRAS; sem ele, a prévia fica como sempre foi).
2. `casar` — item a item: quanto da nota cabe no pedido, o que veio a mais, o
   que não fecha a embalagem, o preço diferente do combinado (D11: AVISA, não
   bloqueia) e o que o pedido tinha e não veio.
3. `receber_pela_nota` — na importação, registra o recebimento no pedido
   (PARCIAL/RECEBIDO), liga as movimentações da XML a ele e, quando a nota NÃO
   traz duplicatas, gera as contas pelas parcelas do pedido. Com duplicatas,
   valem as da nota e as do pedido NÃO nascem — nunca em dobro (D8).

O que entra no estoque é o que a NOTA diz, sempre. O pedido só é conferido.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.pedido_compra import PedidoCompra, PedidoCompraItem, SituacaoPedido
from app.db.models.recebimento_compra import RecebimentoCompra, RecebimentoCompraItem
from app.services.compras import pedidos as pedidos_service
from app.services.compras.recebimentos import financeiro_disponivel, lancar_contas

# Diferença de preço por unidade acima disto vira aviso (D11). Pontos-base.
TOLERANCIA_PRECO_BP = 200


def modulo_compras_ativo(db: Session) -> bool:
    """A licença DIZ que tem COMPRAS. Sem resposta, não tem (D2)."""
    from app.services import licenca as licenca_service

    modulos = licenca_service.modulos_da_licenca(db)
    return bool(modulos) and "COMPRAS" in modulos


def pedidos_abertos(db: Session, empresa_id: int, fornecedor_id: int) -> list[PedidoCompra]:
    """Enviados e recebidos em parte deste fornecedor, o mais recente primeiro."""
    return list(db.scalars(
        select(PedidoCompra)
        .options(selectinload(PedidoCompra.itens), selectinload(PedidoCompra.parcelas))
        .where(
            PedidoCompra.empresa_id == empresa_id,
            PedidoCompra.fornecedor_id == fornecedor_id,
            PedidoCompra.situacao.in_(SituacaoPedido.EM_ABERTO),
        )
        .order_by(PedidoCompra.enviado_em.desc(), PedidoCompra.id.desc())
    ))


@dataclass
class EntradaDaNota:
    """O que a nota trouxe de um produto (somando os itens dela que são ele)."""

    produto_id: int
    unidades: Decimal
    custo_total: int  # centavos, com impostos e frete (D6 da XML)


@dataclass
class LinhaCasada:
    item: PedidoCompraItem
    unidades_nota: Decimal
    quantidade: int          # unidades de compra que entram como recebidas no pedido
    custo_compra: int        # custo REAL por unidade de compra (da nota)
    avisos: list[str] = field(default_factory=list)


@dataclass
class Casamento:
    linhas: list[LinhaCasada]
    fora_do_pedido: list[int]          # produto_id que veio na nota e o pedido não tem
    nao_vieram: list[PedidoCompraItem]  # itens do pedido com saldo que a nota não trouxe

    @property
    def avisos(self) -> list[str]:
        saida = [a for l in self.linhas for a in l.avisos]
        for item in self.nao_vieram:
            saida.append(f"'{item.descricao}': o pedido espera {item.pendente} {item.unidade_compra} e não veio na nota.")
        if self.fora_do_pedido:
            saida.append(f"{len(self.fora_do_pedido)} item(ns) da nota não estão no pedido (entram no estoque assim mesmo).")
        return saida


def _reais(centavos: Decimal) -> str:
    texto = f"{centavos / 100:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _qtd(n: Decimal | float) -> str:
    n = Decimal(str(n))
    return f"{int(n)}" if n == n.to_integral_value() else f"{n.normalize()}".replace(".", ",")


def casar(pedido: PedidoCompra, entradas: list[EntradaDaNota]) -> Casamento:
    """Confere a nota contra o pedido. Não grava nada."""
    por_produto: dict[int, EntradaDaNota] = {}
    for e in entradas:
        atual = por_produto.get(e.produto_id)
        if atual is None:
            por_produto[e.produto_id] = EntradaDaNota(e.produto_id, Decimal(e.unidades), e.custo_total)
        else:
            atual.unidades += Decimal(e.unidades)
            atual.custo_total += e.custo_total

    linhas: list[LinhaCasada] = []
    usados: set[int] = set()
    nao_vieram: list[PedidoCompraItem] = []
    for item in pedido.itens:
        if item.produto_id is None or item.pendente <= 0:
            continue
        entrada = por_produto.get(item.produto_id)
        if entrada is None or entrada.unidades <= 0:
            nao_vieram.append(item)
            continue
        usados.add(item.produto_id)

        em_compra = int(entrada.unidades // item.fator)
        sobra = entrada.unidades - em_compra * item.fator
        quantidade = min(em_compra, item.pendente)
        por_unidade = Decimal(entrada.custo_total) / entrada.unidades
        custo_compra = int((por_unidade * item.fator).to_integral_value(rounding=ROUND_HALF_UP))
        linha = LinhaCasada(item=item, unidades_nota=entrada.unidades, quantidade=quantidade, custo_compra=custo_compra)

        if em_compra > item.pendente:
            linha.avisos.append(
                f"'{item.descricao}': veio a mais — {em_compra} {item.unidade_compra} na nota, o pedido esperava "
                f"{item.pendente}."
            )
        elif em_compra < item.pendente:
            linha.avisos.append(
                f"'{item.descricao}': veio a menos — {em_compra} de {item.pendente} {item.unidade_compra}; "
                "o resto continua esperado."
            )
        if sobra:
            linha.avisos.append(
                f"'{item.descricao}': {_qtd(sobra)} unidade(s) não fecham {item.unidade_compra} com {item.fator} "
                "— entram no estoque, mas não contam no pedido."
            )
        if item.custo_unitario > 0:
            combinado = Decimal(item.custo_unitario) / item.fator
            diferenca_bp = (por_unidade - combinado) * 10_000 / combinado
            if abs(diferenca_bp) > TOLERANCIA_PRECO_BP:
                sentido = "mais caro" if diferenca_bp > 0 else "mais barato"
                percentual = f"{abs(diferenca_bp) / 100:.1f}".replace(".", ",")
                linha.avisos.append(
                    f"'{item.descricao}': preço {percentual}% {sentido} que o combinado "
                    f"(nota {_reais(por_unidade)}/un, pedido {_reais(combinado)}/un)."
                )
        linhas.append(linha)

    fora = [pid for pid in por_produto if pid not in usados and pid not in {i.produto_id for i in pedido.itens}]
    return Casamento(linhas=linhas, fora_do_pedido=fora, nao_vieram=nao_vieram)


def validar_pedido_da_nota(
    db: Session, token: dict[str, Any], pedido_id: int, fornecedor_id: Optional[int]
) -> PedidoCompra:
    if not modulo_compras_ativo(db):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "Ligar a nota a um pedido exige o módulo Compras."
        )
    pedido = pedidos_service.carregar(db, token, pedido_id)
    if pedido.situacao not in SituacaoPedido.EM_ABERTO:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"O pedido {pedido.codigo} está {pedido.situacao.lower()}: não espera mais mercadoria.",
        )
    if fornecedor_id is None or pedido.fornecedor_id != fornecedor_id:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"O pedido {pedido.codigo} é de outro fornecedor, não do emitente desta nota.",
        )
    return pedido


def receber_pela_nota(
    db: Session,
    token: dict[str, Any],
    pedido: PedidoCompra,
    *,
    nota_entrada_id: int,
    numero_nota: str,
    entradas: list[EntradaDaNota],
    movimentos_por_produto: dict[int, list[Any]],
    gerar_contas: bool,
) -> tuple[list[str], int]:
    """Registra no pedido o que a nota trouxe. Devolve (avisos de divergência, contas lançadas).

    `gerar_contas`: só quando a nota NÃO tem duplicatas (com elas, quem gera é
    a própria XML). As contas seguem as parcelas do pedido, sobre o valor da
    NOTA para os itens do pedido.
    """
    casamento = casar(pedido, entradas)
    usuario_id, usuario_nome = pedidos_service.usuario_do_token(token)
    recebimento = RecebimentoCompra(
        empresa_id=token["empresa_id"],
        pedido_id=pedido.id,
        nota_entrada_id=nota_entrada_id,
        numero_nota=(numero_nota or "")[:20] or None,
        recebido_por_id=usuario_id,
        recebido_por_nome=usuario_nome,
        recebido_em=datetime.now(),
    )
    db.add(recebimento)
    db.flush()

    valor = 0
    for linha in casamento.linhas:
        item = linha.item
        if linha.quantidade <= 0:
            continue
        movs = movimentos_por_produto.get(item.produto_id, [])
        for mov in movs:
            mov.recebimento_compra_id = recebimento.id
        recebimento.itens.append(RecebimentoCompraItem(
            pedido_item_id=item.id,
            produto_id=item.produto_id,
            descricao=item.descricao,
            unidade_compra=item.unidade_compra,
            fator=item.fator,
            quantidade=linha.quantidade,
            unidades=float(linha.unidades_nota),
            custo_unitario=linha.custo_compra,
            movimentacao_id=movs[0].id if movs else None,
        ))
        item.quantidade_recebida += linha.quantidade
        valor += linha.quantidade * linha.custo_compra

    # O custo da nota já traz frete e impostos por item (D6 da XML): o ajuste
    # de frete/desconto do pedido não se soma de novo aqui.
    recebimento.valor_itens = valor
    recebimento.valor_ajuste = 0
    recebimento.valor_total = valor

    anterior = pedido.situacao
    pedido.situacao = (
        SituacaoPedido.RECEBIDO if all(i.pendente == 0 for i in pedido.itens) else SituacaoPedido.PARCIAL
    )
    db.flush()

    if gerar_contas and valor > 0 and financeiro_disponivel(db):
        recebimento.contas_pagar_lancadas = lancar_contas(db, token, pedido, recebimento)

    avisos = casamento.avisos
    motivo = f"NF-e {numero_nota}" + (f" · {len(avisos)} divergência(s)" if avisos else "")
    pedidos_service.registrar_log(db, token, pedido, "RECEBIDO", anterior, pedido.situacao, motivo[:255])
    db.flush()
    return avisos, recebimento.contas_pagar_lancadas
