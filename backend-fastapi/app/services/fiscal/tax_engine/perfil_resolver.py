# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/tax_engine/perfil_resolver.py
# DESCRIÇÃO: Qual regra do perfil tributário vale para (UF de destino, NCM).
# ---------------------------------------------------------------------------
"""
A inteligência do perfil: da regra mais específica para a mais genérica.

    Prioridade 1:  UF = "SP"  AND  NCM = "85171200"   (exceção do produto)
    Prioridade 2:  UF = "SP"  AND  NCM = NULL         (regra do estado)
    Prioridade 3:  UF = NULL  AND  NCM = NULL         (fallback geral)

Uma query só: o ORDER BY põe a mais específica primeiro e o `first()`
resolve. Regra com UF NULL e NCM preenchido é ignorada de propósito -- a
alíquota interestadual depende SEMPRE do destino, nunca só do produto.

Este módulo abre exceção à regra "tax_engine não toca o banco": é a ponte
entre o motor puro (TASK007/008) e a tabela de regras, no mesmo espírito do
`resolver.py`.
"""

from typing import Optional

from sqlalchemy import and_, case, or_, select
from sqlalchemy.orm import Session

from app.db.models.regra_perfil_tributario import RegraPerfilTributario


def resolver_regra_perfil(
    db: Session,
    perfil_id: int,
    uf_destino: str,
    ncm_produto: Optional[str] = None,
) -> Optional[RegraPerfilTributario]:
    """
    A regra aplicável, ou None quando o perfil não existe ou não tem regra
    que case (nem fallback) -- para o chamador, "sem configuração
    interestadual para este destino".
    """
    uf = uf_destino.strip().upper()
    R = RegraPerfilTributario

    uf_e_ncm = and_(R.uf_destino == uf, R.ncm_excecao == ncm_produto)
    so_uf = and_(R.uf_destino == uf, R.ncm_excecao.is_(None))
    fallback = and_(R.uf_destino.is_(None), R.ncm_excecao.is_(None))

    stmt = (
        select(R)
        .where(R.perfil_id == perfil_id, or_(uf_e_ncm, so_uf, fallback))
        .order_by(
            case((R.uf_destino.isnot(None), 1), else_=0).desc(),
            case((R.ncm_excecao.isnot(None), 1), else_=0).desc(),
        )
        .limit(1)
    )
    return db.scalars(stmt).first()
