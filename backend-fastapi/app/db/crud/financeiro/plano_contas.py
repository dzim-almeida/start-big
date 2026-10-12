# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/financeiro/plano_contas.py
# DESCRICAO: Financeiro (banco) - plano de contas.
# ---------------------------------------------------------------------------

from typing import Optional, Sequence
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.db.models.conta_pagar import ContaPagar
from app.db.models.plano_conta import PlanoConta


# ===========================================================================
# PLANO DE CONTAS
# ===========================================================================

def listar_planos_conta(
    db: Session, empresa_id: int, apenas_ativos: bool = False
) -> Sequence[PlanoConta]:
    q = db.query(PlanoConta).filter(PlanoConta.empresa_id == empresa_id)
    if apenas_ativos:
        q = q.filter(PlanoConta.ativo.is_(True))
    return q.order_by(PlanoConta.tipo.asc(), PlanoConta.nome.asc()).all()


def get_plano_conta(db: Session, empresa_id: int, plano_id: int) -> Optional[PlanoConta]:
    return (
        db.query(PlanoConta)
        .filter(PlanoConta.id == plano_id, PlanoConta.empresa_id == empresa_id)
        .first()
    )


def get_plano_conta_por_nome(
    db: Session, empresa_id: int, nome: str
) -> Optional[PlanoConta]:
    return (
        db.query(PlanoConta)
        .filter(PlanoConta.empresa_id == empresa_id, func.lower(PlanoConta.nome) == nome.lower())
        .first()
    )


def criar_plano_conta(db: Session, plano: PlanoConta) -> PlanoConta:
    db.add(plano)
    db.flush()
    return plano


def ids_de_planos_em_uso(db: Session, empresa_id: int) -> set[int]:
    """Categorias que já classificam alguma conta.

    Uma consulta só para a lista inteira, e não uma por categoria: a tela do
    plano de contas mostra dezenas de linhas, e perguntar "esta está em uso?"
    uma a uma seria o N+1 clássico.
    """
    linhas = (
        db.query(ContaPagar.plano_conta_id)
        .filter(
            ContaPagar.empresa_id == empresa_id,
            ContaPagar.plano_conta_id.isnot(None),
        )
        .distinct()
        .all()
    )
    return {linha[0] for linha in linhas}
