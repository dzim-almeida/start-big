# ---------------------------------------------------------------------------
# ARQUIVO: endpoints/produto_embalagem.py
# DESCRIÇÃO: Embalagens do produto (fardo, caixa, pack) — plano de embalagens, fase 1.
# ---------------------------------------------------------------------------
#
# Mesma permissão do cadastro de produto ("produto"). O PUT é replace-all: a
# tela manda a lista inteira de embalagens do produto, e o que não veio sai.
#
# Registrado ANTES de `produto.router` no api.py, pelo mesmo motivo das
# movimentações: os caminhos literais não podem cair no `/{produto_id}`.
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.core.depends import _handle_db_transaction, check_permission
from app.db.session import get_db
from app.schemas.produto_embalagem import EmbalagemRead, EmbalagensSalvar
from app.services import produto_embalagem as embalagem_service

router = APIRouter()

permissao_produto = check_permission(required_permission="produto")


@router.get(
    "/{produto_id}/embalagens",
    response_model=list[EmbalagemRead],
    summary="Listar as embalagens do produto",
)
def listar_embalagens(
    produto_id: int = Path(..., ge=1),
    user_token: dict = Depends(permissao_produto),
    db: Session = Depends(get_db),
):
    return embalagem_service.listar(db, produto_id)


@router.put(
    "/{produto_id}/embalagens",
    response_model=list[EmbalagemRead],
    summary="Salvar as embalagens do produto",
    description=(
        "Substitui a lista inteira. Código de barras único no sistema (409 se repetir o de um produto "
        "ou de outra embalagem). `gerar_codigo_interno` cria um EAN-13 interno (prefixo 29)."
    ),
)
def salvar_embalagens(
    dados: EmbalagensSalvar,
    produto_id: int = Path(..., ge=1),
    user_token: dict = Depends(permissao_produto),
    db: Session = Depends(get_db),
):
    return _handle_db_transaction(db, embalagem_service.salvar, produto_id, dados)
