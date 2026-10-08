# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fabrica/separacao.py
# DESCRIÇÃO: Separação bipada e margem real (docs/marcenaria-fabrica-plano.md, F4).
# ---------------------------------------------------------------------------
"""
Na OS da fábrica a chapa sai do estoque quando o almoxarife a SEPARA, não
quando a OS fecha (D6). Uma regra só para tudo, com `quantidade_separada`:

- separar baixa a DIFERENÇA bipada (SAÍDA, origem ORDEM_SERVICO);
- finalizar baixa `quantidade - separada` (services/ordem_servico.py);
- a reserva de Compras conta `quantidade - separada` (demanda_os.py);
- cancelar devolve o separado à prateleira; reabrir não (já foi usado).

O CUSTO REAL (D7) é o custo médio do estoque no instante da separação,
ponderado se o item foi separado aos poucos. O `custo_unitario` congelado na
aprovação nunca muda: a margem real é a comparação dos dois.

A tela do almoxarife não mostra custo (DC5): `listar` não leva preço.
"""

from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enum import (
    MovimentacaoOrigem,
    MovimentacaoTipo,
    OrdemServicoItemAprovacao,
    OrdemServicoItemTipo,
    OrdemServicoStatus,
)
from app.db.models.fabrica_orcamento import EventoFase, FabricaMovel
from app.db.models.ordem_servico import OrdemServico
from app.db.models.ordem_servico_item import OrdemServicoItem
from app.db.models.pedido_compra import PedidoCompra
from app.db.models.produto import Produto
from app.db.models.produto_embalagem import ProdutoEmbalagem
from app.db.models.recebimento_compra import RecebimentoCompra
from app.schemas.fabrica import (
    InsumoMargem,
    ItemSeparacao,
    MargemRead,
    MovelMargem,
    SeparacaoRead,
)
from app.services import movimentacao_estoque as mov_service
from app.services.fabrica import trilho
from app.services.fabrica.modo import Fase


def _erro(codigo: int, detalhe: str) -> HTTPException:
    return HTTPException(status_code=codigo, detail=detalhe)


def _itens(os_: OrdemServico) -> list[OrdemServicoItem]:
    """O que se separa: peça do catálogo, aprovada — a mesma regra da baixa."""
    return [
        i for i in os_.itens
        if i.tipo == OrdemServicoItemTipo.PRODUTO and i.produto_id is not None
        and i.status_aprovacao == OrdemServicoItemAprovacao.APROVADO and (i.quantidade or 0) > 0
    ]


def _falta(item: OrdemServicoItem) -> float:
    return round(max((item.quantidade or 0) - (item.quantidade_separada or 0), 0), 3)


def tudo_separado(os_: OrdemServico) -> tuple[bool, list[str]]:
    faltando = [i.nome for i in _itens(os_) if _falta(i) > 0]
    return not faltando, faltando


def _os_para_separar(db: Session, numero_os: str) -> OrdemServico:
    os_ = trilho._os_aberta(db, numero_os)
    if Fase.ORDEM.index(os_.fase_fabrica) < Fase.ORDEM.index(Fase.SEPARACAO_COMPRA):
        raise _erro(
            status.HTTP_409_CONFLICT,
            "A separação começa na etapa \"Separação e compra\" (depois do sinal).",
        )
    return os_


# --- Leitura --------------------------------------------------------------------------

def _codigos(db: Session, produto: Produto) -> list[str]:
    codigos = [c for c in (produto.codigo_barras, produto.codigo_produto) if c]
    for emb in db.scalars(select(ProdutoEmbalagem).where(
        ProdutoEmbalagem.produto_id == produto.id, ProdutoEmbalagem.ativo.is_(True),
    )):
        if emb.codigo_barras:
            codigos.append(emb.codigo_barras)
    return codigos


def _nome_do_cliente(os_: OrdemServico) -> Optional[str]:
    c = os_.cliente
    if c is None:
        return None
    return getattr(c, "nome", None) or getattr(c, "nome_fantasia", None) or getattr(c, "razao_social", None)


def listar(db: Session, numero_os: str) -> SeparacaoRead:
    os_ = trilho._os(db, numero_os)
    itens = []
    for item in _itens(os_):
        produto = db.get(Produto, item.produto_id)
        itens.append(ItemSeparacao(
            item_id=item.id,
            produto_id=item.produto_id,
            descricao=item.nome,
            unidade=(produto.unidade_medida if produto else None) or "UN",
            localizacao=produto.localizacao_estoque if produto else None,
            codigos=_codigos(db, produto) if produto else [],
            quantidade=float(item.quantidade or 0),
            separada=float(item.quantidade_separada or 0),
            falta=_falta(item),
            saldo_estoque=float(produto.estoque.quantidade or 0) if produto and produto.estoque else 0.0,
        ))
    pode = (
        os_.status not in (OrdemServicoStatus.FINALIZADA, OrdemServicoStatus.CANCELADA)
        and Fase.ORDEM.index(os_.fase_fabrica) >= Fase.ORDEM.index(Fase.SEPARACAO_COMPRA)
    )
    return SeparacaoRead(
        numero_os=os_.numero_os,
        cliente=_nome_do_cliente(os_),
        projeto=os_.objeto.modelo if os_.objeto else None,
        fase=os_.fase_fabrica,
        pode_separar=pode,
        completa=tudo_separado(os_)[0],
        itens=itens,
    )


# --- Separar e estornar ---------------------------------------------------------------------

def _achar(db: Session, os_: OrdemServico, codigo: Optional[str], item_id: Optional[int]) -> tuple[OrdemServicoItem, int]:
    """O item da OS e o FATOR do que foi bipado (embalagem de 10 = 10 unidades)."""
    itens = _itens(os_)
    if item_id is not None:
        item = next((i for i in itens if i.id == item_id), None)
        if item is None:
            raise _erro(status.HTTP_404_NOT_FOUND, "Este item não é desta OS (ou não se separa).")
        return item, 1
    codigo = (codigo or "").strip()
    if not codigo:
        raise _erro(status.HTTP_422_UNPROCESSABLE_ENTITY, "Bipe o código ou escolha o item.")
    por_produto = {i.produto_id: i for i in itens}
    for produto_id, item in por_produto.items():
        produto = db.get(Produto, produto_id)
        if produto and codigo in (produto.codigo_barras, produto.codigo_produto):
            return item, 1
    emb = db.scalars(select(ProdutoEmbalagem).where(
        ProdutoEmbalagem.codigo_barras == codigo, ProdutoEmbalagem.ativo.is_(True),
        ProdutoEmbalagem.produto_id.in_(list(por_produto) or [0]),
    )).first()
    if emb is not None:
        return por_produto[emb.produto_id], emb.fator
    raise _erro(status.HTTP_404_NOT_FOUND, f"O código {codigo} não é de nenhum material desta OS.")


def separar(db: Session, numero_os: str, token: dict[str, Any], codigo: Optional[str],
            item_id: Optional[int], quantidade: float) -> SeparacaoRead:
    os_ = _os_para_separar(db, numero_os)
    item, fator = _achar(db, os_, codigo, item_id)
    unidades = round(quantidade * fator, 3)
    if unidades > _falta(item) + 1e-9:
        raise _erro(
            status.HTTP_409_CONFLICT,
            f"'{item.nome}': falta separar {_falta(item):g}; bipado {unidades:g}. "
            "Se vai mais material, faça uma nova versão do orçamento.",
        )
    produto = db.get(Produto, item.produto_id)
    custo_agora = mov_service.custo_atual(produto.estoque) or 0
    usuario_nome = token.get("nome") or "Sistema"
    sub = token.get("sub")
    mov_service.registrar_movimentacao(
        db, produto=produto, tipo=MovimentacaoTipo.SAIDA, quantidade=unidades,
        origem=MovimentacaoOrigem.ORDEM_SERVICO,
        usuario_id=int(sub) if sub and str(sub).isdigit() else None, usuario_nome=usuario_nome,
        ordem_servico_id=os_.id, observacao=f"Separação da OS {os_.numero_os}",
        # A chapa está na mão do almoxarife: saldo negativo é contagem a acertar,
        # não motivo para travar a fábrica (mesma regra da baixa da OS).
        permitir_negativo=True,
    )
    antes = item.quantidade_separada or 0
    depois = round(antes + unidades, 3)
    item.custo_real = round(((item.custo_real or 0) * antes + custo_agora * unidades) / depois) if depois else None
    item.quantidade_separada = depois
    db.flush()
    return listar(db, numero_os)


def estornar(db: Session, numero_os: str, token: dict[str, Any], item_id: int,
             quantidade: float, motivo: str) -> SeparacaoRead:
    os_ = trilho._os_aberta(db, numero_os)
    item = next((i for i in _itens(os_) if i.id == item_id), None)
    if item is None:
        raise _erro(status.HTTP_404_NOT_FOUND, "Este item não é desta OS.")
    if quantidade > (item.quantidade_separada or 0) + 1e-9:
        raise _erro(status.HTTP_409_CONFLICT, f"'{item.nome}': só {item.quantidade_separada or 0:g} foi separado.")
    _devolver(db, os_, item, quantidade, token, f"Estorno da separação da OS {os_.numero_os}: {motivo.strip()}")
    trilho.registrar(db, os_, EventoFase.RETROCESSO, token.get("nome") or "Sistema",
                     f"Separação estornada: {quantidade:g} de {item.nome} — {motivo.strip()}")
    db.flush()
    return listar(db, numero_os)


def _devolver(db: Session, os_: OrdemServico, item: OrdemServicoItem, quantidade: float,
              token: dict[str, Any], observacao: str) -> None:
    produto = db.get(Produto, item.produto_id)
    sub = token.get("sub")
    mov_service.registrar_movimentacao(
        db, produto=produto, tipo=MovimentacaoTipo.ENTRADA, quantidade=quantidade,
        origem=MovimentacaoOrigem.ORDEM_SERVICO,
        usuario_id=int(sub) if sub and str(sub).isdigit() else None,
        usuario_nome=token.get("nome") or "Sistema",
        ordem_servico_id=os_.id, observacao=observacao[:500], permitir_negativo=True,
    )
    restante = round((item.quantidade_separada or 0) - quantidade, 3)
    item.quantidade_separada = restante if restante > 0 else None
    if item.quantidade_separada is None:
        item.custo_real = None


def devolver_tudo(db: Session, os_: OrdemServico, token: dict[str, Any]) -> None:
    """Cancelar a OS devolve à prateleira o que foi separado (D6). No-op fora da fábrica."""
    for item in _itens(os_):
        if item.quantidade_separada:
            _devolver(db, os_, item, item.quantidade_separada, token, f"OS {os_.numero_os} cancelada")
    db.flush()


def ha_separado(os_: OrdemServico) -> bool:
    return any((i.quantidade_separada or 0) > 0 for i in os_.itens)


# --- Margem orçada × real ----------------------------------------------------------------------

def custo_do_servico(db: Session, pedido_id: Optional[int]) -> Optional[int]:
    """O que a central de corte cobrou de fato: o que foi RECEBIDO do pedido (F5)."""
    if pedido_id is None:
        return None
    pedido = db.get(PedidoCompra, pedido_id)
    if pedido is None:
        return None
    recebido = db.scalar(
        select(func.coalesce(func.sum(RecebimentoCompra.valor_total), 0)).where(RecebimentoCompra.pedido_id == pedido_id)
    ) or 0
    return int(recebido) if recebido else None


def margem(db: Session, numero_os: str) -> MargemRead:
    from app.services.fabrica import orcamentos as orcamentos_service

    os_ = trilho._os(db, numero_os)
    orc = trilho.orcamento_aprovado(db, os_.id)
    if orc is None:
        raise _erro(status.HTTP_409_CONFLICT, "Ainda não há orçamento aprovado nesta OS.")

    insumos_orc = {i.produto_id: i for i in orcamentos_service._insumos(orc)}
    insumos = []
    for item in _itens(os_):
        if item.fabrica_orcamento_id != orc.id:
            continue
        orcado = insumos_orc.get(item.produto_id)
        # Orçado: a FRAÇÃO de chapa (com a perda) ao custo congelado — o que o
        # preço cobriu. Real: as chapas inteiras que saíram, ao custo do dia.
        custo_orcado = sum(
            orcamentos_service._custo_material(mat, orc.perda_bp)
            for _amb, mov in orcamentos_service._moveis(orc) for mat in mov.materiais
            if mat.produto_id == item.produto_id
        )
        separada = float(item.quantidade_separada or 0)
        insumos.append(InsumoMargem(
            produto_id=item.produto_id,
            descricao=item.nome,
            quantidade=float(item.quantidade or 0),
            separada=separada,
            custo_orcado=custo_orcado,
            custo_real=round((item.custo_real or 0) * separada) if separada else None,
            custo_unitario_orcado=orcado.custo_unitario if orcado else item.custo_unitario,
            custo_unitario_real=item.custo_real,
        ))

    moveis = []
    for amb, mov in orcamentos_service._moveis(orc):
        if not mov.terceirizado:
            continue
        moveis.append(MovelMargem(
            movel_id=mov.id,
            nome=f"{amb.nome} — {mov.nome}",
            custo_orcado=mov.custo_terceiro or 0,
            custo_real=custo_do_servico(db, mov.pedido_compra_id),
            pedido_compra_id=mov.pedido_compra_id,
        ))

    custo_orcado = (orc.custo_total or 0)
    reais = [i.custo_real for i in insumos] + [m.custo_real for m in moveis]
    completo = all(r is not None for r in reais) and all(i.separada >= i.quantidade for i in insumos)
    custo_real = sum(r or 0 for r in reais)
    preco = orc.total

    def _bp(custo: int) -> Optional[int]:
        return round((preco - custo) * 10000 / preco) if preco else None

    return MargemRead(
        numero_os=os_.numero_os,
        versao=orc.versao,
        preco=preco,
        custo_orcado=custo_orcado,
        custo_real=custo_real,
        margem_orcada_bp=_bp(custo_orcado),
        margem_real_bp=_bp(custo_real) if completo else None,
        completo=completo,
        insumos=insumos,
        terceirizados=moveis,
    )


def movel_da_os(db: Session, movel_id: int) -> tuple[FabricaMovel, OrdemServico]:
    movel = db.get(FabricaMovel, movel_id)
    if movel is None:
        raise _erro(status.HTTP_404_NOT_FOUND, "Móvel não encontrado.")
    os_ = db.get(OrdemServico, movel.ambiente.orcamento.os_id)
    return movel, os_
