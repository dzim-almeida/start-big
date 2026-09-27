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
# Modelos: mesma permissão do Estoque ("produto"). Envio: ver o bloco no fim.
# ---------------------------------------------------------------------------

from typing import Optional

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.core.depends import _handle_db_transaction, check_permission
from app.db.session import get_db
from app.schemas.modelo_etiqueta import ModeloEtiquetaCreate, ModeloEtiquetaRead, ModeloEtiquetaUpdate
from app.schemas.etiqueta_envio import DadosEnvio, OrigemEnvioItem, ParteEnvio
from app.services import etiqueta_envio as envio_service
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


# ---------------------------------------------------------------------------
# ENVIO (fase 5): etiquetas de volume e DANFE Simplificado
# ---------------------------------------------------------------------------
#
# Os dados saem prontos (remetente, destinatário, NF-e autorizada). Cada tipo
# de origem exige a permissão do seu módulo — ver services/etiqueta_envio.py.

permissao_envio = check_permission(
    required_permission=["produto", *envio_service.PERMISSOES_OS, *envio_service.PERMISSOES_VENDA]
)


@router.get(
    "/envio/origens",
    response_model=list[OrigemEnvioItem],
    summary="Buscar OS e vendas para etiqueta de envio",
    description="As mais recentes primeiro, por número, cliente ou identificador. Só os tipos que o usuário pode ver.",
)
def buscar_origens_envio(
    busca: Optional[str] = Query(None, max_length=100),
    user_token: dict = Depends(permissao_envio),
    db: Session = Depends(get_db),
):
    return envio_service.buscar_origens(db, user_token, busca)


@router.get("/envio/os/{os_id}", response_model=DadosEnvio, summary="Dados de envio de uma OS")
def dados_envio_os(
    os_id: int = Path(..., ge=1),
    user_token: dict = Depends(permissao_envio),
    db: Session = Depends(get_db),
):
    return envio_service.dados_os(db, user_token, os_id)


@router.get("/envio/venda/{venda_id}", response_model=DadosEnvio, summary="Dados de envio de uma venda")
def dados_envio_venda(
    venda_id: int = Path(..., ge=1),
    user_token: dict = Depends(permissao_envio),
    db: Session = Depends(get_db),
):
    return envio_service.dados_venda(db, user_token, venda_id)


@router.get("/envio/remetente", response_model=ParteEnvio, summary="Remetente (a empresa) para etiqueta avulsa")
def remetente_envio(
    user_token: dict = Depends(permissao_envio),
    db: Session = Depends(get_db),
):
    return envio_service.remetente(db, user_token)
