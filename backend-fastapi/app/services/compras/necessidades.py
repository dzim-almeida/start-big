# ---------------------------------------------------------------------------
# ARQUIVO: app/services/compras/necessidades.py
# MÓDULO: Service — Necessidades de compra (Compras, fase 2)
# ---------------------------------------------------------------------------
"""
"O que eu preciso comprar?" — por estoque mínimo (fase 2). A média de vendas
entra na fase 5 e a OS da marcenaria na fase 6, como OUTRAS origens desta
mesma tela (plano, §3).

A conta é a de `necessidade.sugerir_compra` (pura, testada): só entra quem
tem mínimo cadastrado, e o que está A CAMINHO (pedidos enviados) desconta.
Rascunho não desconta — mas aparece ("já em rascunho PC-000012"), para o
lojista não pedir duas vezes sem saber.

FORNECEDOR SUGERIDO, nesta ordem: o principal do produto; senão o mais barato
por unidade; senão o primeiro cadastrado. Os outros vêm em `opcoes`, e o
mais barato, quando não é o sugerido, vem em `alternativa` (D18).
"""

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.enum import MovimentacaoOrigem, MovimentacaoTipo
from app.db.models.estoque import Estoque
from app.db.models.movimentacao_estoque import MovimentacaoEstoque
from app.db.models.fornecedor import Fornecedor
from app.db.models.pedido_compra import (
    OrigemDemanda,
    PedidoCompra,
    PedidoCompraItem,
    PedidoCompraOrigem,
    SituacaoPedido,
)
from app.db.models.produto import Produto
from app.db.models.produto_fornecedor import ProdutoFornecedor
from app.schemas.compras import (
    AlternativaMaisBarata,
    DemandaOSRead,
    GerarPedidos,
    NecessidadeGrupo,
    NecessidadeItem,
    OpcaoFornecedor,
    PedidoEscrita,
    PedidoItemEscrita,
    PedidoResumo,
)
from app.services.compras import pedidos as pedidos_service
from app.services.compras.demanda_os import demandas_por_produto, que_compram, reservado
from app.services.compras.fornecedores_produto import TIPOS_QUE_VENDEM
from app.services.compras.necessidade import (
    OfertaFornecedor,
    economia_percentual,
    mais_barato,
    preco_por_unidade,
    sugerir_compra,
    sugerir_por_vendas,
)

SEM_FORNECEDOR = "Sem fornecedor cadastrado"

# Fase 5: a base da sugestão. MINIMO é o comportamento da fase 2 (padrão).
BASE_MINIMO = "MINIMO"
BASE_VENDAS = "VENDAS"
ORIGEM_MINIMO = "MINIMO"
ORIGEM_VENDAS = "VENDAS"
ORIGEM_OS = "OS"
# Três meses: longo para não seguir um pico de uma semana, curto para
# acompanhar a estação (cerveja no verão).
JANELA_VENDAS_DIAS = 90


def _vende(fornecedor: Optional[Fornecedor]) -> bool:
    return fornecedor is not None and fornecedor.ativo and fornecedor.tipo in TIPOS_QUE_VENDEM


def _nome(fornecedor: Fornecedor) -> str:
    return fornecedor.nome_fantasia or fornecedor.nome


def _em_pedido(db: Session, empresa_id: int) -> dict[int, float]:
    """Unidades do produto a caminho (pedidos ENVIADO/PARCIAL), por produto."""
    pendente = (
        PedidoCompraItem.quantidade - PedidoCompraItem.quantidade_recebida - PedidoCompraItem.quantidade_cancelada
    ) * PedidoCompraItem.fator
    linhas = db.execute(
        select(PedidoCompraItem.produto_id, func.sum(pendente))
        .join(PedidoCompra, PedidoCompra.id == PedidoCompraItem.pedido_id)
        .where(
            PedidoCompra.empresa_id == empresa_id,
            PedidoCompra.situacao.in_(SituacaoPedido.EM_ABERTO),
            PedidoCompraItem.produto_id.is_not(None),
        )
        .group_by(PedidoCompraItem.produto_id)
    ).all()
    return {produto_id: float(max(total or 0, 0)) for produto_id, total in linhas}


def _em_rascunho(db: Session, empresa_id: int) -> tuple[dict[int, float], dict[int, list[str]]]:
    linhas = db.execute(
        select(PedidoCompraItem.produto_id, PedidoCompraItem.quantidade, PedidoCompraItem.fator, PedidoCompra.numero)
        .join(PedidoCompra, PedidoCompra.id == PedidoCompraItem.pedido_id)
        .where(
            PedidoCompra.empresa_id == empresa_id,
            PedidoCompra.situacao == SituacaoPedido.RASCUNHO,
            PedidoCompraItem.produto_id.is_not(None),
        )
    ).all()
    quantidades: dict[int, float] = defaultdict(float)
    codigos: dict[int, list[str]] = defaultdict(list)
    for produto_id, quantidade, fator, numero in linhas:
        quantidades[produto_id] += quantidade * fator
        codigo = f"PC-{numero:06d}"
        if codigo not in codigos[produto_id]:
            codigos[produto_id].append(codigo)
    return quantidades, codigos


def _opcao(linha: ProdutoFornecedor, unidade_produto: str, ver_custos: bool) -> OpcaoFornecedor:
    return OpcaoFornecedor(
        fornecedor_id=linha.fornecedor_id,
        fornecedor_nome=_nome(linha.fornecedor),
        embalagem_id=linha.embalagem_id,
        unidade_compra=linha.embalagem.sigla if linha.embalagem else unidade_produto,
        fator=linha.fator,
        ultimo_preco=linha.ultimo_preco if ver_custos else None,
        prazo_dias=linha.prazo_dias,
    )


def _vendido_por_produto(db: Session, desde: datetime) -> dict[int, float]:
    """Quanto saiu por VENDA e OS desde `desde`, líquido do que voltou.

    O livro de estoque é a fonte: saída de venda/OS soma; entrada dessas
    mesmas origens (venda cancelada, peça devolvida da OS) e DEVOLUÇÃO
    descontam. Assim a média não conta venda que não aconteceu.
    """
    origens = (MovimentacaoOrigem.VENDA.value, MovimentacaoOrigem.ORDEM_SERVICO.value)
    sinal = case(
        (MovimentacaoEstoque.tipo == MovimentacaoTipo.SAIDA, MovimentacaoEstoque.quantidade),
        else_=-MovimentacaoEstoque.quantidade,
    )
    linhas = db.execute(
        select(MovimentacaoEstoque.produto_id, func.sum(sinal))
        .where(
            MovimentacaoEstoque.created_at >= desde,
            MovimentacaoEstoque.tipo.in_([MovimentacaoTipo.SAIDA, MovimentacaoTipo.ENTRADA]),
            (MovimentacaoEstoque.origem.in_(origens))
            | (MovimentacaoEstoque.origem == MovimentacaoOrigem.DEVOLUCAO.value),
        )
        .group_by(MovimentacaoEstoque.produto_id)
    ).all()
    return {produto_id: max(float(total or 0), 0.0) for produto_id, total in linhas}


def listar(
    db: Session,
    token: dict[str, Any],
    ver_custos: bool,
    *,
    base: str = BASE_MINIMO,
    cobertura_dias: int = 30,
    janela_dias: int = JANELA_VENDAS_DIAS,
) -> list[NecessidadeGrupo]:
    """`base`: MINIMO (só o estoque mínimo, fase 2) ou VENDAS (também a média
    de venda dos últimos `janela_dias`, cobrindo `cobertura_dias` — fase 5)."""
    empresa_id = token["empresa_id"]
    pelas_vendas = base == BASE_VENDAS
    vendido = (
        _vendido_por_produto(db, datetime.now() - timedelta(days=janela_dias)) if pelas_vendas else {}
    )
    # Fase 6: as OS abertas já comprometeram peças (reserva calculada). Entram
    # SEMPRE, qualquer que seja a base: a OS é demanda concreta, com cliente.
    demandas = demandas_por_produto(db)
    filtro = Estoque.quantidade_minima.is_not(None)
    if pelas_vendas and vendido:
        filtro = filtro | Produto.id.in_([pid for pid, qtd in vendido.items() if qtd > 0])
    if demandas:
        filtro = filtro | Produto.id.in_(list(demandas))
    produtos = db.scalars(
        select(Produto)
        .join(Estoque, Estoque.id == Produto.id)
        .where(Produto.ativo.is_(True), filtro)
        .order_by(Produto.nome)
    ).all()
    if not produtos:
        return []

    em_pedido = _em_pedido(db, empresa_id)
    em_rascunho, rascunhos = _em_rascunho(db, empresa_id)
    vinculos: dict[int, list[ProdutoFornecedor]] = defaultdict(list)
    for linha in db.scalars(
        select(ProdutoFornecedor)
        .where(ProdutoFornecedor.produto_id.in_([p.id for p in produtos]))
        .order_by(ProdutoFornecedor.id)
    ).unique():
        if _vende(linha.fornecedor):
            vinculos[linha.produto_id].append(linha)

    grupos: dict[Optional[int], NecessidadeGrupo] = {}
    for produto in produtos:
        estoque = produto.estoque
        unidade = produto.unidade_medida or "UN"
        linhas = vinculos.get(produto.id, [])
        por_fornecedor = {l.fornecedor_id: l for l in linhas}

        # Quem é o sugerido (ver o cabeçalho).
        escolhido: Optional[ProdutoFornecedor] = None
        principal: Optional[Fornecedor] = None
        if produto.fornecedor_id in por_fornecedor:
            escolhido = por_fornecedor[produto.fornecedor_id]
        elif produto.fornecedor_id and _vende(produto.fornecedor):
            principal = produto.fornecedor  # principal sem linha: compra avulso, sem preço
        elif linhas:
            vencedor = mais_barato(OfertaFornecedor(l.fornecedor_id, l.ultimo_preco, l.fator) for l in linhas)
            escolhido = por_fornecedor.get(vencedor) or linhas[0]

        fator = escolhido.fator if escolhido else 1
        a_caminho = em_pedido.get(produto.id, 0.0)
        # O que as OS abertas já comprometeram não está livre: a prateleira tem,
        # mas tem dono. As três regras olham o SALDO LIVRE.
        das_os = demandas.get(produto.id, [])
        reservado_os = reservado(das_os)
        # RC04: a OS da fábrica sem sinal reserva (aparece em `reservado_os`),
        # mas não pesa na compra — nem pelo mínimo, senão compraria por tabela.
        compram = que_compram(das_os)
        livre = (estoque.quantidade or 0) - reservado(compram)
        pelo_minimo = sugerir_compra(
            saldo=livre,
            em_pedido=a_caminho,
            minimo=estoque.quantidade_minima,
            ideal=estoque.quantidade_ideal,
            fator=fator,
        )
        media = vendido.get(produto.id, 0.0) / janela_dias if pelas_vendas else 0.0
        pela_venda = sugerir_por_vendas(
            saldo=livre,
            em_pedido=a_caminho,
            media_diaria=media,
            prazo_dias=escolhido.prazo_dias if escolhido else None,
            cobertura_dias=cobertura_dias,
            minimo=estoque.quantidade_minima,
            fator=fator,
        ) if media > 0 else 0
        # A OS: o que ela precisa e o estoque livre + o que está a caminho não
        # cobrem. "Mínimo zero" na mesma conta pura dá exatamente isso.
        pela_os = sugerir_compra(saldo=livre, em_pedido=a_caminho, minimo=0, ideal=None, fator=fator) if compram else 0
        # Vale a MAIOR das três: a venda pede mais que o mínimo quando gira
        # rápido; o mínimo manda quando gira pouco; a OS, quando tem cliente
        # esperando uma peça que não está aqui.
        sugestao = max(pelo_minimo, pela_venda, pela_os)
        if sugestao <= 0:
            continue
        if pela_os >= max(pelo_minimo, pela_venda):
            origem = ORIGEM_OS
        else:
            origem = ORIGEM_VENDAS if pela_venda > pelo_minimo else ORIGEM_MINIMO

        fornecedor_id = escolhido.fornecedor_id if escolhido else (principal.id if principal else None)
        fornecedor_nome = (
            _nome(escolhido.fornecedor) if escolhido else (_nome(principal) if principal else None)
        )

        alternativa = None
        if ver_custos and escolhido is not None and escolhido.ultimo_preco:
            vencedor = mais_barato(OfertaFornecedor(l.fornecedor_id, l.ultimo_preco, l.fator) for l in linhas)
            if vencedor is not None and vencedor != escolhido.fornecedor_id:
                barato = por_fornecedor[vencedor]
                atual = preco_por_unidade(escolhido.ultimo_preco, escolhido.fator)
                menor = preco_por_unidade(barato.ultimo_preco, barato.fator)
                alternativa = AlternativaMaisBarata(
                    fornecedor_id=barato.fornecedor_id,
                    fornecedor_nome=_nome(barato.fornecedor),
                    preco_unidade=float(menor),
                    economia_bp=economia_percentual(atual, menor),
                )

        opcoes = [_opcao(l, unidade, ver_custos) for l in linhas]
        if principal is not None:
            opcoes.insert(0, OpcaoFornecedor(
                fornecedor_id=principal.id, fornecedor_nome=_nome(principal), unidade_compra=unidade, fator=1,
            ))

        item = NecessidadeItem(
            produto_id=produto.id,
            produto_nome=produto.nome,
            codigo_produto=produto.codigo_produto,
            unidade_medida=unidade,
            saldo=estoque.quantidade or 0,
            minimo=estoque.quantidade_minima,
            ideal=estoque.quantidade_ideal,
            em_pedido=a_caminho,
            em_rascunho=em_rascunho.get(produto.id, 0.0),
            rascunhos=rascunhos.get(produto.id, []),
            fornecedor_id=fornecedor_id,
            fornecedor_nome=fornecedor_nome,
            embalagem_id=escolhido.embalagem_id if escolhido else None,
            unidade_compra=(escolhido.embalagem.sigla if escolhido and escolhido.embalagem else unidade),
            fator=fator,
            sugestao=sugestao,
            ultimo_preco=escolhido.ultimo_preco if (ver_custos and escolhido) else None,
            alternativa=alternativa,
            opcoes=opcoes,
            origem=origem,
            media_diaria=round(media, 3) if media > 0 else None,
            dura_dias=(
                round(max(livre, 0) / media, 1) if media > 0 else None
            ),
            reservado_os=reservado_os,
            ordens=[
                DemandaOSRead(os_id=d.os_id, numero_os=d.numero_os, quantidade=d.quantidade,
                              data_previsao=d.data_previsao, data_instalacao=d.data_instalacao,
                              aguardando_sinal=not d.pode_comprar)
                for d in das_os
            ],
        )
        grupo = grupos.get(fornecedor_id)
        if grupo is None:
            grupo = grupos[fornecedor_id] = NecessidadeGrupo(
                fornecedor_id=fornecedor_id, fornecedor_nome=fornecedor_nome or SEM_FORNECEDOR, itens=[]
            )
        grupo.itens.append(item)

    # Com fornecedor primeiro, por nome; "sem fornecedor" por último.
    return sorted(grupos.values(), key=lambda g: (g.fornecedor_id is None, g.fornecedor_nome.lower()))


def gerar_pedidos(
    db: Session, token: dict[str, Any], dados: GerarPedidos, ver_custos: bool
) -> list[PedidoResumo]:
    """Um RASCUNHO por fornecedor, com o preço e a embalagem do cadastro dele.

    Sem preço cadastrado, o item entra com o último custo do estoque (por
    unidade) — ou zero; o lojista confere no rascunho antes de enviar.
    """
    por_fornecedor: dict[int, list] = defaultdict(list)
    for item in dados.itens:
        por_fornecedor[item.fornecedor_id].append(item)

    criados = []
    for fornecedor_id, itens in por_fornecedor.items():
        ids = [i.produto_id for i in itens]
        if len(ids) != len(set(ids)):
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, "O mesmo produto aparece duas vezes para o mesmo fornecedor."
            )
        fornecedor = pedidos_service.validar_fornecedor(db, fornecedor_id)
        vinculos = {
            l.produto_id: l
            for l in db.scalars(
                select(ProdutoFornecedor).where(
                    ProdutoFornecedor.fornecedor_id == fornecedor_id, ProdutoFornecedor.produto_id.in_(ids)
                )
            ).unique()
        }
        escritos = []
        for item in itens:
            vinculo = vinculos.get(item.produto_id)
            if vinculo is not None:
                custo = vinculo.ultimo_preco or 0
                escritos.append(PedidoItemEscrita(
                    produto_id=item.produto_id, embalagem_id=vinculo.embalagem_id, fator=vinculo.fator,
                    quantidade=item.quantidade, custo_unitario=custo,
                ))
            else:
                produto = db.get(Produto, item.produto_id)
                custo = (produto.estoque.valor_entrada or 0) if produto and produto.estoque else 0
                escritos.append(PedidoItemEscrita(
                    produto_id=item.produto_id, quantidade=item.quantidade, custo_unitario=custo,
                ))
        prazos = [v.prazo_dias for v in vinculos.values() if v.prazo_dias is not None]
        previsao = date.today() + timedelta(days=max(prazos)) if prazos else None

        pedido = pedidos_service.novo_rascunho(db, token, fornecedor)
        pedidos_service.aplicar_escrita(db, pedido, PedidoEscrita(
            fornecedor_id=fornecedor_id, previsao_entrega=previsao, itens=escritos,
        ))
        db.flush()
        _ligar_as_os(db, pedido)
        pedidos_service.registrar_log(
            db, token, pedido, "CRIADO", None, SituacaoPedido.RASCUNHO, "Gerado pelas Necessidades de compra"
        )
        criados.append(pedido)

    db.flush()
    return [pedidos_service.resumo(p, ver_custos) for p in criados]


def _ja_pedido_por_os(db: Session, produto_ids: list[int]) -> dict[tuple[int, int], float]:
    """(produto, OS) → unidades que pedidos ainda vivos (rascunho, enviado,
    parcial) já levam para aquela OS. Para não pedir duas vezes a mesma peça."""
    linhas = db.execute(
        select(PedidoCompraItem.produto_id, PedidoCompraOrigem.origem_id, func.sum(PedidoCompraOrigem.quantidade))
        .join(PedidoCompraItem, PedidoCompraItem.id == PedidoCompraOrigem.pedido_item_id)
        .join(PedidoCompra, PedidoCompra.id == PedidoCompraItem.pedido_id)
        .where(
            PedidoCompraOrigem.origem == OrigemDemanda.OS,
            PedidoCompraItem.produto_id.in_(produto_ids or [0]),
            PedidoCompra.situacao.in_((SituacaoPedido.RASCUNHO, *SituacaoPedido.EM_ABERTO)),
        )
        .group_by(PedidoCompraItem.produto_id, PedidoCompraOrigem.origem_id)
    ).all()
    return {(produto_id, os_id): float(total or 0) for produto_id, os_id, total in linhas}


def _ligar_as_os(db: Session, pedido: PedidoCompra) -> None:
    """RC06: reparte o que o pedido traz entre as OS a que a peça FALTA.

    A mesma fila do painel "Compras desta OS": o estoque de hoje cobre
    primeiro as OS mais antigas; o que ainda falta a cada uma, menos o que
    outros pedidos vivos já levam para ela, é o que este pedido atende. O que
    sobra é reposição (não se grava origem). Em unidades do produto.
    """
    produto_ids = [i.produto_id for i in pedido.itens if i.produto_id is not None]
    # RC04: o pedido não vai para OS da fábrica que ainda espera o sinal.
    demandas = {pid: que_compram(lista) for pid, lista in demandas_por_produto(db, produto_ids).items()}
    if not any(demandas.values()):
        return
    ja_pedido = _ja_pedido_por_os(db, produto_ids)
    for item in pedido.itens:
        sobra = float(item.quantidade * item.fator)
        produto = db.get(Produto, item.produto_id) if item.produto_id else None
        estoque = float(produto.estoque.quantidade or 0) if produto and produto.estoque else 0.0
        for d in demandas.get(item.produto_id, []):
            cobre = min(d.quantidade, max(estoque, 0.0))
            estoque -= cobre
            if sobra <= 0:
                break
            falta = d.quantidade - cobre - ja_pedido.get((item.produto_id, d.os_id), 0.0)
            if falta <= 0:
                continue
            parte = min(falta, sobra)
            item.origens.append(PedidoCompraOrigem(origem=OrigemDemanda.OS, origem_id=d.os_id, quantidade=parte))
            sobra -= parte
    db.flush()
