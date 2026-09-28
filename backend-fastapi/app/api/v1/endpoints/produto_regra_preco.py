# ---------------------------------------------------------------------------
# ARQUIVO: endpoints/produto_regra_preco.py
# DESCRIÇÃO: Regras de preço por quantidade do produto (R2 faixas, R3 leve-pague).
# ---------------------------------------------------------------------------
#
# Mesma permissão do cadastro de produto ("produto"): o preço do produto é de
# quem cadastra o produto. LIGAR as regras na loja é das Configurações (G11).
#
# PUT replace-all, como as embalagens. Registrado ANTES de `produto.router` no
# api.py, pelo mesmo motivo delas.
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.core.depends import _handle_db_transaction, check_permission
from app.db.session import get_db
from app.schemas.produto_regra_preco import RegraPrecoRead, RegrasPrecoSalvar
from app.services import regras_preco as regras_service

router = APIRouter()

permissao_produto = check_permission(required_permission="produto")


@router.get(
    "/{produto_id}/regras-preco",
    response_model=list[RegraPrecoRead],
    summary="Listar as regras de preço por quantidade do produto",
)
def listar_regras(
    produto_id: int = Path(..., ge=1),
    user_token: dict = Depends(permissao_produto),
    db: Session = Depends(get_db),
):
    return regras_service.listar(db, produto_id)


@router.put(
    "/{produto_id}/regras-preco",
    response_model=list[RegraPrecoRead],
    summary="Salvar as regras de preço por quantidade do produto",
    description=(
        "Substitui a lista inteira. FAIXA = 'a partir de N un, R$ X cada' (R2); "
        "LEVE_PAGUE = 'leve X, pague Y' (R3). Só valem com a chave da regra ligada em Regras de Vendas."
    ),
)
def salvar_regras(
    dados: RegrasPrecoSalvar,
    produto_id: int = Path(..., ge=1),
    user_token: dict = Depends(permissao_produto),
    db: Session = Depends(get_db),
):
    return _handle_db_transaction(db, regras_service.salvar, produto_id, dados)
