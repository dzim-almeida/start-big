# ---------------------------------------------------------------------------
# ARQUIVO: endpoints/etiquetas.py
# DESCRIÇÃO: Central de Etiquetas — modelos de layout compartilhados pela loja.
# ---------------------------------------------------------------------------
#
# Não existe rota de "imprimir" aqui, de propósito: o backend roda no servidor
# da loja e a impressora de etiqueta está plugada no terminal de quem imprime.
# Quem renderiza e manda para a impressora é o terminal (docs/etiquetas-plano.md,
# decisão D11). Os dados dos produtos vêm da listagem de /produtos que já existe.
#
# Mesma permissão do Estoque ("produto"): quem cuida do estoque cuida das etiquetas.
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from app.core.depends import _handle_db_transaction, check_permission
from app.db.session import get_db
from app.schemas.modelo_etiqueta import ModeloEtiquetaCreate, ModeloEtiquetaRead, ModeloEtiquetaUpdate
from app.services import modelo_etiqueta as modelo_service

router = APIRouter()

permissao_estoque = check_permission(required_permission="produto")


@router.get(
    "/modelos",
    response_model=list[ModeloEtiquetaRead],
    summary="Listar modelos de etiqueta",
    description="Os modelos criados pela loja. Os presets de fábrica ficam no frontend.",
)
def listar_modelos(
    user_token: dict = Depends(permissao_estoque),
    db: Session = Depends(get_db),
):
    return modelo_service.listar_modelos(db, user_token["empresa_id"])


@router.post(
    "/modelos",
    response_model=ModeloEtiquetaRead,
    status_code=status.HTTP_201_CREATED,
    summary="Criar modelo de etiqueta",
)
def criar_modelo(
    dados: ModeloEtiquetaCreate,
    user_token: dict = Depends(permissao_estoque),
    db: Session = Depends(get_db),
):
    return _handle_db_transaction(db, modelo_service.criar_modelo, user_token["empresa_id"], dados)


@router.get(
    "/modelos/{modelo_id}",
    response_model=ModeloEtiquetaRead,
    summary="Detalhar modelo de etiqueta",
)
def obter_modelo(
    modelo_id: int = Path(..., ge=1),
    user_token: dict = Depends(permissao_estoque),
    db: Session = Depends(get_db),
):
    return modelo_service.obter_modelo(db, user_token["empresa_id"], modelo_id)


@router.put(
    "/modelos/{modelo_id}",
    response_model=ModeloEtiquetaRead,
    summary="Atualizar modelo de etiqueta",
    description="Substitui nome, fonte e definição inteiros.",
)
def atualizar_modelo(
    dados: ModeloEtiquetaUpdate,
    modelo_id: int = Path(..., ge=1),
    user_token: dict = Depends(permissao_estoque),
    db: Session = Depends(get_db),
):
    return _handle_db_transaction(
        db, modelo_service.atualizar_modelo, user_token["empresa_id"], modelo_id, dados
    )


@router.delete(
    "/modelos/{modelo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir modelo de etiqueta",
)
def excluir_modelo(
    modelo_id: int = Path(..., ge=1),
    user_token: dict = Depends(permissao_estoque),
    db: Session = Depends(get_db),
):
    _handle_db_transaction(db, modelo_service.deletar_modelo, user_token["empresa_id"], modelo_id)
