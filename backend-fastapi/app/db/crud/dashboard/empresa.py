# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/dashboard/empresa.py
# DESCRICAO: Dashboard - visao da empresa (dono/master): OS vencendo e
#            atrasadas, estoque baixo, ranking, OS por status, ultimas vendas.
# ---------------------------------------------------------------------------

from datetime import datetime
from typing import Sequence

from sqlalchemy.orm import Session, aliased
from sqlalchemy import select, func, or_, and_, literal

from app.core.tempo import hoje_local
from app.db.models.venda import Venda
from app.db.models.ordem_servico import OrdemServico as OSModel
from app.db.models.objeto_servico import ObjetoServico as OSEquipamentoModel
from app.db.models.cliente import Cliente, ClientePF, ClientePJ
from app.db.models.produto import Produto
from app.db.models.estoque import Estoque
from app.db.models.funcionario import Funcionario

from app.core.enum import VendaStatus, OrdemServicoStatus


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
        .join(OSModel.objeto)
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
# MASTER — Ranking de funcionarios
# ===========================================================================

def get_ranking_funcionarios(
    db: Session,
    data_inicio: datetime,
    data_fim: datetime,
    empresa_id: int,
    limit: int = 10,
) -> Sequence:
    """Ranking de funcionarios por valor de vendas finalizadas no periodo."""
    vendas_sub = (
        select(
            Venda.funcionario_id,
            func.coalesce(func.sum(Venda.total), 0).label("total_vendas"),
            func.count(Venda.id).label("qtd_vendas"),
        )
        .where(and_(
            Venda.status == VendaStatus.FINALIZADA,
            Venda.criado_em >= data_inicio,
            Venda.criado_em <= data_fim,
        ))
        .group_by(Venda.funcionario_id)
        .subquery()
    )

    os_sub = (
        select(
            OSModel.funcionario_id,
            func.count(OSModel.id).label("qtd_os"),
            func.coalesce(func.sum(OSModel.valor_total), 0).label("os_valor"),
        )
        .where(and_(
            OSModel.status == OrdemServicoStatus.FINALIZADA,
            OSModel.data_finalizacao.isnot(None),
            OSModel.data_finalizacao >= data_inicio,
            OSModel.data_finalizacao <= data_fim,
        ))
        .group_by(OSModel.funcionario_id)
        .subquery()
    )

    total_vendas = func.coalesce(vendas_sub.c.total_vendas, 0)
    total_os = func.coalesce(os_sub.c.os_valor, 0)

    stmt = (
        select(
            Funcionario.id,
            Funcionario.nome,
            total_vendas.label("total_vendas_valor"),
            func.coalesce(vendas_sub.c.qtd_vendas, 0).label("qtd_vendas"),
            total_os.label("total_os_valor"),
            func.coalesce(os_sub.c.qtd_os, 0).label("qtd_os_fechadas"),
        )
        .outerjoin(vendas_sub, vendas_sub.c.funcionario_id == Funcionario.id)
        .outerjoin(os_sub, os_sub.c.funcionario_id == Funcionario.id)
        .where(and_(
            Funcionario.empresa_id == empresa_id,
            Funcionario.ativo == True,
        ))
        # Ranking JUSTO: ordena por faturamento total (vendas + OS), nao so vendas.
        .order_by((total_vendas + total_os).desc())
        .limit(limit)
    )
    return db.execute(stmt).all()


# ===========================================================================
# MASTER — OS por status
# ===========================================================================

def get_os_por_status(db: Session, empresa_id: int) -> Sequence:
    """Contagem de OS ativas agrupadas por status para a empresa."""
    stmt = (
        select(
            OSModel.status,
            func.count(OSModel.id).label("count"),
        )
        .outerjoin(Funcionario, Funcionario.id == OSModel.funcionario_id)
        .where(and_(
            OSModel.ativo == True,
            OSModel.status.notin_([OrdemServicoStatus.CANCELADA, OrdemServicoStatus.FINALIZADA]),
            or_(
                Funcionario.empresa_id == empresa_id,
                OSModel.funcionario_id.is_(None),
            ),
        ))
        .group_by(OSModel.status)
    )
    return db.execute(stmt).all()


# ===========================================================================
# MASTER — OS atrasadas da empresa toda
# ===========================================================================

def get_os_atrasadas_empresa(db: Session, empresa_id: int, limit: int = 15) -> Sequence:
    """OS com prazo vencido de toda a empresa, com nome do responsavel."""
    client_pf = aliased(ClientePF)
    client_pj = aliased(ClientePJ)
    # `data_previsao` e data de calendario escolhida por uma pessoa -- nao e
    # instante. Compara com a meia-noite da LOJA, sem converter para UTC.
    hoje_inicio = datetime.combine(hoje_local(), datetime.min.time())

    stmt = (
        select(
            OSModel.numero_os,
            func.coalesce(client_pf.nome, client_pj.razao_social, literal("Sem cliente")).label("cliente_nome"),
            Funcionario.nome.label("funcionario_nome"),
            OSModel.defeito_relatado,
            OSModel.data_previsao,
        )
        .join(OSModel.objeto)
        .join(OSEquipamentoModel.cliente)
        .outerjoin(client_pf, Cliente.id == client_pf.id)
        .outerjoin(client_pj, Cliente.id == client_pj.id)
        .outerjoin(Funcionario, Funcionario.id == OSModel.funcionario_id)
        .where(and_(
            OSModel.data_previsao < hoje_inicio,
            OSModel.status.notin_([OrdemServicoStatus.FINALIZADA, OrdemServicoStatus.CANCELADA]),
            OSModel.ativo == True,
            or_(
                Funcionario.empresa_id == empresa_id,
                OSModel.funcionario_id.is_(None),
            ),
        ))
        .order_by(OSModel.data_previsao.asc())
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
