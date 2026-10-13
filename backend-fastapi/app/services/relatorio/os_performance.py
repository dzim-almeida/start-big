# ---------------------------------------------------------------------------
# ARQUIVO: services/relatorio/os_performance.py
# DESCRICAO: Relatorios - desempenho de OS (so o Master).
# ---------------------------------------------------------------------------

from datetime import date, datetime
from sqlalchemy.orm import Session
from app.core.enum import SituacaoEquipamento
from app.core.tempo import intervalo_utc
from app.db.crud import relatorio as relatorio_crud
from app.schemas.relatorio import (
    RelatorioOSPerformance,
    OSReparoResumo,
    OSStatusItem,
    OSTecnicoItem,
)


# ---------------------------------------------------------------------------
# OS-PERFORMANCE (Fase 4b)
# ---------------------------------------------------------------------------

def _duracao_horas(criacao: datetime, finalizacao: datetime) -> float:
    """(finalização - criação) em horas, com piso em 0.

    Hoje as duas são UTC. Mas as OS finalizadas ANTES da correção do fuso têm
    data_finalizacao em horário local (UTC-3), o que dá diferença negativa em
    conclusões rápidas. Clampar em 0 evita média negativa nesses registros
    antigos sem mascarar OS realmente longas.
    """
    segundos = (finalizacao - criacao).total_seconds()
    return max(segundos, 0) / 3600


def get_os_performance(db: Session, inicio: date, fim: date, empresa_id: int) -> RelatorioOSPerformance:
    """
    Desempenho de OS no período: throughput (abertas × finalizadas), tempo médio de
    conclusão, taxa de reparo (desfecho) e desempenho por técnico, mais o snapshot do
    backlog por status atual.

    Finalizadas são ancoradas em data_finalizacao dentro do período; abertas em
    data_criacao. Tempo médio usa _duracao_horas (piso 0). Por técnico só entra OS
    com funcionário atribuído.
    """
    dt_inicio, dt_fim = intervalo_utc(inicio, fim)

    rows = relatorio_crud.get_os_finalizadas_periodo(db, dt_inicio, dt_fim, empresa_id)
    finalizadas = len(rows)
    faturamento_total = sum((r.valor_total or 0) for r in rows)

    # Tempo médio geral + acumuladores por técnico e desfecho.
    duracoes: list[float] = []
    reparado = sem_reparo = condenado = nao_informado = 0
    tecnicos: dict[int, dict] = {}

    for r in rows:
        if r.data_criacao and r.data_finalizacao:
            dur = _duracao_horas(r.data_criacao, r.data_finalizacao)
            duracoes.append(dur)
        else:
            dur = None

        situ = r.situacao_equipamento
        if situ == SituacaoEquipamento.REPARADO:
            reparado += 1
        elif situ == SituacaoEquipamento.SEM_REPARO:
            sem_reparo += 1
        elif situ == SituacaoEquipamento.CONDENADO:
            condenado += 1
        else:
            nao_informado += 1

        if r.funcionario_id is not None:
            t = tecnicos.setdefault(
                r.funcionario_id,
                {"nome": r.funcionario_nome or "—", "qtd": 0, "faturamento": 0, "duracoes": []},
            )
            t["qtd"] += 1
            t["faturamento"] += r.valor_total or 0
            if dur is not None:
                t["duracoes"].append(dur)

    tempo_medio = round(sum(duracoes) / len(duracoes), 1) if duracoes else None
    taxa_reparo = round(reparado / finalizadas * 100, 1) if finalizadas else 0.0

    por_tecnico = [
        OSTecnicoItem(
            funcionario_id=fid,
            nome=t["nome"],
            finalizadas=t["qtd"],
            tempo_medio_horas=round(sum(t["duracoes"]) / len(t["duracoes"]), 1) if t["duracoes"] else None,
            faturamento=t["faturamento"],
        )
        for fid, t in tecnicos.items()
    ]
    por_tecnico.sort(key=lambda x: x.finalizadas, reverse=True)

    abertas = relatorio_crud.get_os_abertas_count_periodo(db, dt_inicio, dt_fim, empresa_id)

    por_status = [
        OSStatusItem(status=r.status.value if hasattr(r.status, "value") else str(r.status), quantidade=r.quantidade)
        for r in relatorio_crud.get_os_por_status(db, empresa_id)
    ]

    return RelatorioOSPerformance(
        inicio=inicio,
        fim=fim,
        abertas=abertas,
        finalizadas=finalizadas,
        tempo_medio_horas=tempo_medio,
        faturamento_total=faturamento_total,
        reparo=OSReparoResumo(
            reparado=reparado,
            sem_reparo=sem_reparo,
            condenado=condenado,
            nao_informado=nao_informado,
            taxa_reparo_pct=taxa_reparo,
        ),
        por_status=por_status,
        por_tecnico=por_tecnico,
    )
