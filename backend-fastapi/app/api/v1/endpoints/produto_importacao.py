# ---------------------------------------------------------------------------
# ARQUIVO: endpoints/produto_importacao.py
# DESCRICAO: Importação de produtos por planilha Excel.
#
#   POST /estoque/importar-planilha/ler       → prévia (não grava)
#   POST /estoque/importar-planilha/importar  → cria os novos, tudo ou nada
#
# Permissão: a mesma do cadastro de produto ("produto").
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.core.depends import _handle_db_transaction, check_permission, get_db
from app.schemas.produto.importacao import PreviaImportacao, ResultadoImportacaoPlanilha
from app.services.produto import importacao_planilha as service

router = APIRouter()


@router.post("/ler", response_model=PreviaImportacao, summary="Confere a planilha de produtos (não grava)")
async def ler_planilha(
    arquivo: UploadFile = File(..., description="Planilha Excel .xlsx"),
    usuario_token: dict = Depends(check_permission(required_permission="produto")),
    db: Session = Depends(get_db),
):
    conteudo = await arquivo.read(service.TAMANHO_MAXIMO + 1)
    return service.ler(db, conteudo, usuario_token)


@router.post(
    "/importar",
    response_model=ResultadoImportacaoPlanilha,
    status_code=status.HTTP_201_CREATED,
    summary="Cria os produtos novos da planilha",
)
async def importar_planilha(
    arquivo: UploadFile = File(..., description="Planilha Excel .xlsx"),
    usuario_token: dict = Depends(check_permission(required_permission="produto")),
    db: Session = Depends(get_db),
):
    conteudo = await arquivo.read(service.TAMANHO_MAXIMO + 1)
    return _handle_db_transaction(db, service.importar, conteudo, usuario_token)
