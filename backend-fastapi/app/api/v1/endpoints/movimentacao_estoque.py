# ---------------------------------------------------------------------------
# ARQUIVO: endpoints/movimentacao_estoque.py
# DESCRIÇÃO: Endpoints para movimentações de estoque.
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.depends import get_token, check_permission, _handle_db_transaction
from app.db.session import get_db
from app.schemas.movimentacao_estoque import MovimentacaoCreate, MovimentacaoRead
from app.services import movimentacao_estoque as mov_service

router = APIRouter()


@router.post(
    "/{produto_id}/movimentacoes",
    response_model=MovimentacaoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registra uma movimentação de estoque (entrada, saída ou ajuste)"
)
def create_movimentacao(
    produto_id: int = Path(..., ge=1, description="ID do produto"),
    data: MovimentacaoCreate = ...,
    usuario_token: dict = Depends(check_permission(required_permission="produto")),
    db: Session = Depends(get_db),
):
    return _handle_db_transaction(
        db,
        mov_service.create_movimentacao,
        produto_id,
        data,
        usuario_token,
    )


@router.get(
    "/movimentacoes",
    response_model=List[MovimentacaoRead],
    status_code=status.HTTP_200_OK,
    summary="Lista movimentações de estoque (todas ou filtradas por produto)"
)
def get_movimentacoes(
    produto_id: Optional[int] = Query(None, description="Filtrar por produto"),
    limit: int = Query(100, ge=1, le=500, description="Limite de registros"),
    usuario_token: dict = Depends(check_permission(required_permission="produto")),
    db: Session = Depends(get_db),
):
    return _handle_db_transaction(
        db,
        mov_service.get_movimentacoes,
        produto_id=produto_id,
        limit=limit,
    )