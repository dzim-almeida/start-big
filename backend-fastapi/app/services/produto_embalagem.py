# ---------------------------------------------------------------------------
# ARQUIVO: app/services/produto_embalagem.py
# MÓDULO: Service — Embalagens do produto (fase 1 do plano de embalagens)
# ---------------------------------------------------------------------------
"""
Cadastro das embalagens de um produto. Nesta fase ninguém vende nem baixa
estoque por embalagem ainda — é o cadastro, o código e a etiqueta.

Regra que não se negocia (plano, D4): o código de barras de uma embalagem é
ÚNICO NO SISTEMA INTEIRO. Não pode repetir o código de barras nem o SKU de
nenhum produto ativo, nem o de outra embalagem. O leitor do caixa recusa código
ambíguo (`leitorCodigoBarras.util.ts`); uma colisão viraria "não achei" na
frente do cliente.
"""

from typing import Optional, Sequence

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.gtin import codigo_interno_embalagem
from app.db.models.produto import Produto
from app.db.models.produto_embalagem import ProdutoEmbalagem
from app.schemas.produto_embalagem import EmbalagensSalvar

CAMPOS = ("sigla", "descricao", "fator", "codigo_barras", "preco", "desconto_bp", "vende_no_pdv", "usa_na_entrada", "ativo")


def _conflito(detalhe: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detalhe)


def _produto(db: Session, produto_id: int) -> Produto:
    produto = db.get(Produto, produto_id)
    if produto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado.")
    return produto


def onde_o_codigo_esta(
    db: Session,
    codigo: str,
    ignorar_embalagens: Sequence[int] = (),
    ignorar_produto_id: Optional[int] = None,
) -> Optional[str]:
    """Quem já usa o código — descrição legível — ou None se está livre.

    `ignorar_produto_id` deixa de fora os códigos do próprio produto (usado
    pela validação do cadastro do produto, que confere só as embalagens).
    """
    stmt_produto = select(Produto).where(
        Produto.ativo.is_(True),
        or_(Produto.codigo_barras == codigo, Produto.codigo_produto == codigo),
    )
    if ignorar_produto_id is not None:
        stmt_produto = stmt_produto.where(Produto.id != ignorar_produto_id)
    produto = db.scalars(stmt_produto).first()
    if produto is not None:
        campo = "código de barras" if produto.codigo_barras == codigo else "código (SKU)"
        return f"o {campo} do produto '{produto.nome}'"

    stmt_emb = select(ProdutoEmbalagem).where(ProdutoEmbalagem.codigo_barras == codigo)
    if ignorar_embalagens:
        stmt_emb = stmt_emb.where(ProdutoEmbalagem.id.not_in(list(ignorar_embalagens)))
    emb = db.scalars(stmt_emb).first()
    if emb is not None:
        return f"a embalagem {emb.sigla} do produto '{emb.produto.nome}'"
    return None


def listar(db: Session, produto_id: int) -> list[ProdutoEmbalagem]:
    return list(_produto(db, produto_id).embalagens)


def salvar(db: Session, produto_id: int, dados: EmbalagensSalvar) -> list[ProdutoEmbalagem]:
    """Replace-all: atualiza as que vieram com id, cria as sem id, apaga as que não vieram."""
    produto = _produto(db, produto_id)
    existentes = {e.id: e for e in produto.embalagens}

    for item in dados.embalagens:
        if item.id is not None and item.id not in existentes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"A embalagem {item.id} não é deste produto.",
            )

    # O próprio produto não pode ter o código de uma embalagem sua.
    codigos_do_produto = {c for c in (produto.codigo_barras, produto.codigo_produto) if c}
    ids_da_lista = [e.id for e in dados.embalagens if e.id is not None]
    for item in dados.embalagens:
        if item.codigo_barras is None:
            continue
        if item.codigo_barras in codigos_do_produto:
            raise _conflito(
                f"O código {item.codigo_barras} já é o do próprio produto. A embalagem precisa de um código dela."
            )
        dono = onde_o_codigo_esta(db, item.codigo_barras, ignorar_embalagens=ids_da_lista, ignorar_produto_id=produto.id)
        if dono:
            raise _conflito(f"O código {item.codigo_barras} já é {dono}.")

    manter = set(ids_da_lista)
    for emb_id, emb in existentes.items():
        if emb_id not in manter:
            produto.embalagens.remove(emb)
    db.flush()

    a_gerar: list[ProdutoEmbalagem] = []
    for item in dados.embalagens:
        emb = existentes[item.id] if item.id is not None else ProdutoEmbalagem(produto_id=produto.id)
        for campo in CAMPOS:
            setattr(emb, campo, getattr(item, campo))
        if item.id is None:
            produto.embalagens.append(emb)
        if item.gerar_codigo_interno and not item.codigo_barras:
            a_gerar.append(emb)
    db.flush()

    # O código interno sai do id, que só existe depois do flush.
    for emb in a_gerar:
        codigo = codigo_interno_embalagem(emb.id)
        dono = onde_o_codigo_esta(db, codigo, ignorar_embalagens=[emb.id])
        if dono:
            raise _conflito(f"O código interno {codigo} já é {dono}. Informe o código à mão.")
        emb.codigo_barras = codigo
    db.flush()
    db.refresh(produto)
    return list(produto.embalagens)


def codigo_de_produto_livre(db: Session, codigo: Optional[str], produto_id: Optional[int] = None) -> None:
    """Para o cadastro do PRODUTO: o código dele não pode ser o de uma embalagem (dele ou de outro)."""
    if not codigo:
        return
    emb = db.scalars(select(ProdutoEmbalagem).where(ProdutoEmbalagem.codigo_barras == codigo)).first()
    if emb is None:
        return
    dono = "deste produto" if emb.produto_id == produto_id else f"do produto '{emb.produto.nome}'"
    raise _conflito(f"O código {codigo} já é da embalagem {emb.sigla} {dono}.")
