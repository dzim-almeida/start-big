# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fabrica/insumo.py
# DESCRIÇÃO: O produto como insumo da fábrica (docs/marcenaria-fabrica-plano.md, F1).
# ---------------------------------------------------------------------------
"""
Rota própria, fora do PUT do produto, pelo mesmo motivo das embalagens e dos
fornecedores de Compras: o cadastro do produto — e o payload que todo
segmento manda e recebe — não muda. Só a marcenaria enxerga isto.
"""

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models.produto import Produto
from app.schemas.fabrica import InsumoBusca, InsumoEscrita, InsumoRead
from app.services.movimentacao_estoque import custo_atual


def _produto(db: Session, produto_id: int) -> Produto:
    produto = db.get(Produto, produto_id)
    if produto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado.")
    return produto


def _ler(produto: Produto) -> InsumoRead:
    return InsumoRead(
        produto_id=produto.id,
        unidade_medida=produto.unidade_medida,
        unidade_consumo=produto.unidade_consumo,
        consumo_por_unidade=produto.consumo_por_unidade,
        sofre_perda=bool(produto.sofre_perda),
    )


def obter(db: Session, produto_id: int) -> InsumoRead:
    return _ler(_produto(db, produto_id))


def salvar(db: Session, produto_id: int, dados: InsumoEscrita) -> InsumoRead:
    produto = _produto(db, produto_id)
    produto.unidade_consumo = dados.unidade_consumo
    produto.consumo_por_unidade = dados.consumo_por_unidade
    produto.sofre_perda = dados.sofre_perda
    db.flush()
    return _ler(produto)


def buscar(db: Session, busca: str, limite: int = 20) -> list[InsumoBusca]:
    """Só produtos ativos JÁ marcados como insumo, por nome ou código.

    Busca vazia lista os primeiros em ordem alfabética: a fábrica costuma ter
    poucas dezenas de insumos, e ver a lista ajuda a lembrar o nome.
    """
    termo = (busca or "").strip()
    consulta = select(Produto).where(
        Produto.ativo.is_(True),
        Produto.unidade_consumo.is_not(None),
        Produto.consumo_por_unidade.is_not(None),
    )
    if termo:
        consulta = consulta.where(or_(
            Produto.nome.ilike(f"%{termo}%"),
            Produto.codigo_produto.ilike(f"%{termo}%"),
            Produto.codigo_barras == termo,
        ))
    produtos = db.scalars(consulta.order_by(Produto.nome).limit(limite)).all()
    return [
        InsumoBusca(
            id=p.id, nome=p.nome, codigo_produto=p.codigo_produto, unidade_medida=p.unidade_medida,
            unidade_consumo=p.unidade_consumo, consumo_por_unidade=p.consumo_por_unidade,
            sofre_perda=bool(p.sofre_perda), custo_unitario=custo_atual(p.estoque) or 0,
        )
        for p in produtos
    ]
