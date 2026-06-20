# ---------------------------------------------------------------------------
# ARQUIVO: endpoints/orcamento.py
# DESCRICAO: Endpoints para o modulo de Orcamentos.
#
# Estrutura de endpoints:
#   POST   /                                  -> Criar orcamento
#   PATCH  /{orcamento_id}                    -> Atualizar orcamento
#   POST   /{orcamento_id}/itens              -> Adicionar item
#   PATCH  /{orcamento_id}/itens/{item_id}    -> Editar item
#   DELETE /{orcamento_id}/itens/{item_id}    -> Remover item
#   DELETE /{orcamento_id}                    -> Excluir orcamento
#   POST   /{orcamento_id}/converter          -> Converter em venda
#   GET    /                                  -> Listar orcamentos
#   GET    /status/                           -> Resumo de status
#   GET    /{orcamento_id}                    -> Detalhe do orcamento
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.core.depends import check_permission, get_db, _handle_db_transaction
from app.schemas.orcamentos import (
    OrcamentoCreate,
    OrcamentoUpdate,
    OrcamentoRead,
    OrcamentoListRead,
    OrcamentoSearchFilters,
    OrcamentoStatusSummary,
    OrcamentoProdutoCreate,
    OrcamentoProdutoUpdate,
    OrcamentoProdutosAlterSummary,
    OrcamentoFinanceSummary,
    ConverterOrcamentoPayload,
)
from app.schemas.vendas import VendaRead

from app.services import orcamento as orcamento_service

router = APIRouter()

module_permission = ["venda", "view_sales", "manage_sales", "delete_sales"]


# ===========================================================================
# CRIACAO (POST /)
# ===========================================================================

@router.post(
    "/",
    response_model=OrcamentoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Orcamento",
    description="Cria um novo orcamento para simulacao de valores.",
)
def criar_orcamento(
    user_token: dict = Depends(check_permission(required_permission=module_permission)),
    *,
    db: Session = Depends(get_db),
    payload: OrcamentoCreate,
):
    return _handle_db_transaction(
        db,
        orcamento_service.create_orcamento,
        payload
    )


# ===========================================================================
# ATUALIZACAO GERAL (PATCH /{orcamento_id})
# ===========================================================================

@router.patch(
    "/{orcamento_id}",
    response_model=OrcamentoRead,
    summary="Atualizar Orcamento",
    description="Atualiza dados gerais do orcamento como entrega, desconto e observacao.",
)
def atualizar_orcamento(
    user_token: dict = Depends(check_permission(required_permission=module_permission)),
    *,
    db: Session = Depends(get_db),
    orcamento_id: int = Path(..., description="ID do orcamento"),
    payload: OrcamentoUpdate,
):
    return _handle_db_transaction(
        db,
        orcamento_service.update_orcamento,
        orcamento_id,
        payload
    )


# ===========================================================================
# ITENS DO ORCAMENTO
# ===========================================================================

@router.post(
    "/{orcamento_id}/itens",
    response_model=OrcamentoProdutosAlterSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Adicionar Item ao Orcamento",
    description="Insere um produto (cadastrado ou avulso) no orcamento.",
)
def adicionar_item(
    user_token: dict = Depends(check_permission(required_permission=module_permission)),
    *,
    db: Session = Depends(get_db),
    orcamento_id: int = Path(..., description="ID do orcamento"),
    payload: OrcamentoProdutoCreate,
):
    orcamento, product = _handle_db_transaction(
        db,
        orcamento_service.add_item_to_orcamento,
        orcamento_id,
        payload
    )
    return OrcamentoProdutosAlterSummary(
        produto_adicionado=product,
        financeiro_atualizado=OrcamentoFinanceSummary(
            subtotal=orcamento.subtotal or 0,
            descontos=orcamento.descontos or 0,
            entrega=orcamento.entrega or 0,
            total=orcamento.total or 0
        )
    )


@router.patch(
    "/{orcamento_id}/itens/{item_id}",
    response_model=OrcamentoProdutosAlterSummary,
    summary="Editar Item do Orcamento",
    description="Altera propriedades de um item do orcamento.",
)
def editar_item(
    user_token: dict = Depends(check_permission(required_permission=module_permission)),
    *,
    db: Session = Depends(get_db),
    orcamento_id: int = Path(..., description="ID do orcamento"),
    item_id: int = Path(..., description="ID do item"),
    payload: OrcamentoProdutoUpdate,
):
    orcamento, product = _handle_db_transaction(
        db,
        orcamento_service.update_item_in_orcamento,
        orcamento_id,
        item_id,
        payload
    )

    return OrcamentoProdutosAlterSummary(
        produto_adicionado=product,
        financeiro_atualizado=OrcamentoFinanceSummary(
            subtotal=orcamento.subtotal or 0,
            descontos=orcamento.descontos or 0,
            entrega=orcamento.entrega or 0,
            total=orcamento.total or 0
        )
    )


@router.delete(
    "/{orcamento_id}/itens/{item_id}",
    response_model=OrcamentoRead,
    status_code=status.HTTP_200_OK,
    summary="Remover Item do Orcamento",
    description="Exclui um produto do orcamento.",
)
def remover_item(
    user_token: dict = Depends(check_permission(required_permission=module_permission)),
    *,
    db: Session = Depends(get_db),
    orcamento_id: int = Path(..., description="ID do orcamento"),
    item_id: int = Path(..., description="ID do item"),
):
    return _handle_db_transaction(
        db,
        orcamento_service.remove_item_from_orcamento,
        orcamento_id,
        item_id
    )


# ===========================================================================
# ACOES DO ORCAMENTO
# ===========================================================================

@router.delete(
    "/{orcamento_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir Orcamento",
    description="Exclui permanentemente um orcamento nao convertido.",
)
def excluir_orcamento(
    user_token: dict = Depends(check_permission(required_permission=module_permission)),
    *,
    db: Session = Depends(get_db),
    orcamento_id: int = Path(..., description="ID do orcamento"),
):
    _handle_db_transaction(
        db,
        orcamento_service.delete_orcamento,
        orcamento_id
    )


@router.post(
    "/{orcamento_id}/converter",
    response_model=VendaRead,
    status_code=status.HTTP_201_CREATED,
    summary="Converter Orcamento em Venda",
    description="Cria uma nova venda a partir do orcamento, copiando todos os itens e valores.",
)
def converter_orcamento(
    user_token: dict = Depends(check_permission(required_permission=module_permission)),
    *,
    db: Session = Depends(get_db),
    orcamento_id: int = Path(..., description="ID do orcamento"),
    payload: ConverterOrcamentoPayload,
):
    return _handle_db_transaction(
        db,
        orcamento_service.converter_orcamento,
        orcamento_id,
        payload
    )


# ===========================================================================
# CONSULTAS
# ===========================================================================

@router.get(
    "/",
    response_model=OrcamentoListRead,
    summary="Listar Orcamentos",
    description="Retorna lista paginada de orcamentos com filtros.",
)
def listar_orcamentos(
    user_token: dict = Depends(check_permission(required_permission=module_permission)),
    *,
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100, description="Limite por pagina"),
    page: int = Query(1, ge=1, description="Pagina"),
    filters: OrcamentoSearchFilters = Depends()
):
    if not user_token.get("is_master"):
        filters.funcionario_id = user_token.get("funcionario_id")

    orcamentos, total, total_pages, links = orcamento_service.get_orcamentos(
        db, filters=filters, page=page, limit=limit
    )

    return OrcamentoListRead(
        filters=filters,
        orcamentos=orcamentos,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        links=links
    )


@router.get(
    "/status/",
    response_model=OrcamentoStatusSummary,
    status_code=status.HTTP_200_OK,
    summary="Resumo de Status dos Orcamentos",
    description="Fornece um resumo quantitativo dos orcamentos.",
)
def resumo_status_orcamentos(
    user_token: dict = Depends(check_permission(required_permission=module_permission)),
    *,
    db: Session = Depends(get_db),
):
    funcionario_id = None if user_token.get("is_master") else user_token.get("funcionario_id")
    return orcamento_service.get_orcamentos_status(db, funcionario_id=funcionario_id)


@router.get(
    "/{orcamento_id}",
    response_model=OrcamentoRead,
    summary="Obter Detalhes do Orcamento",
    description="Retorna os detalhes completos de um orcamento.",
)
def obter_detalhes_orcamento(
    user_token: dict = Depends(check_permission(required_permission=module_permission)),
    *,
    db: Session = Depends(get_db),
    orcamento_id: int = Path(..., description="ID do orcamento"),
):
    return orcamento_service.get_orcamento_by_id(db, orcamento_id)
