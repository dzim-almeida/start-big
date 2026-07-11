# ---------------------------------------------------------------------------
# ARQUIVO: app/db/models/terminal_conectado.py
# DESCRIÇÃO: Modelo SQLAlchemy para a tabela 'terminais_conectados'.
#            Armazena os terminais (máquinas) com sessão ativa no sistema.
#            Usado como pivô para envio de heartbeat por terminal.
# ---------------------------------------------------------------------------

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class TerminalConectado(Base):
    """
    Registra cada terminal (máquina) com login ativo no sistema.
    O heartbeat itera sobre esta tabela para enviar POST por HWID.

    - hwid: UNIQUE — um registro por máquina, sem duplicatas.
    - ultima_sinc: atualizado a cada heartbeat bem-sucedido.
    - Sem FK para usuarios — rastreia máquinas, não usuários.
    """
    __tablename__ = "terminais_conectados"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True,
    )
    hwid: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True,
        doc="Hardware ID do terminal remoto",
    )
    ultima_sinc: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False,
        doc="Timestamp do último heartbeat enviado com sucesso",
    )
    data_criacao: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False,
    )

    def __repr__(self) -> str:
        return f"<TerminalConectado(id={self.id}, hwid={self.hwid[:8]}...)>"
