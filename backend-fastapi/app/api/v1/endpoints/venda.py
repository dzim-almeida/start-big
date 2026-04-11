# ---------------------------------------------------------------------------
# ARQUIVO: endpoints/venda.py
# DESCRICAO: Endpoints mockados para o módulo de Vendas (PDV).
#
# IMPORTANTE — Ordem de declaração das rotas:
#   Rotas com paths estáticos DEVEM ser declaradas ANTES de rotas com
#   path parameters, pois FastAPI resolve rotas em ordem de declaração.
#
# Estrutura de endpoints:
#   POST   /                              → Criar rascunho de venda
#   PATCH  /{venda_id}                    → Atualizar dados gerais da venda
#   POST   /{venda_id}/itens              → Adicionar item ao carrinho
#   PATCH  /{venda_id}/itens/{item_id}    → Editar item do carrinho
#   DELETE /{venda_id}/itens/{item_id}    → Remover item do carrinho
#   POST   /{venda_id}/cancelar           → Cancelar venda
#   POST   /{venda_id}/finalizar          → Finalizar venda (checkout)
# ---------------------------------------------------------------------------

from datetime import datetime

from fastapi import APIRouter, Depends, Path, Response, status

from app.core.depends import check_permission
from app.core.enum import TipoProdutoVenda, VendaStatus
from app.schemas.vendas import (
    AddProdutoVendaRead,
    FinalizarVendaPayload,
    PagamentoVendaRead,
    ProdutoVendaCreate,
    ProdutoVendaRead,
    ProdutoVendaUpdate,
    VendaCreate,
    VendaRead,
    VendaResumoFinanceiro,
    VendaUpdate,
)

router = APIRouter()

module_permission = "venda"


# ---------------------------------------------------------------------------
# Helpers para gerar dados mockados
# ---------------------------------------------------------------------------

def _mock_resumo_financeiro(subtotal: int = 5000, entrega: int = 0, desconto: int = 0, adiantamento: int = 0) -> VendaResumoFinanceiro:
    return VendaResumoFinanceiro(
        subtotal=subtotal,
        entrega=entrega,
        desconto=desconto,
        adiantamento=adiantamento,
        total=subtotal + entrega - desconto - adiantamento,
    )


def _mock_produto_read(item_id: int = 1, produto: ProdutoVendaCreate | None = None) -> ProdutoVendaRead:
    if produto:
        subtotal = produto.quantidade * produto.valor_unitario - produto.desconto
        return ProdutoVendaRead(
            id=item_id,
            tipo_produto=produto.tipo_produto,
            produto_id=produto.produto_id,
            quantidade=produto.quantidade,
            descricao_avulsa=produto.descricao_avulsa,
            valor_unitario=produto.valor_unitario,
            desconto=produto.desconto,
            subtotal=subtotal,
        )
    return ProdutoVendaRead(
        id=item_id,
        tipo_produto=TipoProdutoVenda.CADASTRADO,
        produto_id=1,
        quantidade=2,
        descricao_avulsa=None,
        valor_unitario=2500,
        desconto=0,
        subtotal=5000,
    )


def _mock_venda_read(
    venda_id: int = 1,
    status_venda: VendaStatus = VendaStatus.RASCUNHO,
    cliente_id: int | None = None,
    funcionario_id: int = 1,
    produtos: list[ProdutoVendaRead] | None = None,
    pagamentos: list[PagamentoVendaRead] | None = None,
    entrega: int = 0,
    desconto: int = 0,
    adiantamento: int = 0,
    observacao: str | None = None,
) -> VendaRead:
    now = datetime.now()
    prods = produtos or []
    pags = pagamentos or []
    subtotal = sum(p.subtotal for p in prods)
    total = subtotal + entrega - desconto - adiantamento
    return VendaRead(
        id=venda_id,
        cliente_id=cliente_id,
        funcionario_id=funcionario_id,
        sessao_caixa_id=None,
        entrega=entrega,
        subtotal=subtotal,
        desconto=desconto,
        adiantamento=adiantamento,
        total=max(total, 0),
        status=status_venda,
        observacao=observacao,
        criado_em=now,
        atualizado_em=now,
        produtos=prods,
        pagamentos=pags,
    )


# ===========================================================================
# CRIAÇÃO (POST /)
# ===========================================================================

@router.post(
    "/",
    response_model=VendaRead,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Rascunho de Venda",
    description=(
        "Cria uma nova venda no status RASCUNHO, gerando o ID identificador "
        "do carrinho para adição posterior de itens e pagamentos."
    ),
)
def criar_venda(
    user_token: dict = Depends(check_permission(required_permission=module_permission)),
    *,
    payload: VendaCreate,
):
    return _mock_venda_read(
        cliente_id=payload.cliente_id,
        funcionario_id=payload.funcionario_id,
    )


# ===========================================================================
# ATUALIZAÇÃO GERAL (PATCH /{venda_id})
# ===========================================================================

@router.patch(
    "/{venda_id}",
    response_model=VendaRead,
    summary="Atualizar Dados Gerais da Venda",
    description=(
        "Permite vincular/alterar o cliente, aplicar descontos globais, "
        "registrar frete (entrega) ou valores de adiantamento."
    ),
)
def atualizar_venda(
    user_token: dict = Depends(check_permission(required_permission=module_permission)),
    *,
    venda_id: int = Path(..., description="ID da venda"),
    payload: VendaUpdate,
):
    return _mock_venda_read(
        venda_id=venda_id,
        cliente_id=payload.cliente_id,
        funcionario_id=payload.funcionario_id or 1,
        entrega=payload.entrega or 0,
        desconto=payload.desconto or 0,
        adiantamento=payload.adiantamento or 0,
        observacao=payload.observacao,
    )


# ===========================================================================
# ITENS DO CARRINHO
# ===========================================================================

@router.post(
    "/{venda_id}/itens",
    response_model=AddProdutoVendaRead,
    status_code=status.HTTP_201_CREATED,
    summary="Adicionar Item ao Carrinho",
    description=(
        "Insere um produto (cadastrado ou avulso) na venda. "
        "Retorna o produto adicionado junto com o resumo financeiro atualizado."
    ),
)
def adicionar_item(
    user_token: dict = Depends(check_permission(required_permission=module_permission)),
    *,
    venda_id: int = Path(..., description="ID da venda"),
    payload: ProdutoVendaCreate,
):
    produto_mock = _mock_produto_read(item_id=1, produto=payload)
    return AddProdutoVendaRead(
        produto_adicionado=produto_mock,
        resumo_financeiro=_mock_resumo_financeiro(subtotal=produto_mock.subtotal),
    )


@router.patch(
    "/{venda_id}/itens/{item_id}",
    response_model=AddProdutoVendaRead,
    summary="Editar Item do Carrinho",
    description=(
        "Altera propriedades de um produto já adicionado, como quantidade, "
        "desconto específico ou descrição de produtos avulsos."
    ),
)
def editar_item(
    user_token: dict = Depends(check_permission(required_permission=module_permission)),
    *,
    venda_id: int = Path(..., description="ID da venda"),
    item_id: int = Path(..., description="ID do item no carrinho"),
    payload: ProdutoVendaUpdate,
):
    produto_mock = _mock_produto_read(item_id=item_id)
    if payload.quantidade is not None:
        produto_mock.quantidade = payload.quantidade
    if payload.valor_unitario is not None:
        produto_mock.valor_unitario = payload.valor_unitario
    if payload.desconto is not None:
        produto_mock.desconto = payload.desconto
    if payload.descricao_avulsa is not None:
        produto_mock.descricao_avulsa = payload.descricao_avulsa
    produto_mock.subtotal = produto_mock.quantidade * produto_mock.valor_unitario - produto_mock.desconto

    return AddProdutoVendaRead(
        produto_adicionado=produto_mock,
        resumo_financeiro=_mock_resumo_financeiro(subtotal=produto_mock.subtotal),
    )


@router.delete(
    "/{venda_id}/itens/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover Item do Carrinho",
    description="Exclui o produto do rascunho da venda.",
)
def remover_item(
    user_token: dict = Depends(check_permission(required_permission=module_permission)),
    *,
    venda_id: int = Path(..., description="ID da venda"),
    item_id: int = Path(..., description="ID do item no carrinho"),
):
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ===========================================================================
# AÇÕES DA VENDA (cancelar / finalizar)
# ===========================================================================

@router.post(
    "/{venda_id}/cancelar",
    response_model=VendaRead,
    summary="Cancelar Venda",
    description=(
        "Invalida o rascunho ou a venda em andamento, interrompendo o fluxo "
        "e descartando qualquer reserva de estoque provisória."
    ),
)
def cancelar_venda(
    user_token: dict = Depends(check_permission(required_permission=module_permission)),
    *,
    venda_id: int = Path(..., description="ID da venda"),
):
    return _mock_venda_read(
        venda_id=venda_id,
        status_venda=VendaStatus.CANCELADA,
    )


@router.post(
    "/{venda_id}/finalizar",
    response_model=VendaRead,
    summary="Finalizar Venda (Checkout)",
    description=(
        "Recebe os pagamentos e valida se a soma cobre o total financeiro. "
        "Caso positivo, efetua a baixa de estoque e muda o status para CONCLUIDA."
    ),
)
def finalizar_venda(
    user_token: dict = Depends(check_permission(required_permission=module_permission)),
    *,
    venda_id: int = Path(..., description="ID da venda"),
    payload: FinalizarVendaPayload,
):
    now = datetime.now()
    pagamentos_mock = [
        PagamentoVendaRead(
            id=idx + 1,
            forma_pagamento_id=p.forma_pagamento_id,
            parcelado=p.parcelado,
            qtd_parcelas=p.qtd_parcelas,
            valor=p.valor,
            data_pagamento=now,
        )
        for idx, p in enumerate(payload.pagamentos)
    ]
    total_pago = sum(p.valor for p in payload.pagamentos)
    produto_mock = _mock_produto_read()

    return _mock_venda_read(
        venda_id=venda_id,
        status_venda=VendaStatus.CONCLUIDA,
        produtos=[produto_mock],
        pagamentos=pagamentos_mock,
    )
