# ---------------------------------------------------------------------------
# ARQUIVO: services/movimentacao_estoque.py
# DESCRIÇÃO: Lógica de negócio para movimentações de estoque.
# ---------------------------------------------------------------------------

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Sequence, Optional, Dict, Any

from app.schemas.movimentacao_estoque import MovimentacaoCreate
from app.db.models.movimentacao_estoque import MovimentacaoEstoque
from app.db.crud import movimentacao_estoque as mov_crud
from app.db.crud import produto as produto_crud
from app.core.enum import MovimentacaoTipo


not_found_produto = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Produto não encontrado"
)

estoque_insuficiente = HTTPException(
    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    detail="Estoque insuficiente para realizar a saída"
)


def create_movimentacao(
    db: Session,
    produto_id: int,
    data: MovimentacaoCreate,
    usuario_token: Dict[str, Any],
) -> MovimentacaoEstoque:
    """
    Registra uma movimentação de estoque e atualiza a quantidade do produto.

    Regras:
    - ENTRADA: soma a quantidade ao estoque
    - SAIDA: subtrai; levanta 422 se o estoque for insuficiente
    - AJUSTE: define a quantidade final diretamente (quantidade = valor final desejado)
    """
    produto = produto_crud.get_produto_by_id(db, produto_id)
    if not produto:
        raise not_found_produto

    estoque = produto.estoque
    quantidade_anterior = estoque.quantidade

    if data.tipo == MovimentacaoTipo.ENTRADA:
        quantidade_posterior = quantidade_anterior + data.quantidade
    elif data.tipo == MovimentacaoTipo.SAIDA:
        if quantidade_anterior < data.quantidade:
            raise estoque_insuficiente
        quantidade_posterior = quantidade_anterior - data.quantidade
    else:  # AJUSTE
        quantidade_posterior = data.quantidade

    # Atualiza o estoque
    estoque.quantidade = quantidade_posterior

    # Determina a quantidade real movimentada para AJUSTE
    quantidade_real = (
        abs(quantidade_posterior - quantidade_anterior)
        if data.tipo == MovimentacaoTipo.AJUSTE
        else data.quantidade
    )

    movimentacao = MovimentacaoEstoque(
        produto_id=produto_id,
        produto_nome=produto.nome,
        usuario_id=int(usuario_token["sub"]),
        usuario_nome=usuario_token.get("nome", "Desconhecido"),
        tipo=data.tipo,
        quantidade=quantidade_real,
        quantidade_anterior=quantidade_anterior,
        quantidade_posterior=quantidade_posterior,
        observacao=data.observacao,
    )

    return mov_crud.create_movimentacao(db, movimentacao)


def get_movimentacoes(
    db: Session,
    produto_id: Optional[int] = None,
    limit: int = 100,
) -> Sequence[MovimentacaoEstoque]:
    """Lista movimentações de estoque, opcionalmente por produto."""
    return mov_crud.get_movimentacoes(db, produto_id=produto_id, limit=limit)