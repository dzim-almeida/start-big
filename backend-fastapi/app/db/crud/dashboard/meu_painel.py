# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/dashboard/meu_painel.py
# DESCRICAO: Dashboard - visao do funcionario logado ("meu" painel):
#            resumo, series por dia, fila, OS e vendas dele.
# ---------------------------------------------------------------------------

from datetime import datetime
from typing import Sequence, NamedTuple

from sqlalchemy.orm import Session, aliased
from sqlalchemy import select, func, and_, case, literal

from app.core.tempo import data_local_sql, hoje_local, inicio_do_dia_utc
from app.db.models.venda import Venda
from app.db.models.ordem_servico import OrdemServico as OSModel
from app.db.models.objeto_servico import ObjetoServico as OSEquipamentoModel
from app.db.models.cliente import Cliente, ClientePF, ClientePJ

from app.core.enum import VendaStatus, OrdemServicoStatus, OrdemServicoPrioridade


# ===========================================================================
# MEU RESUMO — Stats pessoais do funcionario logado
# ===========================================================================

class MeuResumoAgregado(NamedTuple):
    minhas_vendas_valor: int
    minhas_vendas_count: int
    minhas_os_valor: int
    minhas_os_abertas: int
    minhas_os_concluidas: int


def get_meu_resumo_stats(
    db: Session,
    data_inicio: datetime,
    data_fim: datetime,
    funcionario_id: int,
) -> MeuResumoAgregado:
    """Stats pessoais do funcionario: vendas e OS filtradas pelo seu ID."""
    vendas_stmt = select(
        func.coalesce(func.sum(Venda.total), 0).label("vendas_valor"),
        func.count(Venda.id).label("vendas_count"),
    ).where(
        and_(
            Venda.status == VendaStatus.FINALIZADA,
            Venda.criado_em >= data_inicio,
            Venda.criado_em <= data_fim,
            Venda.funcionario_id == funcionario_id,
        )
    )
    vendas_result = db.execute(vendas_stmt).first()

    # Duas ancoras, mesmo motivo do get_stats_agregados: o que o funcionario
    # CONCLUIU (e faturou) conta pela data de finalizacao; o que ele tem ABERTO
    # conta pela data de entrada.
    os_concluidas_stmt = select(
        func.count(OSModel.id).label("os_concluidas"),
        func.coalesce(func.sum(OSModel.valor_total), 0).label("os_valor"),
    ).where(
        and_(
            OSModel.status == OrdemServicoStatus.FINALIZADA,
            OSModel.data_finalizacao.isnot(None),
            OSModel.data_finalizacao >= data_inicio,
            OSModel.data_finalizacao <= data_fim,
            OSModel.funcionario_id == funcionario_id,
            OSModel.ativo == True,
        )
    )
    os_concluidas_result = db.execute(os_concluidas_stmt).first()

    os_abertas = db.scalar(
        select(func.count(OSModel.id)).where(
            and_(
                OSModel.status.notin_([OrdemServicoStatus.FINALIZADA, OrdemServicoStatus.CANCELADA]),
                OSModel.data_criacao >= data_inicio,
                OSModel.data_criacao <= data_fim,
                OSModel.funcionario_id == funcionario_id,
                OSModel.ativo == True,
            )
        )
    ) or 0

    return MeuResumoAgregado(
        minhas_vendas_valor=vendas_result.vendas_valor or 0,
        minhas_vendas_count=vendas_result.vendas_count or 0,
        minhas_os_valor=os_concluidas_result.os_valor or 0,
        minhas_os_abertas=os_abertas,
        minhas_os_concluidas=os_concluidas_result.os_concluidas or 0,
    )


def get_minhas_vendas_por_dia(
    db: Session, data_inicio: datetime, data_fim: datetime, funcionario_id: int
) -> Sequence:
    """Soma das vendas finalizadas do funcionario, agrupada por dia (serie de tendencia pessoal)."""
    stmt = (
        select(
            data_local_sql(Venda.criado_em).label("dia"),
            func.coalesce(func.sum(Venda.total), 0).label("total"),
        )
        .where(
            and_(
                Venda.status == VendaStatus.FINALIZADA,
                Venda.criado_em >= data_inicio,
                Venda.criado_em <= data_fim,
                Venda.funcionario_id == funcionario_id,
            )
        )
        .group_by(data_local_sql(Venda.criado_em))
    )
    return db.execute(stmt).all()


def get_minhas_os_por_dia(
    db: Session, data_inicio: datetime, data_fim: datetime, funcionario_id: int
) -> Sequence:
    """Soma das OS finalizadas do funcionario, agrupada por dia (serie de tendencia pessoal)."""
    stmt = (
        select(
            data_local_sql(OSModel.data_finalizacao).label("dia"),
            func.coalesce(func.sum(OSModel.valor_total), 0).label("total"),
        )
        .where(
            and_(
                OSModel.status == OrdemServicoStatus.FINALIZADA,
                OSModel.data_finalizacao.isnot(None),
                OSModel.data_finalizacao >= data_inicio,
                OSModel.data_finalizacao <= data_fim,
                OSModel.funcionario_id == funcionario_id,
            )
        )
        .group_by(data_local_sql(OSModel.data_finalizacao))
    )
    return db.execute(stmt).all()


def get_minhas_os_vencendo(db: Session, funcionario_id: int, limit: int = 10):
    """OS do funcionario proximas/passadas do prazo."""
    client_pf = aliased(ClientePF)
    client_pj = aliased(ClientePJ)

    stmt = (
        select(
            OSModel.numero_os,
            func.coalesce(client_pf.nome, client_pj.razao_social, literal("Sem cliente")).label("cliente_nome"),
            OSModel.defeito_relatado,
            OSModel.data_previsao,
        )
        .join(OSModel.objeto)
        .join(OSEquipamentoModel.cliente)
        .outerjoin(client_pf, Cliente.id == client_pf.id)
        .outerjoin(client_pj, Cliente.id == client_pj.id)
        .where(
            and_(
                OSModel.data_previsao.isnot(None),
                OSModel.status.notin_([OrdemServicoStatus.FINALIZADA, OrdemServicoStatus.CANCELADA]),
                OSModel.funcionario_id == funcionario_id,
            )
        )
        .order_by(OSModel.data_previsao.asc())
        .limit(limit)
    )
    return db.execute(stmt).all()


def get_minha_fila(db: Session, funcionario_id: int, limit: int = 20):
    """OS abertas do funcionario ordenadas por prioridade (URGENTE→BAIXA) e prazo."""
    client_pf = aliased(ClientePF)
    client_pj = aliased(ClientePJ)

    prioridade_order = case(
        (OSModel.prioridade == OrdemServicoPrioridade.URGENTE, 1),
        (OSModel.prioridade == OrdemServicoPrioridade.ALTA, 2),
        (OSModel.prioridade == OrdemServicoPrioridade.NORMAL, 3),
        (OSModel.prioridade == OrdemServicoPrioridade.BAIXA, 4),
        else_=5,
    )

    stmt = (
        select(
            OSModel.numero_os,
            func.coalesce(client_pf.nome, client_pj.razao_social, literal("Sem cliente")).label("cliente_nome"),
            OSModel.defeito_relatado,
            OSModel.prioridade,
            OSModel.status,
            OSModel.data_previsao,
        )
        .join(OSModel.objeto)
        .join(OSEquipamentoModel.cliente)
        .outerjoin(client_pf, Cliente.id == client_pf.id)
        .outerjoin(client_pj, Cliente.id == client_pj.id)
        .where(
            and_(
                OSModel.funcionario_id == funcionario_id,
                OSModel.status.notin_([
                    OrdemServicoStatus.FINALIZADA,
                    OrdemServicoStatus.CANCELADA,
                    OrdemServicoStatus.AGUARDANDO_RETIRADA,
                ]),
                OSModel.ativo == True,
            )
        )
        .order_by(prioridade_order.asc(), OSModel.data_previsao.asc())
        .limit(limit)
    )
    return db.execute(stmt).all()


def get_minhas_os_atrasadas(db: Session, funcionario_id: int, limit: int = 10):
    """OS com data_previsao anterior a hoje (atrasadas)."""
    client_pf = aliased(ClientePF)
    client_pj = aliased(ClientePJ)
    # `data_previsao` e data de calendario escolhida por uma pessoa -- nao e
    # instante. Compara com a meia-noite da LOJA, sem converter para UTC.
    hoje_inicio = datetime.combine(hoje_local(), datetime.min.time())

    stmt = (
        select(
            OSModel.numero_os,
            func.coalesce(client_pf.nome, client_pj.razao_social, literal("Sem cliente")).label("cliente_nome"),
            OSModel.defeito_relatado,
            OSModel.data_previsao,
        )
        .join(OSModel.objeto)
        .join(OSEquipamentoModel.cliente)
        .outerjoin(client_pf, Cliente.id == client_pf.id)
        .outerjoin(client_pj, Cliente.id == client_pj.id)
        .where(
            and_(
                OSModel.funcionario_id == funcionario_id,
                OSModel.data_previsao < hoje_inicio,
                OSModel.status.notin_([OrdemServicoStatus.FINALIZADA, OrdemServicoStatus.CANCELADA]),
                OSModel.ativo == True,
            )
        )
        .order_by(OSModel.data_previsao.asc())
        .limit(limit)
    )
    return db.execute(stmt).all()


def get_os_aguardando_retirada(db: Session, funcionario_id: int, limit: int = 10):
    """OS com status AGUARDANDO_RETIRADA do funcionario."""
    client_pf = aliased(ClientePF)
    client_pj = aliased(ClientePJ)

    stmt = (
        select(
            OSModel,
            func.coalesce(client_pf.nome, client_pj.razao_social, literal("Sem cliente")).label("cliente_nome"),
        )
        .join(OSModel.objeto)
        .join(OSEquipamentoModel.cliente)
        .outerjoin(client_pf, Cliente.id == client_pf.id)
        .outerjoin(client_pj, Cliente.id == client_pj.id)
        .where(
            and_(
                OSModel.funcionario_id == funcionario_id,
                OSModel.status == OrdemServicoStatus.AGUARDANDO_RETIRADA,
                OSModel.ativo == True,
            )
        )
        .order_by(OSModel.data_finalizacao.asc())
        .limit(limit)
    )
    return db.execute(stmt).all()


def get_minhas_vendas_hoje(db: Session, funcionario_id: int):
    """Vendas do funcionario criadas hoje."""
    client_pf = aliased(ClientePF)
    client_pj = aliased(ClientePJ)
    # `criado_em`/`data_criacao` sao instantes em UTC: a borda do dia da loja
    # vai convertida, senao a venda da noite cai no dia seguinte.
    hoje_inicio = inicio_do_dia_utc(hoje_local())

    stmt = (
        select(
            Venda.id,
            func.coalesce(client_pf.nome, client_pj.razao_social).label("cliente_nome"),
            Venda.total,
            Venda.status,
            Venda.criado_em,
        )
        .outerjoin(Venda.cliente)
        .outerjoin(client_pf, Cliente.id == client_pf.id)
        .outerjoin(client_pj, Cliente.id == client_pj.id)
        .where(
            and_(
                Venda.funcionario_id == funcionario_id,
                Venda.criado_em >= hoje_inicio,
                Venda.status.in_([VendaStatus.ATIVA, VendaStatus.FINALIZADA]),
            )
        )
        .order_by(Venda.criado_em.desc())
    )
    return db.execute(stmt).all()


def get_minhas_os_hoje(db: Session, funcionario_id: int):
    """OS do funcionario criadas hoje."""
    client_pf = aliased(ClientePF)
    client_pj = aliased(ClientePJ)
    # `criado_em`/`data_criacao` sao instantes em UTC: a borda do dia da loja
    # vai convertida, senao a venda da noite cai no dia seguinte.
    hoje_inicio = inicio_do_dia_utc(hoje_local())

    stmt = (
        select(
            OSModel.numero_os,
            func.coalesce(client_pf.nome, client_pj.razao_social, literal("Sem cliente")).label("cliente_nome"),
            OSModel.valor_total,
            OSModel.status,
            OSModel.data_criacao,
        )
        .join(OSModel.objeto)
        .join(OSEquipamentoModel.cliente)
        .outerjoin(client_pf, Cliente.id == client_pf.id)
        .outerjoin(client_pj, Cliente.id == client_pj.id)
        .where(
            and_(
                OSModel.funcionario_id == funcionario_id,
                OSModel.data_criacao >= hoje_inicio,
                OSModel.ativo == True,
            )
        )
        .order_by(OSModel.data_criacao.desc())
    )
    return db.execute(stmt).all()


def get_minhas_ultimas_vendas(db: Session, funcionario_id: int, limit: int = 5):
    """Ultimas vendas do funcionario logado."""
    client_pf = aliased(ClientePF)
    client_pj = aliased(ClientePJ)

    stmt = (
        select(
            Venda.id,
            func.coalesce(client_pf.nome, client_pj.razao_social).label("cliente_nome"),
            Venda.total,
            Venda.status,
            Venda.criado_em,
        )
        .outerjoin(Venda.cliente)
        .outerjoin(client_pf, Cliente.id == client_pf.id)
        .outerjoin(client_pj, Cliente.id == client_pj.id)
        .where(
            and_(
                Venda.status.in_([VendaStatus.FINALIZADA, VendaStatus.ATIVA]),
                Venda.funcionario_id == funcionario_id,
            )
        )
        .order_by(Venda.criado_em.desc())
        .limit(limit)
    )
    return db.execute(stmt).all()
