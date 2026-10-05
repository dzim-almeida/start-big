# ---------------------------------------------------------------------------
# ARQUIVO: endpoints/fabrica.py
# DESCRIÇÃO: Marcenaria-fábrica (docs/marcenaria-fabrica-plano.md).
#            F1: o produto como insumo (unidade de consumo × compra).
# ---------------------------------------------------------------------------
#
# O ROUTER INTEIRO só existe para o segmento Marcenaria (403
# SEGMENTO_SEM_FABRICA nos outros), e cada rota pede a permissão de quem
# mexe no cadastro de produto. Prefixo próprio, como /compras: nada disto se
# mistura com as rotas de /produtos que todo segmento usa.
# ---------------------------------------------------------------------------

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.core.depends import _handle_db_transaction, check_permission
from app.core.segmentos.definicoes.marcenaria import SEGMENTO_MARCENARIA
from app.db.session import get_db
from app.schemas.fabrica import InsumoEscrita, InsumoRead
from app.services.fabrica import insumo as insumo_service
from app.services.segmentos import get_segmento_atual


def requer_marcenaria(db: Session = Depends(get_db)) -> None:
    """403 fora da marcenaria: a fábrica não existe para os outros segmentos."""
    if get_segmento_atual(db) != SEGMENTO_MARCENARIA:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "codigo": "SEGMENTO_SEM_FABRICA",
                "mensagem": "Este recurso é da marcenaria (fábrica de planejados).",
            },
        )


router = APIRouter(dependencies=[Depends(requer_marcenaria)])


@router.get(
    "/produtos/{produto_id}/insumo",
    response_model=InsumoRead,
    summary="O produto como insumo da fábrica",
    description="Unidade de consumo (M2, M, UN), quanto uma unidade do estoque rende e se sofre perda.",
)
def obter_insumo(
    produto_id: int = Path(..., ge=1),
    user_token: Dict[str, Any] = Depends(check_permission(required_permission="produto")),
    db: Session = Depends(get_db),
):
    return insumo_service.obter(db, produto_id)


@router.put(
    "/produtos/{produto_id}/insumo",
    response_model=InsumoRead,
    summary="Salvar o produto como insumo da fábrica",
    description="`unidade_consumo` nulo desliga: o produto volta a ser comum (rendimento e perda são limpos).",
)
def salvar_insumo(
    dados: InsumoEscrita,
    produto_id: int = Path(..., ge=1),
    user_token: Dict[str, Any] = Depends(check_permission(required_permission="produto")),
    db: Session = Depends(get_db),
):
    return _handle_db_transaction(db, insumo_service.salvar, produto_id, dados)
