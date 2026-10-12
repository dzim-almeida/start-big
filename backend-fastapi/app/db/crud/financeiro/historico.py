# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/financeiro/historico.py
# DESCRICAO: Financeiro (banco) - auditoria: o historico de cada documento.
# ---------------------------------------------------------------------------

from typing import Optional, Sequence
from sqlalchemy.orm import Session
from app.db.models.historico_financeiro import HistoricoFinanceiro


# ===========================================================================
# AUDITORIA
# ===========================================================================

def registrar_historico(
    db: Session,
    *,
    empresa_id: int,
    entidade: str,
    entidade_id: int,
    campo: str,
    valor_antigo: Optional[str],
    valor_novo: Optional[str],
    funcionario_id: Optional[int],
    funcionario_nome: Optional[str],
) -> HistoricoFinanceiro:
    """O ÚNICO lugar que escreve na trilha de auditoria."""
    linha = HistoricoFinanceiro(
        empresa_id=empresa_id,
        entidade=entidade,
        entidade_id=entidade_id,
        campo=campo,
        valor_antigo=valor_antigo,
        valor_novo=valor_novo,
        funcionario_id=funcionario_id,
        funcionario_nome=funcionario_nome,
    )
    db.add(linha)
    db.flush()
    return linha


def listar_historico(
    db: Session, empresa_id: int, entidade: str, entidade_id: int
) -> Sequence[HistoricoFinanceiro]:
    return (
        db.query(HistoricoFinanceiro)
        .filter(
            HistoricoFinanceiro.empresa_id == empresa_id,
            HistoricoFinanceiro.entidade == entidade,
            HistoricoFinanceiro.entidade_id == entidade_id,
        )
        .order_by(HistoricoFinanceiro.criado_em.desc(), HistoricoFinanceiro.id.desc())
        .all()
    )
