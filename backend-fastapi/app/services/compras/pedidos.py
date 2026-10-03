# ---------------------------------------------------------------------------
# ARQUIVO: app/services/compras/pedidos.py
# MÓDULO: Service — Pedido de compra (Compras, fase 2)
# ---------------------------------------------------------------------------
"""
O ciclo do pedido nesta fase (D5, D6, D7):

    criar ─► RASCUNHO ──enviar──► ENVIADO
                │  ▲                 │
                │  └─voltar (motivo)─┘
                └──cancelar (motivo)──► CANCELADO ◄── cancelar (motivo)

- Só RASCUNHO se edita por inteiro (itens, preços, condição). ENVIADO aceita
  só previsão e observação: o fornecedor já recebeu o pedido, e mudar item
  exige voltar a rascunho COM MOTIVO no histórico.
- Recebimento (PARCIAL/RECEBIDO) é a fase 3. Até lá ninguém sai de ENVIADO
  por recebimento, então cancelar um enviado é sempre permitido.
- Toda mudança vira linha no `compras_log` (quem, quando, por quê).

O pedido NÃO mexe no estoque nem no financeiro: é o compromisso. Estoque e
contas a pagar nascem no recebimento.
"""

import re
from datetime import date, datetime
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.db.models.compra_log import CompraLog
from app.db.models.empresa import Empresa
from app.db.models.fornecedor import Fornecedor
from app.db.models.pedido_compra import (
    PedidoCompra,
    PedidoCompraItem,
    PedidoCompraParcela,
    SituacaoPedido,
    TipoPedido,
)
from app.db.models.produto import Produto
from app.db.models.produto_fornecedor import ProdutoFornecedor
from app.db.models.recebimento_compra import RecebimentoCompra
from app.schemas.compras import (
    CompraLogRead,
    MensagemFornecedor,
    PedidoDadosEscrita,
    PedidoEscrita,
    PedidoItemEscrita,
    PedidoItemRead,
    PedidoListagem,
    PedidoParcelaEscrita,
    PedidoParcelaRead,
    PedidoRead,
    PedidoResumo,
    RecebimentoItemRead,
    RecebimentoRead,
)
from app.services.compras.fornecedores_produto import TIPOS_QUE_VENDEM
from app.services.compras.parcelas import gerar_parcelas

OBJETO_PEDIDO = "PEDIDO"


def _erro(codigo: int, detalhe: str) -> HTTPException:
    return HTTPException(status_code=codigo, detail=detalhe)


def usuario_do_token(token: dict[str, Any]) -> tuple[Optional[int], str]:
    sub = token.get("sub")
    return (int(sub) if sub and str(sub).isdigit() else None), token.get("nome", "Desconhecido")


def registrar_log(
    db: Session,
    token: dict[str, Any],
    pedido: PedidoCompra,
    acao: str,
    anterior: Optional[str],
    nova: Optional[str],
    motivo: Optional[str] = None,
) -> None:
    usuario_id, usuario_nome = usuario_do_token(token)
    db.add(CompraLog(
        objeto=OBJETO_PEDIDO, objeto_id=pedido.id, acao=acao,
        situacao_anterior=anterior, situacao_nova=nova, motivo=motivo,
        usuario_id=usuario_id, usuario_nome=usuario_nome,
    ))


# --- leitura -------------------------------------------------------------------

def _atrasado(pedido: PedidoCompra) -> bool:
    return (
        pedido.situacao in SituacaoPedido.EM_ABERTO
        and pedido.previsao_entrega is not None
        and pedido.previsao_entrega < date.today()
    )


def resumo(pedido: PedidoCompra, ver_custos: bool) -> PedidoResumo:
    return PedidoResumo(
        id=pedido.id,
        numero=pedido.numero,
        codigo=pedido.codigo,
        situacao=pedido.situacao,
        fornecedor_id=pedido.fornecedor_id,
        fornecedor_nome=pedido.fornecedor_nome,
        previsao_entrega=pedido.previsao_entrega,
        atrasado=_atrasado(pedido),
        quantidade_itens=len(pedido.itens),
        valor_total=pedido.valor_total if ver_custos else None,
        criado_em=pedido.criado_em,
        enviado_em=pedido.enviado_em,
    )


def telefone_whatsapp(fornecedor: Optional[Fornecedor]) -> Optional[str]:
    """Celular (ou fixo) com DDI 55, só dígitos. Nulo se não há número utilizável."""
    if fornecedor is None:
        return None
    for numero in (fornecedor.celular, fornecedor.telefone):
        digitos = re.sub(r"\D", "", numero or "")
        if len(digitos) in (10, 11):
            return f"55{digitos}"
        if len(digitos) in (12, 13) and digitos.startswith("55"):
            return digitos
    return None


def _historico(db: Session, pedido_id: int) -> list[CompraLogRead]:
    linhas = db.scalars(
        select(CompraLog)
        .where(CompraLog.objeto == OBJETO_PEDIDO, CompraLog.objeto_id == pedido_id)
        .order_by(CompraLog.ocorrido_em.desc(), CompraLog.id.desc())
    ).all()
    return [CompraLogRead.model_validate(l, from_attributes=True) for l in linhas]


def _codigos_barras(db: Session, item: PedidoCompraItem) -> list[str]:
    """O que o leitor pode bipar para este item: a embalagem primeiro, depois o produto.

    O código do PRODUTO vai junto mesmo num item em fardo: a tela usa para
    avisar "bipou a unidade, este item é recebido em FD" em vez de "não achei".
    """
    if item.produto_id is None:
        return []
    produto = db.get(Produto, item.produto_id)
    if produto is None:
        return []
    codigos: list[str] = []
    if item.embalagem_id is not None:
        embalagem = next((e for e in produto.embalagens if e.id == item.embalagem_id), None)
        if embalagem is not None and embalagem.codigo_barras:
            codigos.append(embalagem.codigo_barras)
    for codigo in (produto.codigo_barras, produto.codigo_produto):
        if codigo and codigo not in codigos:
            codigos.append(codigo)
    return codigos


def _recebimentos(db: Session, pedido_id: int, ver_custos: bool) -> list[RecebimentoRead]:
    linhas = db.scalars(
        select(RecebimentoCompra)
        .options(selectinload(RecebimentoCompra.itens))
        .where(RecebimentoCompra.pedido_id == pedido_id)
        .order_by(RecebimentoCompra.recebido_em.desc(), RecebimentoCompra.id.desc())
    ).all()
    return [
        RecebimentoRead(
            id=r.id,
            recebido_em=r.recebido_em,
            recebido_por_nome=r.recebido_por_nome,
            numero_nota=r.numero_nota,
            observacao=r.observacao,
            valor_itens=r.valor_itens if ver_custos else None,
            valor_ajuste=r.valor_ajuste if ver_custos else None,
            valor_total=r.valor_total if ver_custos else None,
            contas_pagar_lancadas=r.contas_pagar_lancadas,
            itens=[
                RecebimentoItemRead(
                    descricao=i.descricao, unidade_compra=i.unidade_compra, fator=i.fator,
                    quantidade=i.quantidade, unidades=i.unidades,
                    custo_unitario=i.custo_unitario if ver_custos else None,
                )
                for i in r.itens
            ],
        )
        for r in linhas
    ]


def serializar(db: Session, pedido: PedidoCompra, ver_custos: bool) -> PedidoRead:
    base = resumo(pedido, ver_custos)
    return PedidoRead(
        **base.model_dump(),
        tipo=pedido.tipo,
        condicao_pagamento=pedido.condicao_pagamento,
        frete=pedido.frete if ver_custos else None,
        desconto=pedido.desconto if ver_custos else None,
        valor_itens=pedido.valor_itens if ver_custos else None,
        observacao=pedido.observacao,
        motivo_cancelamento=pedido.motivo_cancelamento,
        criado_por_nome=pedido.criado_por_nome,
        fornecedor_telefone=telefone_whatsapp(pedido.fornecedor),
        itens=[
            PedidoItemRead(
                id=i.id,
                produto_id=i.produto_id,
                descricao=i.descricao,
                codigo_fornecedor=i.codigo_fornecedor,
                embalagem_id=i.embalagem_id,
                unidade_compra=i.unidade_compra,
                fator=i.fator,
                quantidade=i.quantidade,
                quantidade_recebida=i.quantidade_recebida,
                quantidade_cancelada=i.quantidade_cancelada,
                custo_unitario=i.custo_unitario if ver_custos else None,
                subtotal=i.quantidade * i.custo_unitario if ver_custos else None,
                pendente=i.pendente,
                codigos_barras=_codigos_barras(db, i),
            )
            for i in pedido.itens
        ],
        parcelas=[
            PedidoParcelaRead(numero=p.numero, dias=p.dias, valor=p.valor if ver_custos else None)
            for p in pedido.parcelas
        ],
        historico=_historico(db, pedido.id),
        recebimentos=_recebimentos(db, pedido.id, ver_custos),
    )


def carregar(db: Session, token: dict[str, Any], pedido_id: int) -> PedidoCompra:
    pedido = db.scalars(
        select(PedidoCompra)
        .options(selectinload(PedidoCompra.itens), selectinload(PedidoCompra.parcelas))
        .where(PedidoCompra.id == pedido_id, PedidoCompra.empresa_id == token["empresa_id"])
    ).first()
    if pedido is None:
        raise _erro(status.HTTP_404_NOT_FOUND, "Pedido de compra não encontrado.")
    return pedido


def obter(db: Session, token: dict[str, Any], pedido_id: int, ver_custos: bool) -> PedidoRead:
    return serializar(db, carregar(db, token, pedido_id), ver_custos)


def listar(
    db: Session,
    token: dict[str, Any],
    ver_custos: bool,
    *,
    situacao: Optional[str] = None,
    fornecedor_id: Optional[int] = None,
    busca: Optional[str] = None,
    a_receber: bool = False,
    limit: int = 20,
    offset: int = 0,
) -> PedidoListagem:
    filtro = select(PedidoCompra).where(PedidoCompra.empresa_id == token["empresa_id"])
    if a_receber:
        # A tela de Recebimento: o que foi enviado e ainda não chegou todo.
        filtro = filtro.where(PedidoCompra.situacao.in_(SituacaoPedido.EM_ABERTO))
    if situacao:
        if situacao not in SituacaoPedido.TODAS:
            raise _erro(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Situação desconhecida: {situacao}.")
        filtro = filtro.where(PedidoCompra.situacao == situacao)
    if fornecedor_id:
        filtro = filtro.where(PedidoCompra.fornecedor_id == fornecedor_id)
    termo = (busca or "").strip()
    if termo:
        digitos = re.sub(r"\D", "", termo)
        condicoes = [PedidoCompra.fornecedor_nome.ilike(f"%{termo}%")]
        if digitos:
            condicoes.append(PedidoCompra.numero == int(digitos))
        filtro = filtro.where(or_(*condicoes))

    total = db.scalar(select(func.count()).select_from(filtro.subquery())) or 0
    pedidos = db.scalars(
        filtro.options(selectinload(PedidoCompra.itens))
        .order_by(PedidoCompra.criado_em.desc(), PedidoCompra.id.desc())
        .limit(limit).offset(offset)
    ).all()
    return PedidoListagem(itens=[resumo(p, ver_custos) for p in pedidos], total_itens=total)


# --- escrita -------------------------------------------------------------------

def validar_fornecedor(db: Session, fornecedor_id: int) -> Fornecedor:
    fornecedor = db.get(Fornecedor, fornecedor_id)
    if fornecedor is None:
        raise _erro(status.HTTP_404_NOT_FOUND, f"Fornecedor {fornecedor_id} não encontrado.")
    if not fornecedor.ativo:
        raise _erro(status.HTTP_422_UNPROCESSABLE_ENTITY, f"O fornecedor '{fornecedor.nome}' está inativo.")
    if fornecedor.tipo not in TIPOS_QUE_VENDEM:
        raise _erro(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"'{fornecedor.nome}' está cadastrado como {fornecedor.tipo}, não como fornecedor de produto.",
        )
    return fornecedor


def _item(db: Session, fornecedor_id: int, dados: PedidoItemEscrita) -> PedidoCompraItem:
    produto = db.get(Produto, dados.produto_id)
    if produto is None or not produto.ativo:
        raise _erro(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Produto {dados.produto_id} não encontrado ou inativo.")
    if produto.estoque is None:
        raise _erro(status.HTTP_422_UNPROCESSABLE_ENTITY, f"O produto '{produto.nome}' não controla estoque.")

    embalagem = None
    if dados.embalagem_id is not None:
        embalagem = next((e for e in produto.embalagens if e.id == dados.embalagem_id and e.ativo), None)
        if embalagem is None:
            raise _erro(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"A embalagem escolhida não é do produto '{produto.nome}' ou está inativa.",
            )
    vinculo = db.scalars(
        select(ProdutoFornecedor).where(
            ProdutoFornecedor.produto_id == produto.id, ProdutoFornecedor.fornecedor_id == fornecedor_id
        )
    ).first()
    return PedidoCompraItem(
        produto_id=produto.id,
        descricao=produto.nome[:255],
        codigo_fornecedor=vinculo.codigo_fornecedor if vinculo else None,
        embalagem_id=embalagem.id if embalagem else None,
        unidade_compra=(embalagem.sigla if embalagem else (produto.unidade_medida or "UN"))[:10],
        # A embalagem manda no fator, como em todo o resto do sistema.
        fator=embalagem.fator if embalagem else dados.fator,
        quantidade=dados.quantidade,
        custo_unitario=dados.custo_unitario,
    )


def _recalcular(pedido: PedidoCompra) -> None:
    pedido.valor_itens = sum(i.quantidade * i.custo_unitario for i in pedido.itens)
    total = pedido.valor_itens + pedido.frete - pedido.desconto
    if total < 0:
        raise _erro(status.HTTP_422_UNPROCESSABLE_ENTITY, "O desconto é maior que o valor do pedido.")
    pedido.valor_total = total


def _definir_parcelas(pedido: PedidoCompra, parcelas: Optional[list[PedidoParcelaEscrita]]) -> None:
    """Sem lista: gera pela condição. Com lista: tem de fechar o total exato."""
    if parcelas is None:
        try:
            geradas = gerar_parcelas(pedido.valor_total, pedido.condicao_pagamento)
        except ValueError as erro:
            raise _erro(status.HTTP_422_UNPROCESSABLE_ENTITY, str(erro))
        novas = [(p.dias, p.valor) for p in geradas]
    else:
        soma = sum(p.valor for p in parcelas)
        if parcelas and soma != pedido.valor_total:
            raise _erro(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"As parcelas somam {soma / 100:.2f} e o pedido, {pedido.valor_total / 100:.2f}. "
                "Ajuste as parcelas ou deixe o sistema gerar pela condição.",
            )
        dias = [p.dias for p in parcelas]
        if dias != sorted(dias):
            raise _erro(status.HTTP_422_UNPROCESSABLE_ENTITY, "As parcelas precisam estar em ordem de prazo.")
        novas = [(p.dias, p.valor) for p in parcelas]

    pedido.parcelas.clear()
    for numero, (dias, valor) in enumerate(novas, start=1):
        pedido.parcelas.append(PedidoCompraParcela(numero=numero, dias=dias, valor=valor))


def aplicar_escrita(db: Session, pedido: PedidoCompra, dados: PedidoEscrita) -> None:
    fornecedor = validar_fornecedor(db, dados.fornecedor_id)
    pedido.fornecedor_id = fornecedor.id
    pedido.fornecedor_nome = (fornecedor.nome_fantasia or fornecedor.nome)[:255]
    pedido.previsao_entrega = dados.previsao_entrega
    pedido.condicao_pagamento = (dados.condicao_pagamento or "").strip() or None
    pedido.frete = dados.frete
    pedido.desconto = dados.desconto
    pedido.observacao = (dados.observacao or "").strip() or None

    novos = [_item(db, fornecedor.id, i) for i in dados.itens]  # valida tudo antes de trocar
    pedido.itens.clear()
    pedido.itens.extend(novos)
    _recalcular(pedido)
    _definir_parcelas(pedido, dados.parcelas)


def proximo_numero(db: Session) -> int:
    return (db.scalar(select(func.max(PedidoCompra.numero))) or 0) + 1


def novo_rascunho(db: Session, token: dict[str, Any], fornecedor: Fornecedor) -> PedidoCompra:
    usuario_id, usuario_nome = usuario_do_token(token)
    pedido = PedidoCompra(
        empresa_id=token["empresa_id"],
        numero=proximo_numero(db),
        tipo=TipoPedido.MATERIAL,
        situacao=SituacaoPedido.RASCUNHO,
        fornecedor_id=fornecedor.id,
        fornecedor_nome=(fornecedor.nome_fantasia or fornecedor.nome)[:255],
        criado_por_id=usuario_id,
        criado_por_nome=usuario_nome,
    )
    db.add(pedido)
    # Já no banco: as Necessidades criam vários rascunhos na mesma transação, e
    # sem o flush o `max(numero)` do próximo não veria este (a sessão não faz
    # autoflush) — dois pedidos com o mesmo número, e o UNIQUE derruba tudo.
    db.flush()
    return pedido


def criar(db: Session, token: dict[str, Any], dados: PedidoEscrita, ver_custos: bool) -> PedidoRead:
    pedido = novo_rascunho(db, token, validar_fornecedor(db, dados.fornecedor_id))
    aplicar_escrita(db, pedido, dados)
    db.flush()
    registrar_log(db, token, pedido, "CRIADO", None, SituacaoPedido.RASCUNHO)
    db.flush()
    return serializar(db, pedido, ver_custos)


def _exigir(pedido: PedidoCompra, *situacoes: str, acao: str) -> None:
    if pedido.situacao not in situacoes:
        raise _erro(
            status.HTTP_409_CONFLICT,
            f"O pedido {pedido.codigo} está {pedido.situacao.lower()} e não pode {acao}.",
        )


def atualizar(
    db: Session, token: dict[str, Any], pedido_id: int, dados: PedidoEscrita, ver_custos: bool
) -> PedidoRead:
    pedido = carregar(db, token, pedido_id)
    _exigir(pedido, SituacaoPedido.RASCUNHO, acao="ser editado (volte-o a rascunho antes)")
    aplicar_escrita(db, pedido, dados)
    registrar_log(db, token, pedido, "EDITADO", pedido.situacao, pedido.situacao)
    db.flush()
    return serializar(db, pedido, ver_custos)


def atualizar_dados(
    db: Session, token: dict[str, Any], pedido_id: int, dados: PedidoDadosEscrita, ver_custos: bool
) -> PedidoRead:
    pedido = carregar(db, token, pedido_id)
    _exigir(pedido, SituacaoPedido.RASCUNHO, SituacaoPedido.ENVIADO, acao="ser alterado")
    mudou = []
    if dados.previsao_entrega != pedido.previsao_entrega:
        mudou.append("previsão de entrega")
        pedido.previsao_entrega = dados.previsao_entrega
    observacao = (dados.observacao or "").strip() or None
    if observacao != pedido.observacao:
        mudou.append("observação")
        pedido.observacao = observacao
    if mudou:
        registrar_log(db, token, pedido, "EDITADO", pedido.situacao, pedido.situacao, "Mudou " + " e ".join(mudou))
    db.flush()
    return serializar(db, pedido, ver_custos)


def enviar(db: Session, token: dict[str, Any], pedido_id: int, ver_custos: bool) -> PedidoRead:
    pedido = carregar(db, token, pedido_id)
    _exigir(pedido, SituacaoPedido.RASCUNHO, acao="ser enviado")
    if not pedido.itens:
        raise _erro(status.HTTP_422_UNPROCESSABLE_ENTITY, "O pedido não tem itens.")
    if pedido.parcelas and sum(p.valor for p in pedido.parcelas) != pedido.valor_total:
        raise _erro(status.HTTP_422_UNPROCESSABLE_ENTITY, "As parcelas não fecham o total do pedido. Edite o rascunho.")
    pedido.situacao = SituacaoPedido.ENVIADO
    pedido.enviado_em = datetime.now()
    registrar_log(db, token, pedido, "ENVIADO", SituacaoPedido.RASCUNHO, SituacaoPedido.ENVIADO)
    db.flush()
    return serializar(db, pedido, ver_custos)


def voltar_rascunho(
    db: Session, token: dict[str, Any], pedido_id: int, motivo: str, ver_custos: bool
) -> PedidoRead:
    pedido = carregar(db, token, pedido_id)
    _exigir(pedido, SituacaoPedido.ENVIADO, acao="voltar a rascunho")
    if any(i.quantidade_recebida for i in pedido.itens):
        raise _erro(status.HTTP_409_CONFLICT, "Parte do pedido já foi recebida; não dá para voltar a rascunho.")
    pedido.situacao = SituacaoPedido.RASCUNHO
    pedido.enviado_em = None
    registrar_log(db, token, pedido, "VOLTOU_RASCUNHO", SituacaoPedido.ENVIADO, SituacaoPedido.RASCUNHO, motivo)
    db.flush()
    return serializar(db, pedido, ver_custos)


def cancelar(db: Session, token: dict[str, Any], pedido_id: int, motivo: str, ver_custos: bool) -> PedidoRead:
    pedido = carregar(db, token, pedido_id)
    _exigir(pedido, SituacaoPedido.RASCUNHO, SituacaoPedido.ENVIADO, acao="ser cancelado")
    if any(i.quantidade_recebida for i in pedido.itens):
        # D7: o que entrou no estoque já está no livro e nas contas. O caminho
        # é encerrar o saldo (fase 3), não cancelar.
        raise _erro(status.HTTP_409_CONFLICT, "Parte do pedido já foi recebida; encerre o saldo em vez de cancelar.")
    anterior = pedido.situacao
    pedido.situacao = SituacaoPedido.CANCELADO
    pedido.cancelado_em = datetime.now()
    pedido.motivo_cancelamento = motivo
    registrar_log(db, token, pedido, "CANCELADO", anterior, SituacaoPedido.CANCELADO, motivo)
    db.flush()
    return serializar(db, pedido, ver_custos)


# --- mensagem ao fornecedor ------------------------------------------------------

def _reais(centavos: int) -> str:
    texto = f"{centavos / 100:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _qtd(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def mensagem_whatsapp(db: Session, token: dict[str, Any], pedido_id: int, ver_custos: bool) -> MensagemFornecedor:
    """O pedido em texto, do jeito que se manda para o vendedor do fornecedor.

    Com preço quando quem gera pode ver custo: o preço combinado faz parte do
    pedido, e é ele que se confere na nota.
    """
    pedido = carregar(db, token, pedido_id)
    empresa = db.get(Empresa, token["empresa_id"]) if token.get("empresa_id") else None
    loja = (empresa.nome_fantasia or empresa.razao_social) if empresa else None

    linhas = [f"*Pedido de compra {pedido.codigo}*"]
    if loja:
        linhas.append(f"De: {loja}")
    linhas.append("")
    for i in pedido.itens:
        codigo = f" (cód. {i.codigo_fornecedor})" if i.codigo_fornecedor else ""
        embalagem = f" com {i.fator}" if i.fator > 1 else ""
        preco = f" — {_reais(i.custo_unitario)} cada" if ver_custos and i.custo_unitario else ""
        linhas.append(f"• {_qtd(i.quantidade)} {i.unidade_compra}{embalagem} {i.descricao}{codigo}{preco}")
    linhas.append("")
    if ver_custos and pedido.valor_total:
        linhas.append(f"Total: {_reais(pedido.valor_total)}")
    if pedido.condicao_pagamento:
        linhas.append(f"Pagamento: {pedido.condicao_pagamento}")
    if pedido.previsao_entrega:
        linhas.append(f"Entrega até: {pedido.previsao_entrega:%d/%m/%Y}")
    if pedido.observacao:
        linhas.append(f"Obs.: {pedido.observacao}")
    while linhas and linhas[-1] == "":
        linhas.pop()
    return MensagemFornecedor(texto="\n".join(linhas), telefone=telefone_whatsapp(pedido.fornecedor))
