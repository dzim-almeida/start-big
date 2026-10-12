# ---------------------------------------------------------------------------
# ARQUIVO: app/api/v1/endpoints/marcenaria_terceirizado.py
# DESCRICAO: API dos moveis terceirizados da OS da marcenaria (Spec 11A,
#            secao 6). Prefixo: /api/v1/marcenaria
#
# Esta camada so le o token e os parametros e aplica as permissoes. A regra
# fica em app/services/marcenaria/terceirizado.py. Tudo responde 404 fora da
# marcenaria (capacidade `orcamento_tecnico`) e em OS sem orcamento aprovado.
# ---------------------------------------------------------------------------

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.endpoints.marcenaria_orcamento import executar
from app.core.depends import check_permission
from app.core.modulos import requer_modulo
from app.db.session import get_db
from app.schemas.marcenaria.terceirizado import (
    EnviarManualEntrada,
    MoveisEntrada,
    PedidoCentralEntrada,
    ProblemaEntrada,
    ReceberManualEntrada,
)
from app.services.compras.permissoes import PERMISSOES_GERENCIAR as PERMISSOES_GERIR_COMPRAS
from app.services.marcenaria import terceirizado
from app.services.marcenaria import terceirizado_situacao as sit

router = APIRouter()

# D14: a secao fica numa aba da OS, entao vale a permissao de OS ("servico").
OS = Depends(check_permission(["servico"]))


@router.get("/os/{numero_os}/terceirizados", summary="Móveis terceirizados da OS")
def ler(numero_os: str, usuario_token: dict = OS, db: Session = Depends(get_db)):
    return executar(db, terceirizado.ler, numero_os, usuario_token)


@router.post(
    "/os/{numero_os}/terceirizados/pedir",
    summary="Pedir à central pelo Compras (pedido de serviço em rascunho)",
    # D10: o modulo COMPRAS contratado e a permissao de criar pedido do Compras,
    # alem da de OS. A trava comercial e a interna continuam as do Compras.
    dependencies=[Depends(requer_modulo("COMPRAS")), Depends(check_permission(PERMISSOES_GERIR_COMPRAS))],
)
def pedir(numero_os: str, dados: PedidoCentralEntrada, usuario_token: dict = OS, db: Session = Depends(get_db)):
    return executar(db, terceirizado.pedir, numero_os, dados, usuario_token)


@router.post("/os/{numero_os}/terceirizados/enviar-manual", summary="Sem o Compras: anotar o pedido à central")
def enviar_manual(numero_os: str, dados: EnviarManualEntrada, usuario_token: dict = OS,
                  db: Session = Depends(get_db)):
    return executar(db, terceirizado.enviar_manual, numero_os, dados, usuario_token)


@router.post("/os/{numero_os}/terceirizados/receber-manual", summary="Sem o Compras: anotar a chegada")
def receber_manual(numero_os: str, dados: ReceberManualEntrada, usuario_token: dict = OS,
                   db: Session = Depends(get_db)):
    return executar(db, terceirizado.receber_manual, numero_os, dados, usuario_token)


@router.post("/os/{numero_os}/terceirizados/conferir", summary="Conferir os móveis que chegaram")
def conferir(numero_os: str, dados: MoveisEntrada, usuario_token: dict = OS, db: Session = Depends(get_db)):
    return executar(db, terceirizado.conferir, numero_os, dados, usuario_token)


@router.post("/os/{numero_os}/terceirizados/{movel_id}/problema", summary="Registrar problema no móvel recebido")
def problema(numero_os: str, movel_id: int, dados: ProblemaEntrada, usuario_token: dict = OS,
             db: Session = Depends(get_db)):
    return executar(db, terceirizado.registrar_problema, numero_os, movel_id, dados, usuario_token)


@router.post("/os/{numero_os}/terceirizados/{movel_id}/voltar", summary="Voltar um passo")
def voltar(numero_os: str, movel_id: int, usuario_token: dict = OS, db: Session = Depends(get_db)):
    return executar(db, terceirizado.voltar, numero_os, movel_id, usuario_token)


@router.get("/terceirizados", summary="Terceirizados das OS abertas (atrasados primeiro)")
def lista_geral(
    situacao: Optional[str] = Query(None, pattern=f"^({'|'.join(sit.ORDEM)})$"),
    central_id: Optional[int] = Query(None, ge=1),
    atrasados: bool = Query(False),
    usuario_token: dict = OS,
    db: Session = Depends(get_db),
):
    return executar(db, terceirizado.lista_geral, usuario_token, situacao, central_id, atrasados)
