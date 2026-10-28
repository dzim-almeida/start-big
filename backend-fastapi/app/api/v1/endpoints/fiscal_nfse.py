# ---------------------------------------------------------------------------
# ARQUIVO: api/v1/endpoints/fiscal_nfse.py
# DESCRIÇÃO: NFS-e (docs/nfse-plano.md). Na F1, só o lado do CADASTRO do
#            serviço: buscar o código de tributação nacional e o NBS. Nada
#            aqui emite.
#
# O router inteiro exige o módulo NFSE na licença (R1 do plano). Sem ele, a
# tela do serviço nem mostra os campos novos; quem chamar a rota direto recebe
# 403 MODULO_NAO_CONTRATADO.
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.depends import get_current_active_user, get_db
from app.core.modulos import requer_modulo
from app.services.fiscal.nfse import tabelas

router = APIRouter(dependencies=[Depends(requer_modulo("NFSE"))])


@router.get(
    "/servicos-nacionais",
    summary="Buscar Código de Tributação Nacional",
    description=(
        "Procura na lista de serviços nacional embarcada (Anexo B do portal da "
        "NFS-e). Aceita o código (com ou sem pontos) e a descrição — 'suporte "
        "informática'. Funciona sem internet."
    ),
)
def buscar_servicos_nacionais(
    user_token: dict = Depends(get_current_active_user),
    *,
    buscar: str = Query("", max_length=120),
    limite: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return {"resultados": tabelas.buscar_servicos_nacionais(db, buscar, limite)}


@router.get(
    "/nbs",
    summary="Buscar NBS",
    description=(
        "Com `codigo_tributacao_nacional`, devolve em `sugeridos` os NBS que a "
        "Receita correlaciona com ele (Anexo VIII). Com `buscar`, procura na "
        "tabela NBS inteira, pelo código ou pela descrição."
    ),
)
def buscar_nbs(
    user_token: dict = Depends(get_current_active_user),
    *,
    buscar: str = Query("", max_length=120),
    codigo_tributacao_nacional: str = Query("", max_length=10),
    limite: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return {
        "sugeridos": tabelas.nbs_sugeridos(db, codigo_tributacao_nacional),
        "resultados": tabelas.buscar_nbs(db, buscar, limite),
    }
