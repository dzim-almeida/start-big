# ---------------------------------------------------------------------------
# ARQUIVO: endpoints/nfe_entrada.py
# DESCRICAO: Entrada de mercadoria pela XML da NF-e do fornecedor.
#
#   POST /estoque/nfe-entrada/ler       → prévia (não grava)
#   POST /estoque/nfe-entrada/importar  → grava tudo numa transação
#   GET  /estoque/nfe-entrada           → notas já importadas
#
# Permissão: a mesma da entrada manual de estoque ("produto").
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.depends import _handle_db_transaction, check_permission, get_db
from app.schemas.nfe_entrada import ImportarNota, NotaEntradaRead, NotaPrevia, ResultadoImportacao
from app.services import nfe_entrada as service

router = APIRouter()


@router.post("/ler", response_model=NotaPrevia, summary="Lê a XML da NF-e e sugere a entrada (não grava)")
async def ler_nota(
    arquivo: UploadFile = File(..., description="XML da NF-e do fornecedor"),
    usuario_token: dict = Depends(check_permission(required_permission="produto")),
    db: Session = Depends(get_db),
):
    conteudo = await arquivo.read(service.TAMANHO_MAXIMO + 1)
    return service.ler(db, conteudo, usuario_token)


@router.post(
    "/importar",
    response_model=ResultadoImportacao,
    status_code=status.HTTP_201_CREATED,
    summary="Dá entrada na NF-e: estoque, custo, produtos novos e contas a pagar",
)
def importar_nota(
    dados: ImportarNota,
    usuario_token: dict = Depends(check_permission(required_permission="produto")),
    db: Session = Depends(get_db),
):
    return _handle_db_transaction(db, service.importar, dados, usuario_token)


@router.get("", response_model=list[NotaEntradaRead], summary="Notas de compra já importadas")
def listar_notas(
    limite: int = Query(50, ge=1, le=200),
    usuario_token: dict = Depends(check_permission(required_permission="produto")),
    db: Session = Depends(get_db),
):
    return service.listar(db, usuario_token, limite)
