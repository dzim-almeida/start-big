# ---------------------------------------------------------------------------
# ARQUIVO: crud/terminal_conectado.py
# DESCRIÇÃO: Queries SQL para a entidade TerminalConectado.
#            Segue o padrão flush-sem-commit (commit no caller).
# ---------------------------------------------------------------------------

from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models.terminal_conectado import TerminalConectado


def get_todos_terminais(db: Session) -> Sequence[TerminalConectado]:
    """Retorna todos os terminais conectados."""
    stmt = select(TerminalConectado)
    return db.scalars(stmt).all()


def get_terminal_by_hwid(db: Session, hwid: str) -> Optional[TerminalConectado]:
    """Busca terminal pelo HWID."""
    stmt = select(TerminalConectado).where(TerminalConectado.hwid == hwid)
    return db.scalars(stmt).first()


def create_terminal(db: Session, terminal: TerminalConectado) -> TerminalConectado:
    """Persiste um novo terminal. Flush sem commit."""
    db.add(terminal)
    db.flush()
    db.refresh(terminal)
    return terminal


def delete_terminal_by_hwid(db: Session, hwid: str) -> None:
    """Remove terminal pelo HWID. Flush sem commit."""
    stmt = delete(TerminalConectado).where(TerminalConectado.hwid == hwid)
    db.execute(stmt)
    db.flush()


def update_ultima_sinc(db: Session, terminal: TerminalConectado) -> TerminalConectado:
    """Atualiza o timestamp de última sincronização. Flush sem commit."""
    terminal.ultima_sinc = datetime.now(timezone.utc)
    db.flush()
    db.refresh(terminal)
    return terminal


def limpar_todos_terminais(db: Session) -> None:
    """Remove todos os terminais (usado no boot do servidor)."""
    stmt = delete(TerminalConectado)
    db.execute(stmt)
    db.flush()
