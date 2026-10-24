# ---------------------------------------------------------------------------
# ARQUIVO: app/api/v1/endpoints/marcenaria_faturamento.py
# DESCRICAO: API do faturamento dos moveis (docs/marcenaria-faturamento-plano.md).
#            Prefixo: /api/v1/marcenaria
#
# Esta camada so le o token e os parametros e aplica a permissao. A regra fica
# em app/services/marcenaria/faturamento/ e app/services/fiscal/emissoes/nfe_marcenaria.py.
# A emissao usa a mesma porta da NF-e (`requer_modulo_fiscal`: modulo NFE
# contratado e fiscal configurado).
# ---------------------------------------------------------------------------

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.v1.endpoints.marcenaria_orcamento import executar
from app.core.depends import check_permission, requer_modulo_fiscal
from app.db.session import get_db
from app.schemas.fiscal.emissao import EmissaoResponse
from app.services.marcenaria.faturamento import estoque_acabado, painel
from app.services.marcenaria.permissoes import PERMISSOES_GERIR_CUSTOS

router = APIRouter()

# A leitura e uma aba da OS: vale a permissao de OS ("servico"), como a producao.
OS = Depends(check_permission(["servico"]))


class MoveisDaNota(BaseModel):
    """Os moveis que saem nesta nota (os de uma entrega)."""
    movel_ids: list[int] = Field(..., min_length=1, max_length=200)


# ===========================================================================
# ESTOQUE DE ACABADOS (F2)
# ===========================================================================

def _sincronizar_todas(db: Session, usuario_token: dict) -> dict:
    resposta = estoque_acabado.sincronizar_todas(db, usuario_token)
    db.commit()
    return resposta


@router.post(
    "/faturamento/sincronizar",
    summary="Dar entrada dos móveis já prontos (OS abertas)",
    description=(
        "Ao ligar o faturamento com obras em andamento: todo móvel aprovado que já está pronto "
        "entra no estoque como produto acabado. Idempotente. Exige 'manage_custos_marcenaria'."
    ),
)
def sincronizar(
    usuario_token: dict = Depends(check_permission(required_permission=PERMISSOES_GERIR_CUSTOS)),
    db: Session = Depends(get_db),
):
    return executar(db, _sincronizar_todas, usuario_token)


# ===========================================================================
# A NOTA DE UMA ENTREGA (F3)
# ===========================================================================

@router.get("/os/{numero_os}/faturamento", summary="Faturamento dos móveis da OS")
def ler_faturamento(numero_os: str, usuario_token: dict = OS, db: Session = Depends(get_db)):
    return executar(db, painel.ler, numero_os)


@router.post("/os/{numero_os}/faturamento/preview", summary="Prévia da NF-e dos móveis escolhidos")
def preview(numero_os: str, dados: MoveisDaNota, usuario_token: dict = Depends(requer_modulo_fiscal),
            db: Session = Depends(get_db)):
    from app.services.fiscal.emissoes.nfe_marcenaria import preview_nfe_marcenaria

    return executar(db, preview_nfe_marcenaria, numero_os, usuario_token["empresa_id"], dados.movel_ids)


def _emitir(db: Session, numero_os: str, empresa_id: int, movel_ids: list[int], usuario_token: dict):
    from app.services.fiscal.emissoes.nfe_marcenaria import emitir_nfe_marcenaria

    doc = emitir_nfe_marcenaria(db, numero_os, empresa_id, movel_ids, usuario_token)
    db.commit()
    return doc


@router.post("/os/{numero_os}/faturamento/emitir", response_model=EmissaoResponse,
             summary="Emitir a NF-e dos móveis escolhidos (uma entrega)")
def emitir(numero_os: str, dados: MoveisDaNota, background_tasks: BackgroundTasks,
           usuario_token: dict = Depends(requer_modulo_fiscal), db: Session = Depends(get_db)):
    from app.services.fiscal.emissao import poll_nfe_status_async

    empresa_id = usuario_token["empresa_id"]
    doc = executar(db, _emitir, numero_os, empresa_id, dados.movel_ids, usuario_token)
    if doc.status == "PROCESSANDO":
        background_tasks.add_task(poll_nfe_status_async, doc.id, empresa_id)
    return EmissaoResponse.de_documento(doc, "NF-e")


# ===========================================================================
# ENTREGA FUTURA: O SIMPLES FATURAMENTO DA OS (F4)
# ===========================================================================

@router.post("/os/{numero_os}/faturamento/simples-faturamento/preview",
             summary="Prévia da nota de simples faturamento (entrega futura)")
def preview_simples_faturamento(numero_os: str, usuario_token: dict = Depends(requer_modulo_fiscal),
                                db: Session = Depends(get_db)):
    from app.services.fiscal.emissoes.nfe_marcenaria import SIMPLES_FATURAMENTO, preview_nfe_marcenaria

    return executar(db, preview_nfe_marcenaria, numero_os, usuario_token["empresa_id"], None, SIMPLES_FATURAMENTO)


def _emitir_simples_faturamento(db: Session, numero_os: str, empresa_id: int, usuario_token: dict):
    from app.services.fiscal.emissoes.nfe_marcenaria import SIMPLES_FATURAMENTO, emitir_nfe_marcenaria

    doc = emitir_nfe_marcenaria(db, numero_os, empresa_id, None, usuario_token, SIMPLES_FATURAMENTO)
    db.commit()
    return doc


@router.post("/os/{numero_os}/faturamento/simples-faturamento/emitir", response_model=EmissaoResponse,
             summary="Emitir a nota de simples faturamento (entrega futura)",
             description="Todos os móveis aprovados ainda sem simples faturamento (o aditivo ganha o seu).")
def emitir_simples_faturamento(numero_os: str, background_tasks: BackgroundTasks,
                               usuario_token: dict = Depends(requer_modulo_fiscal), db: Session = Depends(get_db)):
    from app.services.fiscal.emissao import poll_nfe_status_async

    empresa_id = usuario_token["empresa_id"]
    doc = executar(db, _emitir_simples_faturamento, numero_os, empresa_id, usuario_token)
    if doc.status == "PROCESSANDO":
        background_tasks.add_task(poll_nfe_status_async, doc.id, empresa_id)
    return EmissaoResponse.de_documento(doc, "NF-e")
