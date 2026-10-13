# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/sessao_caixa/sessao.py
# DESCRICAO: Caixa (crud) - buscar, abrir e listar sessoes.
# ---------------------------------------------------------------------------

from datetime import datetime
from typing import Optional, Sequence
from sqlalchemy.orm import Session
from app.core.enum import (
    SessaoCaixaStatus,
)
from app.db.models.sessao_caixa import SessaoCaixa


# ===========================================================================
# SESSÃO
# ===========================================================================

def get_sessao_by_id(db: Session, sessao_id: int) -> Optional[SessaoCaixa]:
    return db.query(SessaoCaixa).filter(SessaoCaixa.id == sessao_id).first()


def get_sessao_aberta_do_funcionario(db: Session, funcionario_id: int) -> Optional[SessaoCaixa]:
    """O turno aberto de um operador.

    É por aqui que a finalização da venda descobre em qual turno o dinheiro cai,
    sem precisar receber o HWID do terminal no checkout. Funciona porque o
    serviço garante que um operador não tem dois turnos abertos ao mesmo tempo:
    ninguém está em dois caixas de uma vez.
    """
    return (
        db.query(SessaoCaixa)
        .filter(
            SessaoCaixa.funcionario_id == funcionario_id,
            SessaoCaixa.status == SessaoCaixaStatus.ABERTO,
        )
        .order_by(SessaoCaixa.data_abertura.desc())
        .first()
    )


def get_sessao_aberta_do_terminal(db: Session, terminal_hwid: str) -> Optional[SessaoCaixa]:
    """O turno aberto de uma máquina. O índice único do banco garante no máximo um."""
    return (
        db.query(SessaoCaixa)
        .filter(
            SessaoCaixa.terminal_hwid == terminal_hwid,
            SessaoCaixa.status == SessaoCaixaStatus.ABERTO,
        )
        .first()
    )


def criar_sessao(
    db: Session,
    funcionario_id: int,
    saldo_inicial: int,
    terminal_hwid: Optional[str],
) -> SessaoCaixa:
    sessao = SessaoCaixa(
        funcionario_id=funcionario_id,
        saldo_inicial=saldo_inicial,
        terminal_hwid=terminal_hwid,
        status=SessaoCaixaStatus.ABERTO,
    )
    db.add(sessao)
    db.flush()
    return sessao


def listar_sessoes(
    db: Session,
    empresa_id: int,
    inicio: Optional[datetime] = None,
    fim: Optional[datetime] = None,
    limit: int = 50,
) -> Sequence[SessaoCaixa]:
    """Histórico de turnos da empresa, mais recentes primeiro.

    O filtro é pela ABERTURA do turno: é o que o dono tem na cabeça quando
    pergunta "o caixa de ontem". Um turno que virou a madrugada aparece no dia em
    que começou, e não no dia em que foi fechado.

    `inicio` e `fim` já chegam em UTC (ver app/core/tempo.py) — quem converte o
    dia da loja é quem chama.
    """
    from app.db.models.funcionario import Funcionario

    consulta = (
        db.query(SessaoCaixa)
        .join(Funcionario, Funcionario.id == SessaoCaixa.funcionario_id)
        .filter(Funcionario.empresa_id == empresa_id)
    )
    if inicio is not None:
        consulta = consulta.filter(SessaoCaixa.data_abertura >= inicio)
    if fim is not None:
        consulta = consulta.filter(SessaoCaixa.data_abertura <= fim)

    return (
        consulta.order_by(SessaoCaixa.data_abertura.desc())
        .limit(limit)
        .all()
    )
