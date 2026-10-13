# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/relatorio/os_performance.py
# DESCRICAO: Relatorios (crud) - OS finalizadas, abertas e por status.
# ---------------------------------------------------------------------------

from datetime import datetime
from typing import Sequence
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_
from app.db.models.ordem_servico import OrdemServico as OSModel
from app.db.models.funcionario import Funcionario
from app.core.enum import (
    OrdemServicoStatus,
)


# ===========================================================================
# OS-PERFORMANCE (Fase 4b)
# ===========================================================================

def get_os_finalizadas_periodo(
    db: Session, data_inicio: datetime, data_fim: datetime, empresa_id: int
) -> Sequence:
    """OS FINALIZADAS no período (âncora = data_finalizacao) com o que a análise precisa:
    técnico, valor, desfecho e as duas datas para o tempo de conclusão.

    O cálculo (média de tempo, contagem de reparo, agregado por técnico) fica no service
    — o volume de OS de uma loja por período é modesto e evita SQL de data por dialeto.
    Escopo por empresa via funcionário (OS sem funcionário também entram, como no dashboard).
    """
    stmt = (
        select(
            OSModel.id,
            OSModel.funcionario_id,
            Funcionario.nome.label("funcionario_nome"),
            OSModel.valor_total,
            OSModel.situacao_equipamento,
            OSModel.data_criacao,
            OSModel.data_finalizacao,
        )
        .outerjoin(Funcionario, Funcionario.id == OSModel.funcionario_id)
        .where(
            and_(
                OSModel.status == OrdemServicoStatus.FINALIZADA,
                OSModel.data_finalizacao.isnot(None),
                OSModel.data_finalizacao >= data_inicio,
                OSModel.data_finalizacao <= data_fim,
                or_(
                    Funcionario.empresa_id == empresa_id,
                    OSModel.funcionario_id.is_(None),
                ),
            )
        )
    )
    return db.execute(stmt).all()


def get_os_abertas_count_periodo(
    db: Session, data_inicio: datetime, data_fim: datetime, empresa_id: int
) -> int:
    """Quantas OS foram CRIADAS (abertas) no período — throughput de entrada."""
    stmt = (
        select(func.count(OSModel.id))
        .outerjoin(Funcionario, Funcionario.id == OSModel.funcionario_id)
        .where(
            and_(
                # Por data de criação, de propósito: aqui a pergunta é quanto
                # trabalho ENTROU, não quanto foi faturado.
                OSModel.data_criacao >= data_inicio,
                OSModel.data_criacao <= data_fim,
                or_(
                    Funcionario.empresa_id == empresa_id,
                    OSModel.funcionario_id.is_(None),
                ),
            )
        )
    )
    return db.execute(stmt).scalar() or 0


def get_os_por_status(db: Session, empresa_id: int) -> Sequence:
    """Snapshot do backlog: contagem de OS ATIVAS por status atual (não é do período)."""
    stmt = (
        select(
            OSModel.status,
            func.count(OSModel.id).label("quantidade"),
        )
        .outerjoin(Funcionario, Funcionario.id == OSModel.funcionario_id)
        .where(
            and_(
                OSModel.ativo == True,
                or_(
                    Funcionario.empresa_id == empresa_id,
                    OSModel.funcionario_id.is_(None),
                ),
            )
        )
        .group_by(OSModel.status)
    )
    return db.execute(stmt).all()
