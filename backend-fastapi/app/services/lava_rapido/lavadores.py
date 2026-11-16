# ---------------------------------------------------------------------------
# ARQUIVO: app/services/lava_rapido/lavadores.py
# DESCRICAO: Lavadores (executores) da OS -- SPEC-00 O7a/O7c e Spec 10A.
#
# So existe para segmento que declara a capacidade `executores_os` (hoje, o
# lava-rapido). O responsavel continua sendo quem abriu a OS; os lavadores
# sao quem executa, e e para eles que vai a comissao de servico (ver
# db/crud/relatorio/equipe.py).
# ---------------------------------------------------------------------------

from typing import List

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import segmentos as reg
from app.core.enum import OrdemServicoStatus
from app.db.crud.ordem_servico.consultas import get_ordem_servico_by_numero_os
from app.db.models.funcionario import Funcionario
from app.db.models.ordem_servico import OrdemServico
from app.db.models.ordem_servico_executor import OrdemServicoExecutor
from app.schemas.lava_rapido.lavador import LavadorRead
from app.services.sistema.segmentos import get_segmento_atual

# "1 ou 2 por carro" (cliente, 12/11); a tabela aceita mais, com folga.
MAXIMO_DE_LAVADORES = 5


def _exigir_executores(db: Session) -> None:
    if not reg.segmento_tem_capacidade(get_segmento_atual(db), reg.CAP_EXECUTORES_OS):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lavadores da OS não disponíveis para este segmento.",
        )


def _os_ou_404(db: Session, numero_os: str) -> OrdemServico:
    os_db = get_ordem_servico_by_numero_os(db, numero_os)
    if os_db is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OS não encontrada.")
    return os_db


def lavadores_da_os(db: Session, os_id: int) -> List[LavadorRead]:
    """Lavadores de uma OS, na ordem em que foram escolhidos. Sem guarda:
    tambem e usado pelo patio, que ja conferiu a capacidade."""
    linhas = db.execute(
        select(Funcionario.id, Funcionario.nome)
        .join(OrdemServicoExecutor, OrdemServicoExecutor.funcionario_id == Funcionario.id)
        .where(OrdemServicoExecutor.ordem_servico_id == os_id)
        .order_by(OrdemServicoExecutor.id)
    ).all()
    return [LavadorRead(funcionario_id=fid, nome=nome) for fid, nome in linhas]


def listar(db: Session, numero_os: str) -> List[LavadorRead]:
    _exigir_executores(db)
    return lavadores_da_os(db, _os_ou_404(db, numero_os).id)


def definir(db: Session, numero_os: str, funcionario_ids: List[int]) -> List[LavadorRead]:
    """Troca a lista inteira de lavadores da OS. Lista vazia = sem lavador
    (a comissao volta para o responsavel, como sempre)."""
    _exigir_executores(db)
    os_db = _os_ou_404(db, numero_os)

    # OS fechada ja entrou (ou vai entrar) na folha do mes: trocar quem lavou
    # mudaria a comissao paga sem ninguem ver.
    if os_db.status in (OrdemServicoStatus.FINALIZADA, OrdemServicoStatus.CANCELADA):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Não é possível trocar os lavadores de uma OS finalizada ou cancelada.",
        )

    ids = list(dict.fromkeys(funcionario_ids))           # sem repetir, na ordem escolhida
    if len(ids) > MAXIMO_DE_LAVADORES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"No máximo {MAXIMO_DE_LAVADORES} lavadores por OS.",
        )
    if ids:
        ativos = set(db.scalars(
            select(Funcionario.id).where(Funcionario.id.in_(ids), Funcionario.ativo.is_(True))
        ).all())
        if ativos != set(ids):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Lavador não encontrado ou inativo.",
            )

    for antigo in db.scalars(
        select(OrdemServicoExecutor).where(OrdemServicoExecutor.ordem_servico_id == os_db.id)
    ).all():
        db.delete(antigo)
    db.flush()
    db.add_all([OrdemServicoExecutor(ordem_servico_id=os_db.id, funcionario_id=fid) for fid in ids])
    db.flush()
    return lavadores_da_os(db, os_db.id)
