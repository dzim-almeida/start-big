# ---------------------------------------------------------------------------
# ARQUIVO: crud/dashboard.py
# DESCRICAO: Queries SQL via SQLAlchemy para o Dashboard.
#            Apenas leitura — sem efeito colateral no banco.
# ---------------------------------------------------------------------------

from datetime import datetime
from typing import Sequence, NamedTuple

from sqlalchemy.orm import Session, aliased
from sqlalchemy import select, func, or_, and_, case, literal

from app.db.models.venda import Venda
from app.db.models.ordem_servico import OrdemServico as OSModel
from app.db.models.ordem_servico_equipamento import OrdemServicoEquipamento as OSEquipamentoModel
from app.db.models.cliente import Cliente, ClientePF, ClientePJ
from app.db.models.produto import Produto
from app.db.models.estoque import Estoque
from app.db.models.funcionario import Funcionario

from app.core.enum import VendaStatus, OrdemServicoStatus


# ===========================================================================
# STATS — Metricas agregadas por periodo (query consolidada)
# ===========================================================================

class StatsAgregados(NamedTuple):
    vendas_total: int
    vendas_count: int
    os_count: int
    clientes_count: int
    os_soma: int
    os_finalizadas_count: int


def get_stats_agregados(
    db: Session,
    data_inicio: datetime,
    data_fim: datetime,
    empresa_id: int,
) -> StatsAgregados:
    """
    Retorna todas as metricas do dashboard em 3 queries (vendas, OS, clientes)
    em vez de 8 separadas. Filtra por empresa_id via Funcionario.
    """
    # Vendas: soma total + contagem (para ticket medio)
    vendas_stmt = select(
        func.coalesce(func.sum(Venda.total), 0).label("vendas_total"),
        func.count(Venda.id).label("vendas_count"),
    ).join(
        Funcionario, Funcionario.id == Venda.funcionario_id
    ).where(
        and_(
            Venda.status == VendaStatus.FINALIZADA,
            Venda.criado_em >= data_inicio,
            Venda.criado_em <= data_fim,
            Funcionario.empresa_id == empresa_id,
        )
    )
    vendas_result = db.execute(vendas_stmt).first()

    # OS: contagem total + soma/contagem finalizadas (para ticket medio)
    os_stmt = select(
        func.count(OSModel.id).label("os_count"),
        func.coalesce(
            func.sum(
                case((OSModel.status == OrdemServicoStatus.FINALIZADA, OSModel.valor_total), else_=0)
            ), 0
        ).label("os_soma"),
        func.sum(
            case((OSModel.status == OrdemServicoStatus.FINALIZADA, 1), else_=0)
        ).label("os_finalizadas_count"),
    ).outerjoin(
        Funcionario, Funcionario.id == OSModel.funcionario_id
    ).where(
        and_(
            OSModel.data_criacao >= data_inicio,
            OSModel.data_criacao <= data_fim,
            or_(
                Funcionario.empresa_id == empresa_id,
                OSModel.funcionario_id.is_(None),
            ),
        )
    )
    os_result = db.execute(os_stmt).first()

    # Clientes: sem empresa_id no modelo, contagem global
    clientes_stmt = select(func.count(Cliente.id)).where(
        and_(
            Cliente.data_criacao >= data_inicio,
            Cliente.data_criacao <= data_fim,
        )
    )
    clientes_count = db.scalar(clientes_stmt) or 0

    return StatsAgregados(
        vendas_total=vendas_result.vendas_total or 0,
        vendas_count=vendas_result.vendas_count or 0,
        os_count=os_result.os_count or 0,
        clientes_count=clientes_count,
        os_soma=os_result.os_soma or 0,
        os_finalizadas_count=os_result.os_finalizadas_count or 0,
    )


# ===========================================================================
# OS VENCENDO — Ordens proximas/passadas do prazo
# ===========================================================================

def get_os_vencendo(db: Session, empresa_id: int, limit: int = 10) -> Sequence:
    """
    OS ativas com data_previsao definida, ordenadas por urgencia (mais urgente primeiro).
    Filtra por empresa_id via Funcionario.
    """
    client_pf = aliased(ClientePF)
    client_pj = aliased(ClientePJ)

    stmt = (
        select(
            OSModel.numero_os,
            func.coalesce(client_pf.nome, client_pj.razao_social, literal("Sem cliente")).label("cliente_nome"),
            OSModel.defeito_relatado,
            OSModel.data_previsao,
        )
        .join(OSModel.equipamento)
        .join(OSEquipamentoModel.cliente)
        .outerjoin(client_pf, Cliente.id == client_pf.id)
        .outerjoin(client_pj, Cliente.id == client_pj.id)
        .outerjoin(Funcionario, Funcionario.id == OSModel.funcionario_id)
        .where(
            and_(
                OSModel.data_previsao.isnot(None),
                OSModel.status.notin_([OrdemServicoStatus.FINALIZADA, OrdemServicoStatus.CANCELADA]),
                or_(
                    Funcionario.empresa_id == empresa_id,
                    OSModel.funcionario_id.is_(None),
                ),
            )
        )
        .order_by(OSModel.data_previsao.asc())
        .limit(limit)
    )

    return db.execute(stmt).all()


# ===========================================================================
# ESTOQUE BAIXO — Produtos que precisam de reposicao
# ===========================================================================

def get_estoque_baixo(db: Session, limit: int = 8) -> Sequence:
    """
    Produtos ativos com estoque zerado ou abaixo da quantidade minima.
    Zerados aparecem primeiro, depois ordenados pela diferenca (mais criticos primeiro).
    Nota: Produto nao possui empresa_id — retorna dados globais.
    """
    stmt = (
        select(
            Produto.id.label("produto_id"),
            Produto.nome,
            Estoque.quantidade,
            Estoque.quantidade_minima,
        )
        .join(Estoque, Estoque.id == Produto.id)
        .where(
            and_(
                Produto.ativo == True,
                or_(
                    Estoque.quantidade == 0,
                    and_(
                        Estoque.quantidade_minima.isnot(None),
                        Estoque.quantidade <= Estoque.quantidade_minima,
                    ),
                ),
            )
        )
        .order_by(
            Estoque.quantidade.asc(),
        )
        .limit(limit)
    )

    return db.execute(stmt).all()


# ===========================================================================
# ULTIMAS VENDAS — Vendas recentes (finalizadas + orcamentos)
# ===========================================================================

def get_ultimas_vendas(db: Session, empresa_id: int, limit: int = 5) -> Sequence:
    """
    Ultimas vendas (finalizadas e orcamentos), com nome do cliente resolvido.
    Filtra por empresa_id via Funcionario.
    """
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
        .join(Funcionario, Funcionario.id == Venda.funcionario_id)
        .outerjoin(Venda.cliente)
        .outerjoin(client_pf, Cliente.id == client_pf.id)
        .outerjoin(client_pj, Cliente.id == client_pj.id)
        .where(
            and_(
                Venda.status.in_([VendaStatus.FINALIZADA, VendaStatus.ATIVA]),
                Funcionario.empresa_id == empresa_id,
            )
        )
        .order_by(Venda.criado_em.desc())
        .limit(limit)
    )

    return db.execute(stmt).all()
