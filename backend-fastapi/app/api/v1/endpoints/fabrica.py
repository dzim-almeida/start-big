# ---------------------------------------------------------------------------
# ARQUIVO: endpoints/fabrica.py
# DESCRIÇÃO: Marcenaria-fábrica (docs/marcenaria-fabrica-plano.md).
#            F1: o produto como insumo (unidade de consumo × compra).
#            F2: orçamento por móvel, com versões, que gera a OS.
#            F3: o trilho (etapas, sinal, instalação) e a linha "Fábrica" de
#            Cargos: orçar/aprovar/liberar compra = Gerenciar; custo = Visualizar.
# ---------------------------------------------------------------------------
#
# O ROUTER INTEIRO só existe para o segmento Marcenaria (403
# SEGMENTO_SEM_FABRICA nos outros). O insumo pede a permissão do cadastro de
# produto; o orçamento, a da Ordem de Serviço. Prefixo próprio, como
# /compras: nada disto se mistura com as rotas que todo segmento usa.
# ---------------------------------------------------------------------------

from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.depends import _handle_db_transaction, check_permission
from app.core.segmentos.definicoes.marcenaria import SEGMENTO_MARCENARIA
from app.db.session import get_db
from app.schemas.fabrica import (
    Avancar,
    Instalacao,
    InsumoBusca,
    LiberarCompra,
    TrilhoRead,
    Voltar,
    InsumoEscrita,
    InsumoRead,
    MotivoRecusa,
    NovaVersao,
    OrcamentoEscrita,
    OrcamentoRead,
    OrcamentoResumo,
)
from app.services.fabrica import insumo as insumo_service
from app.services.fabrica import orcamentos as orcamentos_service
from app.services.fabrica import trilho as trilho_service
from app.services.fabrica.permissoes import (
    nome_do_usuario,
    permissao_gerenciar,
    permissao_os,
    pode_ver_custos,
)
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


# ---------------------------------------------------------------------------
# F2 — orçamento por móvel
# ---------------------------------------------------------------------------



@router.get(
    "/insumos",
    response_model=list[InsumoBusca],
    summary="Buscar insumo para a lista de material",
    description="Só produtos ativos marcados como insumo, por nome ou código. Busca vazia lista os primeiros.",
)
def buscar_insumos(
    busca: str = Query("", max_length=100),
    limite: int = Query(20, ge=1, le=50),
    user_token: Dict[str, Any] = Depends(permissao_os),
    db: Session = Depends(get_db),
):
    insumos = insumo_service.buscar(db, busca, limite)
    if not pode_ver_custos(user_token):
        for insumo in insumos:
            insumo.custo_unitario = None
    return insumos


@router.get(
    "/os/{numero_os}/orcamentos",
    response_model=list[OrcamentoResumo],
    summary="Versões do orçamento da OS",
    description="Da mais nova para a mais antiga. 409 se a OS não está no trilho da fábrica.",
)
def listar_orcamentos(
    numero_os: str = Path(..., max_length=20),
    user_token: Dict[str, Any] = Depends(permissao_os),
    db: Session = Depends(get_db),
):
    return orcamentos_service.listar(db, numero_os)


@router.post(
    "/os/{numero_os}/orcamentos",
    response_model=OrcamentoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Nova versão do orçamento",
    description="Vazia, ou cópia de outra versão desta OS (`copiar_de`).",
)
def criar_orcamento(
    dados: NovaVersao = Body(default_factory=NovaVersao),
    numero_os: str = Path(..., max_length=20),
    user_token: Dict[str, Any] = Depends(permissao_gerenciar),
    db: Session = Depends(get_db),
):
    return _handle_db_transaction(
        db, orcamentos_service.criar, numero_os, dados.copiar_de, nome_do_usuario(user_token)
    )


@router.get(
    "/orcamentos/{orcamento_id}",
    response_model=OrcamentoRead,
    summary="A árvore inteira de uma versão",
    description="Ambientes, móveis e materiais, com custos, totais, sinal e o que a aprovação vai escrever na OS.",
)
def obter_orcamento(
    orcamento_id: int = Path(..., ge=1),
    user_token: Dict[str, Any] = Depends(permissao_os),
    db: Session = Depends(get_db),
):
    return orcamentos_service.obter(db, orcamento_id, pode_ver_custos(user_token))


@router.put(
    "/orcamentos/{orcamento_id}",
    response_model=OrcamentoRead,
    summary="Salvar a árvore inteira (só RASCUNHO)",
    description="O que não vier sai. O servidor recalcula custos e totais; o custo de cada material é o do cadastro ao incluí-lo.",
)
def salvar_orcamento(
    dados: OrcamentoEscrita,
    orcamento_id: int = Path(..., ge=1),
    user_token: Dict[str, Any] = Depends(permissao_gerenciar),
    db: Session = Depends(get_db),
):
    return _handle_db_transaction(db, orcamentos_service.salvar, orcamento_id, dados)


@router.post(
    "/orcamentos/{orcamento_id}/enviar",
    response_model=OrcamentoRead,
    summary="Enviar a proposta ao cliente",
    description="RASCUNHO → ENVIADO. Exige ao menos um móvel e preço em todos.",
)
def enviar_orcamento(
    orcamento_id: int = Path(..., ge=1),
    user_token: Dict[str, Any] = Depends(permissao_gerenciar),
    db: Session = Depends(get_db),
):
    return _handle_db_transaction(db, orcamentos_service.enviar, orcamento_id, nome_do_usuario(user_token))


@router.post(
    "/orcamentos/{orcamento_id}/aprovar",
    response_model=OrcamentoRead,
    summary="O cliente aprovou: gera os itens da OS",
    description=(
        "ENVIADO → APROVADO. Escreve na OS um item por móvel (o preço) e um por insumo (chapas inteiras, com a "
        "perda), trocando os itens de uma aprovação anterior. Versão vencida não se aprova."
    ),
)
def aprovar_orcamento(
    orcamento_id: int = Path(..., ge=1),
    user_token: Dict[str, Any] = Depends(permissao_gerenciar),
    db: Session = Depends(get_db),
):
    return _handle_db_transaction(db, orcamentos_service.aprovar, orcamento_id, nome_do_usuario(user_token))


@router.post(
    "/orcamentos/{orcamento_id}/recusar",
    response_model=OrcamentoRead,
    summary="O cliente recusou",
    description="ENVIADO ou vencido → RECUSADO, com motivo.",
)
def recusar_orcamento(
    dados: MotivoRecusa,
    orcamento_id: int = Path(..., ge=1),
    user_token: Dict[str, Any] = Depends(permissao_gerenciar),
    db: Session = Depends(get_db),
):
    return _handle_db_transaction(
        db, orcamentos_service.recusar, orcamento_id, dados.motivo, nome_do_usuario(user_token)
    )


# ---------------------------------------------------------------------------
# F3 — o trilho
# ---------------------------------------------------------------------------


@router.get(
    "/os/{numero_os}/trilho",
    response_model=TrilhoRead,
    summary="Etapa atual, travas, sinal e histórico",
)
def obter_trilho(
    numero_os: str = Path(..., max_length=20),
    user_token: Dict[str, Any] = Depends(permissao_os),
    db: Session = Depends(get_db),
):
    return trilho_service.estado(db, numero_os)


def _e_devolve_o_trilho(db: Session, acao, numero_os: str, *args) -> TrilhoRead:
    acao(db, numero_os, *args)
    return trilho_service.estado(db, numero_os)


@router.post(
    "/os/{numero_os}/avancar",
    response_model=TrilhoRead,
    summary="Passar para a próxima etapa",
    description=(
        "Com pendência: 409 TRAVA_PENDENTE se as etapas travam; senão 422 MOTIVO_OBRIGATORIO até vir `motivo` "
        "(o log guarda o aviso ignorado). Enviar, aprovar e finalizar não passam por aqui."
    ),
)
def avancar_etapa(
    dados: Avancar = Body(default_factory=Avancar),
    numero_os: str = Path(..., max_length=20),
    user_token: Dict[str, Any] = Depends(permissao_os),
    db: Session = Depends(get_db),
):
    return _handle_db_transaction(
        db, _e_devolve_o_trilho, trilho_service.avancar, numero_os, nome_do_usuario(user_token), dados.motivo
    )


@router.post(
    "/os/{numero_os}/voltar",
    response_model=TrilhoRead,
    summary="Voltar para uma etapa anterior (com motivo)",
)
def voltar_etapa(
    dados: Voltar,
    numero_os: str = Path(..., max_length=20),
    user_token: Dict[str, Any] = Depends(permissao_os),
    db: Session = Depends(get_db),
):
    return _handle_db_transaction(
        db, _e_devolve_o_trilho, trilho_service.voltar, numero_os, dados.fase,
        nome_do_usuario(user_token), dados.motivo,
    )


@router.post(
    "/os/{numero_os}/liberar-compra",
    response_model=TrilhoRead,
    summary="Liberar a compra antes do sinal (gestor, com motivo)",
)
def liberar_compra(
    dados: LiberarCompra,
    numero_os: str = Path(..., max_length=20),
    user_token: Dict[str, Any] = Depends(permissao_gerenciar),
    db: Session = Depends(get_db),
):
    return _handle_db_transaction(
        db, _e_devolve_o_trilho, trilho_service.liberar_compra, numero_os,
        nome_do_usuario(user_token), dados.motivo,
    )


@router.put(
    "/os/{numero_os}/instalacao",
    response_model=TrilhoRead,
    summary="Marcar (ou desmarcar) a data de instalação",
    description="É por ela que a fila de Compras atende primeiro quem instala primeiro.",
)
def definir_instalacao(
    dados: Instalacao,
    numero_os: str = Path(..., max_length=20),
    user_token: Dict[str, Any] = Depends(permissao_os),
    db: Session = Depends(get_db),
):
    return _handle_db_transaction(
        db, _e_devolve_o_trilho, trilho_service.definir_instalacao, numero_os, dados.data_instalacao
    )
