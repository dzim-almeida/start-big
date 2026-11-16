# ---------------------------------------------------------------------------
# ARQUIVO: app/services/lava_rapido/agenda.py
# DESCRICAO: Agenda do lava-rapido (docs/lava-rapido/ SPEC-00 O11, Spec 08A).
#
# So existe para segmento com a capacidade `agenda_servicos`. O agendamento
# nao e documento fiscal nem financeiro: e o lembrete de quem vem e quando.
# Quando o cliente chega, a tela abre a comanda preenchida e, criada a OS,
# marca o agendamento como CHEGOU com o numero dela.
# ---------------------------------------------------------------------------

from datetime import date, datetime, timezone
from typing import List

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import segmentos as reg
from app.core.tempo import intervalo_utc
from app.db.models.lava_rapido.agendamento import AGENDADO, CANCELADO, CHEGOU, Agendamento
from app.schemas.lava_rapido.agendamento import AgendamentoCreate, AgendamentoUpdate
from app.services.sistema.segmentos import get_segmento_atual


def _exigir_agenda(db: Session) -> None:
    if not reg.segmento_tem_capacidade(get_segmento_atual(db), reg.CAP_AGENDA_SERVICOS):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Agenda não disponível para este segmento.")


def _em_utc(instante: datetime) -> datetime:
    """Grava em UTC sem fuso, como toda data da casa. Sem fuso = ja e UTC."""
    if instante.tzinfo is not None:
        instante = instante.astimezone(timezone.utc).replace(tzinfo=None)
    return instante


def _ou_404(db: Session, agendamento_id: int) -> Agendamento:
    agendamento = db.get(Agendamento, agendamento_id)
    if agendamento is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agendamento não encontrado.")
    return agendamento


def listar(db: Session, inicio: date, fim: date) -> List[Agendamento]:
    """Agendamentos dos dias [inicio, fim] (dias da loja), na ordem da hora."""
    _exigir_agenda(db)
    if fim < inicio:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                            detail="O fim do período vem antes do início.")
    if (fim - inicio).days > 62:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                            detail="Período longo demais (máximo 2 meses).")
    de, ate = intervalo_utc(inicio, fim)
    return list(db.scalars(
        select(Agendamento)
        .where(Agendamento.inicio >= de, Agendamento.inicio <= ate)
        .order_by(Agendamento.inicio, Agendamento.id)
    ).all())


def criar(db: Session, dados: AgendamentoCreate) -> Agendamento:
    _exigir_agenda(db)
    valores = dados.model_dump()
    valores["inicio"] = _em_utc(dados.inicio)
    agendamento = Agendamento(**valores, situacao=AGENDADO)
    db.add(agendamento)
    db.flush()
    return agendamento


def atualizar(db: Session, agendamento_id: int, dados: AgendamentoUpdate) -> Agendamento:
    _exigir_agenda(db)
    agendamento = _ou_404(db, agendamento_id)
    mudancas = dados.model_dump(exclude_unset=True)

    # Atendido nao volta: a OS ja existe e e ela que conta daqui em diante.
    if agendamento.situacao == CHEGOU and mudancas.get("situacao", CHEGOU) != CHEGOU:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                            detail="Este agendamento já virou OS.")
    if mudancas.get("situacao") == CHEGOU and not (mudancas.get("numero_os") or agendamento.numero_os):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                            detail="Informe a OS aberta para marcar a chegada.")
    if "inicio" in mudancas and mudancas["inicio"] is not None:
        mudancas["inicio"] = _em_utc(mudancas["inicio"])
    if "servicos" in mudancas and mudancas["servicos"] is None:
        mudancas.pop("servicos")
    for campo, valor in mudancas.items():
        setattr(agendamento, campo, valor)
    db.flush()
    return agendamento


def excluir(db: Session, agendamento_id: int) -> None:
    """So agendamento cancelado sai da agenda de vez; os outros se cancelam."""
    _exigir_agenda(db)
    agendamento = _ou_404(db, agendamento_id)
    if agendamento.situacao != CANCELADO:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                            detail="Cancele o agendamento antes de excluir.")
    db.delete(agendamento)
    db.flush()
