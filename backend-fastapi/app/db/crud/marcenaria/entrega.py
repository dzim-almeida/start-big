# ---------------------------------------------------------------------------
# ARQUIVO: app/db/crud/marcenaria/entrega.py
# DESCRICAO: Consultas da entrega e da agenda de instalacao (Spec 13A).
#
#            So SQL. O commit e a regra (OS aberta, situacao, avisos) ficam
#            nos servicos (app/services/marcenaria/entrega.py e agenda.py).
# ---------------------------------------------------------------------------

from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.marcenaria.entrega import MarcenariaAgendamento, MarcenariaEntrega, MarcenariaEntregaFoto
from app.db.models.marcenaria.orcamento import MarcenariaOrcamento, StatusOrcamento


def entregas_da_os(db: Session, os_id: int) -> list[MarcenariaEntrega]:
    """As entregas da OS, com pendencias, fotos e o ambiente (na ordem dos ambientes)."""
    entregas = db.scalars(
        select(MarcenariaEntrega)
        .where(MarcenariaEntrega.os_id == os_id)
        .options(
            selectinload(MarcenariaEntrega.ambiente),
            selectinload(MarcenariaEntrega.pendencias),
            selectinload(MarcenariaEntrega.fotos).selectinload(MarcenariaEntregaFoto.foto),
        )
    ).all()
    return sorted(entregas, key=lambda e: (e.ambiente.ordem, e.ambiente.id))


def entregas_das_os(db: Session, os_ids: list[int]) -> list[MarcenariaEntrega]:
    """As entregas de VARIAS OS numa consulta so (lista de instalacoes)."""
    if not os_ids:
        return []
    return list(db.scalars(
        select(MarcenariaEntrega)
        .where(MarcenariaEntrega.os_id.in_(os_ids))
        .options(selectinload(MarcenariaEntrega.ambiente))
    ).all())


def agendamentos_da_os(db: Session, os_id: int) -> list[MarcenariaAgendamento]:
    """Os agendamentos da OS, por data e hora (sem hora no fim do dia)."""
    agendamentos = db.scalars(select(MarcenariaAgendamento).where(MarcenariaAgendamento.os_id == os_id)).all()
    return sorted(agendamentos, key=lambda a: (a.data, a.hora_inicio or "99:99", a.id))


def agendamentos_no_periodo(db: Session, de: Optional[date], ate: Optional[date]) -> list[MarcenariaAgendamento]:
    """Os agendamentos entre as datas (as duas inclusas; sem data = sem limite). Usa o indice em `data`."""
    stmt = select(MarcenariaAgendamento)
    if de is not None:
        stmt = stmt.where(MarcenariaAgendamento.data >= de)
    if ate is not None:
        stmt = stmt.where(MarcenariaAgendamento.data <= ate)
    return list(db.scalars(stmt).all())


def orcamentos_aprovados_das_os(db: Session, os_ids: list[int]) -> dict[int, MarcenariaOrcamento]:
    """{os_id: orcamento aprovado} numa consulta so (cliente e endereco da obra)."""
    if not os_ids:
        return {}
    orcamentos = db.scalars(
        select(MarcenariaOrcamento)
        .where(MarcenariaOrcamento.os_id.in_(os_ids), MarcenariaOrcamento.status == StatusOrcamento.APROVADO)
        .options(selectinload(MarcenariaOrcamento.cliente), selectinload(MarcenariaOrcamento.objeto))
    ).all()
    return {orc.os_id: orc for orc in orcamentos}
