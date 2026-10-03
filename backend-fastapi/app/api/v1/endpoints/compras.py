# ---------------------------------------------------------------------------
# ARQUIVO: endpoints/compras.py
# DESCRIÇÃO: Módulo de Compras (docs/compras-plano.md). Fase 1: fornecedores
#            do produto. Fase 2: necessidades e pedido de compra.
# ---------------------------------------------------------------------------
#
# Duas travas (ver services/compras/permissoes.py):
# - o ROUTER INTEIRO exige o módulo COMPRAS na licença (403
#   MODULO_NAO_CONTRATADO). Negado também sem resposta da licença (D2);
# - cada rota exige a caixa certa da linha "Compras" da tela de Cargos.
#
# Prefixo próprio (/compras), e não /produtos/{id}/fornecedores: o que é do
# módulo pago fica atrás de uma trava só, sem misturar com rotas do cadastro
# de produto, que todo mundo tem.
# ---------------------------------------------------------------------------

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.depends import _handle_db_transaction
from app.core.modulos import requer_modulo
from app.db.session import get_db
from app.schemas.compras import (
    FornecedorDoProdutoRead,
    FornecedoresDoProdutoSalvar,
    FornecedorResumo,
    GerarPedidos,
    MensagemFornecedor,
    MotivoEscrita,
    NecessidadeGrupo,
    ParcelaSimulada,
    PedidoDadosEscrita,
    PedidoEscrita,
    PedidoListagem,
    PedidoRead,
    PedidoResumo,
    RecebimentoEscrita,
    RelatorioCompras,
    ProdutoParaPedido,
    SimularParcelas,
)
from app.services.compras import fornecedores_produto as fornecedores_service
from app.services.compras import necessidades as necessidades_service
from app.services.compras import pedidos as pedidos_service
from app.services.compras.parcelas import gerar_parcelas
from app.services.compras import recebimentos as recebimentos_service
from app.services.compras import relatorios as relatorios_service
from app.services.compras.permissoes import (
    permissao_custos,
    permissao_cancelar,
    permissao_gerenciar,
    permissao_receber,
    permissao_ver,
    pode_ver_custos,
)

router = APIRouter(dependencies=[Depends(requer_modulo("COMPRAS"))])


@router.get(
    "/fornecedores",
    response_model=list[FornecedorResumo],
    summary="Fornecedores que vendem mercadoria",
    description="Ativos, sem transportadoras e entregadores. Para o seletor da aba Fornecedores do produto.",
)
def listar_fornecedores(
    user_token: dict = Depends(permissao_ver),
    db: Session = Depends(get_db),
):
    return fornecedores_service.listar_fornecedores_que_vendem(db)


@router.get(
    "/produtos",
    response_model=list[ProdutoParaPedido],
    summary="Buscar produto para pôr no pedido",
    description="Ativos e com estoque, por nome, código ou código de barras (inclui o da embalagem).",
)
def buscar_produtos(
    busca: str = Query("", max_length=100),
    limite: int = Query(20, ge=1, le=50),
    user_token: dict = Depends(permissao_ver),
    db: Session = Depends(get_db),
):
    return fornecedores_service.buscar_produtos(db, busca, limite)


@router.get(
    "/produtos/{produto_id}/fornecedores",
    response_model=list[FornecedorDoProdutoRead],
    summary="De quem a loja compra o produto",
    description="Inclui o fornecedor principal do cadastro mesmo sem linha própria (id nulo). Preços nulos sem permissão de custo.",
)
def listar_fornecedores_do_produto(
    produto_id: int = Path(..., ge=1),
    user_token: dict = Depends(permissao_ver),
    db: Session = Depends(get_db),
):
    return fornecedores_service.listar(db, produto_id, pode_ver_custos(user_token))


@router.put(
    "/produtos/{produto_id}/fornecedores",
    response_model=list[FornecedorDoProdutoRead],
    summary="Salvar os fornecedores do produto",
    description=(
        "Substitui a lista inteira (o que não vier é apagado). `padrao` torna o fornecedor o principal "
        "do produto. A embalagem manda no fator. Sem permissão de custo, o preço enviado é ignorado."
    ),
)
def salvar_fornecedores_do_produto(
    dados: FornecedoresDoProdutoSalvar,
    produto_id: int = Path(..., ge=1),
    user_token: dict = Depends(permissao_gerenciar),
    db: Session = Depends(get_db),
):
    return _handle_db_transaction(
        db, fornecedores_service.salvar, produto_id, dados, pode_ver_custos(user_token)
    )


# ---------------------------------------------------------------------------
# Fase 2 — necessidades e pedido de compra
# ---------------------------------------------------------------------------


@router.get(
    "/necessidades",
    response_model=list[NecessidadeGrupo],
    summary="O que precisa ser comprado",
    description=(
        "Produtos com estoque mínimo cadastrado e saldo + a caminho ≤ mínimo, agrupados pelo fornecedor "
        "sugerido, com a quantidade já na unidade de compra. Rascunhos não descontam, mas aparecem."
    ),
)
def listar_necessidades(
    base: str = Query(
        "MINIMO", pattern="^(MINIMO|VENDAS)$",
        description="MINIMO: só o estoque mínimo. VENDAS: também a média de venda dos últimos 90 dias",
    ),
    cobertura_dias: int = Query(30, ge=1, le=180, description="Com base VENDAS: para quantos dias comprar"),
    user_token: dict = Depends(permissao_ver),
    db: Session = Depends(get_db),
):
    return necessidades_service.listar(
        db, user_token, pode_ver_custos(user_token), base=base, cobertura_dias=cobertura_dias
    )


@router.post(
    "/necessidades/gerar-pedidos",
    response_model=list[PedidoResumo],
    status_code=status.HTTP_201_CREATED,
    summary="Gerar rascunhos a partir das necessidades",
    description="Um RASCUNHO por fornecedor, com o preço, a embalagem e o prazo do cadastro dele.",
)
def gerar_pedidos(
    dados: GerarPedidos,
    user_token: dict = Depends(permissao_gerenciar),
    db: Session = Depends(get_db),
):
    return _handle_db_transaction(
        db, necessidades_service.gerar_pedidos, user_token, dados, pode_ver_custos(user_token)
    )


@router.post(
    "/parcelas/simular",
    response_model=list[ParcelaSimulada],
    summary="Condição de pagamento → parcelas",
    description='"30/60/90" divide o total em 3; o resto dos centavos vai na última. Não grava nada.',
)
def simular_parcelas(
    dados: SimularParcelas,
    user_token: dict = Depends(permissao_ver),
):
    try:
        return [
            ParcelaSimulada(numero=p.numero, dias=p.dias, valor=p.valor)
            for p in gerar_parcelas(dados.total, dados.condicao)
        ]
    except ValueError as erro:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(erro))


@router.get("/pedidos", response_model=PedidoListagem, summary="Pedidos de compra")
def listar_pedidos(
    situacao: Optional[str] = Query(None, description="RASCUNHO, ENVIADO, PARCIAL, RECEBIDO ou CANCELADO"),
    fornecedor_id: Optional[int] = Query(None, ge=1),
    busca: Optional[str] = Query(None, max_length=100, description="Número (PC-12 ou 12) ou fornecedor"),
    a_receber: bool = Query(False, description="Só enviados e recebidos em parte (tela de Recebimento)"),
    atrasados: bool = Query(False, description="Só os a receber com a previsão de entrega já passada"),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_token: dict = Depends(permissao_ver),
    db: Session = Depends(get_db),
):
    return pedidos_service.listar(
        db, user_token, pode_ver_custos(user_token),
        situacao=situacao, fornecedor_id=fornecedor_id, busca=busca, a_receber=a_receber, atrasados=atrasados,
        limit=limit, offset=offset,
    )


@router.post(
    "/pedidos",
    response_model=PedidoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Criar pedido (rascunho)",
    description="Sem `parcelas`, elas são geradas pela condição de pagamento.",
)
def criar_pedido(
    dados: PedidoEscrita,
    user_token: dict = Depends(permissao_gerenciar),
    db: Session = Depends(get_db),
):
    return _handle_db_transaction(db, pedidos_service.criar, user_token, dados, pode_ver_custos(user_token))


@router.get("/pedidos/{pedido_id}", response_model=PedidoRead, summary="Pedido com itens, parcelas e histórico")
def obter_pedido(
    pedido_id: int = Path(..., ge=1),
    user_token: dict = Depends(permissao_ver),
    db: Session = Depends(get_db),
):
    return pedidos_service.obter(db, user_token, pedido_id, pode_ver_custos(user_token))


@router.put(
    "/pedidos/{pedido_id}",
    response_model=PedidoRead,
    summary="Substituir um rascunho inteiro",
    description="Só RASCUNHO. Enviado precisa voltar a rascunho (com motivo) antes.",
)
def atualizar_pedido(
    dados: PedidoEscrita,
    pedido_id: int = Path(..., ge=1),
    user_token: dict = Depends(permissao_gerenciar),
    db: Session = Depends(get_db),
):
    return _handle_db_transaction(
        db, pedidos_service.atualizar, user_token, pedido_id, dados, pode_ver_custos(user_token)
    )


@router.patch(
    "/pedidos/{pedido_id}",
    response_model=PedidoRead,
    summary="Mudar previsão de entrega e observação",
    description="Vale para RASCUNHO e ENVIADO — o fornecedor avisou que atrasa, por exemplo.",
)
def atualizar_dados_pedido(
    dados: PedidoDadosEscrita,
    pedido_id: int = Path(..., ge=1),
    user_token: dict = Depends(permissao_gerenciar),
    db: Session = Depends(get_db),
):
    return _handle_db_transaction(
        db, pedidos_service.atualizar_dados, user_token, pedido_id, dados, pode_ver_custos(user_token)
    )


@router.post("/pedidos/{pedido_id}/enviar", response_model=PedidoRead, summary="Marcar como enviado ao fornecedor")
def enviar_pedido(
    pedido_id: int = Path(..., ge=1),
    user_token: dict = Depends(permissao_gerenciar),
    db: Session = Depends(get_db),
):
    return _handle_db_transaction(db, pedidos_service.enviar, user_token, pedido_id, pode_ver_custos(user_token))


@router.post(
    "/pedidos/{pedido_id}/voltar-rascunho",
    response_model=PedidoRead,
    summary="Voltar um enviado a rascunho (com motivo)",
)
def voltar_pedido_rascunho(
    dados: MotivoEscrita,
    pedido_id: int = Path(..., ge=1),
    user_token: dict = Depends(permissao_gerenciar),
    db: Session = Depends(get_db),
):
    return _handle_db_transaction(
        db, pedidos_service.voltar_rascunho, user_token, pedido_id, dados.motivo, pode_ver_custos(user_token)
    )


@router.post(
    "/pedidos/{pedido_id}/cancelar",
    response_model=PedidoRead,
    summary="Cancelar o pedido (com motivo)",
    description="Caixa Excluir da linha Compras. Fica no histórico; nada é apagado.",
)
def cancelar_pedido(
    dados: MotivoEscrita,
    pedido_id: int = Path(..., ge=1),
    user_token: dict = Depends(permissao_cancelar),
    db: Session = Depends(get_db),
):
    return _handle_db_transaction(
        db, pedidos_service.cancelar, user_token, pedido_id, dados.motivo, pode_ver_custos(user_token)
    )


@router.get(
    "/pedidos/{pedido_id}/whatsapp",
    response_model=MensagemFornecedor,
    summary="Texto do pedido para mandar por WhatsApp",
)
def mensagem_pedido(
    pedido_id: int = Path(..., ge=1),
    user_token: dict = Depends(permissao_ver),
    db: Session = Depends(get_db),
):
    return pedidos_service.mensagem_whatsapp(db, user_token, pedido_id, pode_ver_custos(user_token))


# ---------------------------------------------------------------------------
# Fase 3 — recebimento
# ---------------------------------------------------------------------------


@router.post(
    "/pedidos/{pedido_id}/recebimentos",
    response_model=PedidoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Dar entrada no que chegou",
    description=(
        "Entrada no estoque (origem COMPRA) com o custo real, pedido PARCIAL/RECEBIDO, último preço do "
        "fornecedor e, com o Financeiro, as contas a pagar proporcionais. Quem só recebe não muda custo."
    ),
)
def receber_pedido(
    dados: RecebimentoEscrita,
    pedido_id: int = Path(..., ge=1),
    user_token: dict = Depends(permissao_receber),
    db: Session = Depends(get_db),
):
    return _handle_db_transaction(
        db, recebimentos_service.receber, user_token, pedido_id, dados, pode_ver_custos(user_token)
    )


@router.post(
    "/pedidos/{pedido_id}/encerrar",
    response_model=PedidoRead,
    summary="Encerrar o saldo de um pedido recebido em parte",
    description="O resto não vem mais: o pedido fica RECEBIDO e o saldo, cancelado. Motivo no histórico.",
)
def encerrar_pedido(
    dados: MotivoEscrita,
    pedido_id: int = Path(..., ge=1),
    user_token: dict = Depends(permissao_receber),
    db: Session = Depends(get_db),
):
    return _handle_db_transaction(
        db, recebimentos_service.encerrar_saldo, user_token, pedido_id, dados.motivo, pode_ver_custos(user_token)
    )


# ---------------------------------------------------------------------------
# Fase 5 — relatórios
# ---------------------------------------------------------------------------


@router.get(
    "/relatorios",
    response_model=RelatorioCompras,
    summary="Fornecedores (prazo, pontualidade, valor) e variação de preço",
    description="Exige ver custo (linha Compras); quem só recebe não acessa.",
)
def relatorio_compras(
    inicio: date = Query(..., description="Primeiro dia do período"),
    fim: date = Query(..., description="Último dia do período"),
    user_token: dict = Depends(permissao_custos),
    db: Session = Depends(get_db),
):
    if fim < inicio:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "O fim do período é antes do início.")
    if (fim - inicio).days > 366:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Período de no máximo um ano.")
    return relatorios_service.gerar(db, user_token, inicio, fim)
