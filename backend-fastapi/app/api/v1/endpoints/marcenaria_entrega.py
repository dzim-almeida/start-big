# ---------------------------------------------------------------------------
# ARQUIVO: app/api/v1/endpoints/marcenaria_entrega.py
# DESCRICAO: API da entrega e da agenda de instalacao da marcenaria
#            (Spec 13A, secao 6). Prefixo: /api/v1/marcenaria
#
# Esta camada so le o token e os parametros e aplica a permissao. A regra
# fica em app/services/marcenaria/entrega.py e agenda.py. Tudo responde 404
# fora da marcenaria e em OS sem orcamento aprovado. Nenhum preco (P4).
# ---------------------------------------------------------------------------

from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.v1.endpoints.marcenaria_orcamento import executar
from app.core.depends import check_permission
from app.db.session import get_db
from app.schemas.marcenaria.entrega import (
    AgendamentoEntrada,
    ChecklistEntrada,
    PendenciaEntrada,
    RegistroEntrada,
    ResolverEntrada,
)
from app.services.marcenaria import agenda, entrega

router = APIRouter()

# D18: a entrega e uma ABA DA OS, entao vale a permissao de OS ("servico").
OS = Depends(check_permission(["servico"]))
BASE = "/os/{numero_os}/entrega"


@router.get(BASE, summary="Entrega da OS: um termo por ambiente, agendamentos e resumo")
def ler(numero_os: str, usuario_token: dict = OS, db: Session = Depends(get_db)):
    return executar(db, entrega.ler, numero_os)


@router.get(f"{BASE}/resumo", summary="Ambientes entregues e pendências abertas (aviso da finalização)")
def resumo(numero_os: str, usuario_token: dict = OS, db: Session = Depends(get_db)):
    return executar(db, entrega.resumo, numero_os)


@router.put(f"{BASE}/{{entrega_id}}/checklist", summary="Editar o checklist do ambiente")
def editar_checklist(numero_os: str, entrega_id: int, dados: ChecklistEntrada, usuario_token: dict = OS,
                     db: Session = Depends(get_db)):
    return executar(db, entrega.editar_checklist, numero_os, entrega_id, dados, usuario_token)


@router.post(f"{BASE}/{{entrega_id}}/registrar", summary="Registrar (ou corrigir) a entrega do ambiente")
def registrar(numero_os: str, entrega_id: int, dados: RegistroEntrada, usuario_token: dict = OS,
              db: Session = Depends(get_db)):
    return executar(db, entrega.registrar, numero_os, entrega_id, dados, usuario_token)


@router.post(f"{BASE}/{{entrega_id}}/pendencias", summary="Anotar uma pendência")
def criar_pendencia(numero_os: str, entrega_id: int, dados: PendenciaEntrada, usuario_token: dict = OS,
                    db: Session = Depends(get_db)):
    return executar(db, entrega.criar_pendencia, numero_os, entrega_id, dados, usuario_token)


@router.post(f"{BASE}/{{entrega_id}}/pendencias/{{pendencia_id}}/resolver", summary="Resolver uma pendência")
def resolver_pendencia(numero_os: str, entrega_id: int, pendencia_id: int, dados: ResolverEntrada,
                       usuario_token: dict = OS, db: Session = Depends(get_db)):
    return executar(db, entrega.resolver_pendencia, numero_os, entrega_id, pendencia_id, dados, usuario_token)


@router.post(f"{BASE}/{{entrega_id}}/pendencias/{{pendencia_id}}/reabrir", summary="Reabrir uma pendência")
def reabrir_pendencia(numero_os: str, entrega_id: int, pendencia_id: int, usuario_token: dict = OS,
                      db: Session = Depends(get_db)):
    return executar(db, entrega.reabrir_pendencia, numero_os, entrega_id, pendencia_id, usuario_token)


@router.post(f"{BASE}/{{entrega_id}}/fotos", summary="Foto do termo assinado ou da montagem")
def enviar_foto(
    numero_os: str,
    entrega_id: int,
    tipo: Literal["TERMO", "MONTAGEM"] = Form(..., description="TERMO (termo assinado) ou MONTAGEM"),
    arquivo: UploadFile = File(..., description="Imagem (JPEG, PNG, WEBP), como as fotos da OS"),
    usuario_token: dict = OS,
    db: Session = Depends(get_db),
):
    return executar(db, entrega.enviar_foto, numero_os, entrega_id, tipo, arquivo, usuario_token)


@router.delete(f"{BASE}/{{entrega_id}}/fotos/{{foto_id}}", summary="Excluir a foto (sai também da galeria da OS)")
def excluir_foto(numero_os: str, entrega_id: int, foto_id: int, usuario_token: dict = OS,
                 db: Session = Depends(get_db)):
    return executar(db, entrega.excluir_foto, numero_os, entrega_id, foto_id, usuario_token)


@router.post("/os/{numero_os}/agendamentos", summary="Agendar a instalação")
def agendar(numero_os: str, dados: AgendamentoEntrada, usuario_token: dict = OS, db: Session = Depends(get_db)):
    return executar(db, agenda.criar, numero_os, dados, usuario_token)


@router.put("/os/{numero_os}/agendamentos/{agendamento_id}", summary="Remarcar a instalação")
def editar_agendamento(numero_os: str, agendamento_id: int, dados: AgendamentoEntrada, usuario_token: dict = OS,
                       db: Session = Depends(get_db)):
    return executar(db, agenda.editar, numero_os, agendamento_id, dados, usuario_token)


@router.delete("/os/{numero_os}/agendamentos/{agendamento_id}", summary="Desmarcar a instalação")
def excluir_agendamento(numero_os: str, agendamento_id: int, usuario_token: dict = OS,
                        db: Session = Depends(get_db)):
    return executar(db, agenda.excluir, numero_os, agendamento_id, usuario_token)


@router.get("/instalacoes", summary="Quem instala onde: agendamentos por data")
def instalacoes(
    de: Optional[date] = Query(None, description="Primeiro dia (incluso)"),
    ate: Optional[date] = Query(None, description="Último dia (incluso)"),
    montador_id: Optional[int] = Query(None, ge=1),
    atrasadas: bool = Query(False, description="Só agendamentos vencidos com ambiente pendente"),
    usuario_token: dict = OS,
    db: Session = Depends(get_db),
):
    return executar(db, agenda.lista_instalacoes, de, ate, montador_id, atrasadas)
