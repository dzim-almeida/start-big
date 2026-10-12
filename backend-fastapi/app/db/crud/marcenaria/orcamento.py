# ---------------------------------------------------------------------------
# ARQUIVO: app/db/crud/marcenaria/orcamento.py
# DESCRICAO: Consultas do orcamento de marcenaria (Spec 06A).
#
#            So SQL. O commit e a regra (status, revisao, permissao) ficam no
#            servico (app/services/marcenaria/orcamento.py).
# ---------------------------------------------------------------------------

from datetime import date
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased, selectinload

from app.core.busca import filtro_busca
from app.db.models.cliente import Cliente, ClientePF, ClientePJ
from app.db.models.fornecedor import Fornecedor
from app.db.models.marcenaria.ambiente import MarcenariaAmbiente, MarcenariaMovel
from app.db.models.marcenaria.orcamento import (
    MarcenariaOrcamento,
    MarcenariaOrcamentoAnexo,
    MarcenariaOrcamentoRT,
    StatusOrcamento,
)
from app.db.models.objeto_servico import ObjetoServico
from app.db.models.ordem_servico import OrdemServico


# ===========================================================================
# ORCAMENTO
# ===========================================================================

def get_orcamento(db: Session, orcamento_id: int) -> Optional[MarcenariaOrcamento]:
    """O orcamento com a arvore inteira carregada de uma vez.

    `selectinload` busca cada nivel (ambientes, moveis, insumos, arquitetos)
    numa consulta so, em vez de uma por linha: o detalhe roda o motor sobre
    tudo, e 300 moveis virariam 300 consultas.
    """
    stmt = (
        select(MarcenariaOrcamento)
        .where(MarcenariaOrcamento.id == orcamento_id)
        .options(
            selectinload(MarcenariaOrcamento.ambientes)
            .selectinload(MarcenariaAmbiente.moveis)
            .selectinload(MarcenariaMovel.insumos),
            selectinload(MarcenariaOrcamento.ambientes)
            .selectinload(MarcenariaAmbiente.moveis)
            .selectinload(MarcenariaMovel.central),
            selectinload(MarcenariaOrcamento.rts).selectinload(MarcenariaOrcamentoRT.fornecedor),
        )
    )
    return db.scalar(stmt)


def get_orcamento_por_os(db: Session, os_id: int) -> Optional[MarcenariaOrcamento]:
    """O orcamento cuja aprovacao gerou a OS (Spec 08A), com a arvore."""
    orcamento_id = db.scalar(select(MarcenariaOrcamento.id).where(MarcenariaOrcamento.os_id == os_id))
    return get_orcamento(db, orcamento_id) if orcamento_id is not None else None


def ultimo_codigo_com_prefixo(db: Session, prefixo: str) -> Optional[str]:
    """O codigo mais alto que comeca com o prefixo do ano ("ORC-2026-").

    Ordena pelo proprio codigo (e nao pelo id): o numero tem sempre 6 digitos
    com zeros a esquerda, entao a ordem do texto e a ordem do numero.
    """
    stmt = (
        select(MarcenariaOrcamento.codigo)
        .where(MarcenariaOrcamento.codigo.like(f"{prefixo}%"))
        .order_by(MarcenariaOrcamento.codigo.desc())
        .limit(1)
    )
    return db.scalar(stmt)


def listar_enviados_vencidos(db: Session, hoje: date) -> list[MarcenariaOrcamento]:
    """ENVIADO com a validade antes de hoje (D14). Usa o indice da validade."""
    stmt = select(MarcenariaOrcamento).where(
        MarcenariaOrcamento.status == StatusOrcamento.ENVIADO,
        MarcenariaOrcamento.data_validade.is_not(None),
        MarcenariaOrcamento.data_validade < hoje,
    )
    return list(db.scalars(stmt))


def listar_versoes(db: Session, codigo: str) -> list[MarcenariaOrcamento]:
    """Todas as versoes de um codigo, da mais nova para a mais antiga."""
    stmt = (
        select(MarcenariaOrcamento)
        .where(MarcenariaOrcamento.codigo == codigo)
        .order_by(MarcenariaOrcamento.versao.desc())
    )
    return list(db.scalars(stmt))


def _filtros_da_lista(stmt, filtros: dict[str, Any], hoje: date):
    """Aplica os filtros da lista (secao 6.3) a uma consulta de orcamentos."""
    # Padrao: so a versao mais recente de cada codigo. A versao antiga e
    # sempre SUBSTITUIDO (D16), entao basta deixa-la de fora.
    if not filtros.get("incluir_versoes_antigas"):
        stmt = stmt.where(MarcenariaOrcamento.status != StatusOrcamento.SUBSTITUIDO)

    if filtros.get("status"):
        stmt = stmt.where(MarcenariaOrcamento.status == filtros["status"])

    if filtros.get("cliente_id"):
        stmt = stmt.where(MarcenariaOrcamento.cliente_id == filtros["cliente_id"])

    if filtros.get("vendedor_id"):
        stmt = stmt.where(MarcenariaOrcamento.funcionario_id == filtros["vendedor_id"])

    vence_em = filtros.get("vence_em_dias")
    if vence_em is not None:
        # ENVIADO com a validade entre hoje e hoje + N (os que pedem ligacao).
        stmt = stmt.where(
            MarcenariaOrcamento.status == StatusOrcamento.ENVIADO,
            MarcenariaOrcamento.data_validade >= hoje,
            MarcenariaOrcamento.data_validade <= date.fromordinal(hoje.toordinal() + vence_em),
        )

    busca = filtros.get("busca")
    if busca:
        # Cliente e polimorfico (PF tem `nome`, PJ tem razao social e
        # fantasia): os dois lados entram por outer join, como na lista da OS.
        pf = aliased(ClientePF)
        pj = aliased(ClientePJ)
        stmt = (
            stmt.outerjoin(Cliente, Cliente.id == MarcenariaOrcamento.cliente_id)
            .outerjoin(pf, pf.id == Cliente.id)
            .outerjoin(pj, pj.id == Cliente.id)
        )
        filtro = filtro_busca(busca, (
            MarcenariaOrcamento.codigo,
            MarcenariaOrcamento.projeto_nome,
            pf.nome,
            pj.razao_social,
            pj.nome_fantasia,
        ))
        if filtro is not None:
            stmt = stmt.where(filtro)
    return stmt


def listar_orcamentos(
    db: Session,
    filtros: dict[str, Any],
    hoje: date,
    skip: int,
    limit: int,
) -> tuple[list[MarcenariaOrcamento], int]:
    """Uma pagina da lista e o total de itens (para a paginacao)."""
    base = _filtros_da_lista(select(MarcenariaOrcamento), filtros, hoje)

    # Total: conta os ids da mesma consulta, sem a paginacao.
    total = db.scalar(select(func.count()).select_from(base.with_only_columns(MarcenariaOrcamento.id).subquery()))

    stmt = (
        base.options(
            selectinload(MarcenariaOrcamento.cliente),
            selectinload(MarcenariaOrcamento.funcionario),
            selectinload(MarcenariaOrcamento.os),             # numero da OS no aprovado (08A)
        )
        # Mais recente primeiro; o id desempata duas escritas no mesmo instante.
        .order_by(MarcenariaOrcamento.data_atualizacao.desc(), MarcenariaOrcamento.id.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt)), int(total or 0)


def contar_por_status(db: Session) -> dict[str, int]:
    """Quantos orcamentos por status, so a versao mais recente (secao 6.8)."""
    stmt = (
        select(MarcenariaOrcamento.status, func.count(MarcenariaOrcamento.id))
        .where(MarcenariaOrcamento.status != StatusOrcamento.SUBSTITUIDO)
        .group_by(MarcenariaOrcamento.status)
    )
    return {status: int(qtd) for status, qtd in db.execute(stmt)}


def contar_vencendo(db: Session, hoje: date, dias: int) -> int:
    """ENVIADO com a validade entre hoje e hoje + dias."""
    stmt = select(func.count(MarcenariaOrcamento.id)).where(
        MarcenariaOrcamento.status == StatusOrcamento.ENVIADO,
        MarcenariaOrcamento.data_validade >= hoje,
        MarcenariaOrcamento.data_validade <= date.fromordinal(hoje.toordinal() + dias),
    )
    return int(db.scalar(stmt) or 0)


# ===========================================================================
# PROJETOS DO CLIENTE (secao 6.7)
# ===========================================================================

def listar_projetos_do_cliente(db: Session, cliente_id: int) -> list[tuple[ObjetoServico, Any]]:
    """Objetos ATIVOS do cliente, com a data da ultima OS (ou do cadastro).

    Devolve pares (objeto, ultimo_uso), do uso mais recente ao mais antigo.
    """
    # A data da OS mais nova de cada objeto (subconsulta agrupada).
    ultima_os = (
        select(OrdemServico.objeto_id, func.max(OrdemServico.data_criacao).label("ultima"))
        .group_by(OrdemServico.objeto_id)
        .subquery()
    )
    # Sem OS ainda, vale a data do cadastro do objeto.
    ultimo_uso = func.coalesce(ultima_os.c.ultima, ObjetoServico.data_criacao)
    stmt = (
        select(ObjetoServico, ultimo_uso)
        .outerjoin(ultima_os, ultima_os.c.objeto_id == ObjetoServico.id)
        .where(ObjetoServico.cliente_id == cliente_id, ObjetoServico.ativo.is_(True))
        .order_by(ultimo_uso.desc(), ObjetoServico.id.desc())
    )
    return [(objeto, uso) for objeto, uso in db.execute(stmt)]


# ===========================================================================
# ANEXOS (D27-D31)
# ===========================================================================

def listar_arquitetos_ativos(db: Session) -> list[Fornecedor]:
    """Fornecedores ATIVOS do tipo `arquiteto`, em ordem de nome (Spec 09B D4)."""
    stmt = (
        select(Fornecedor)
        .where(Fornecedor.tipo == "arquiteto", Fornecedor.ativo.is_(True))
        .order_by(Fornecedor.nome, Fornecedor.id)
    )
    return list(db.scalars(stmt))


def listar_anexos(db: Session, codigo: str) -> list[MarcenariaOrcamentoAnexo]:
    """Anexos do CODIGO (todas as versoes veem os mesmos, D30), na ordem de inclusao."""
    stmt = (
        select(MarcenariaOrcamentoAnexo)
        .where(MarcenariaOrcamentoAnexo.codigo_orcamento == codigo)
        .order_by(MarcenariaOrcamentoAnexo.id)
    )
    return list(db.scalars(stmt))


def get_anexo(db: Session, anexo_id: int, codigo: str) -> Optional[MarcenariaOrcamentoAnexo]:
    """Um anexo, so se for deste codigo (o id de outro orcamento da 404)."""
    stmt = select(MarcenariaOrcamentoAnexo).where(
        MarcenariaOrcamentoAnexo.id == anexo_id,
        MarcenariaOrcamentoAnexo.codigo_orcamento == codigo,
    )
    return db.scalar(stmt)


def contar_anexos(db: Session, codigo: str) -> int:
    stmt = select(func.count(MarcenariaOrcamentoAnexo.id)).where(
        MarcenariaOrcamentoAnexo.codigo_orcamento == codigo,
    )
    return int(db.scalar(stmt) or 0)


def buscar_por_ids(db: Session, model, ids: list[int]) -> dict[int, Any]:
    """{id: linha} de um model qualquer, para os ids pedidos."""
    if not ids:
        return {}
    return {linha.id: linha for linha in db.scalars(select(model).where(model.id.in_(ids)))}

